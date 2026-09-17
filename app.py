# -*- coding: utf-8 -*-
"""
app.py
Servidor único que recibe los mensajes de WhatsApp Business (Cloud API) y de
Facebook Messenger (Página del despacho), los pasa por el motor de conversación
(flujo.py: saludo -> área -> formulario -> viabilidad con IA -> oferta de consulta
pagada con enlace de Wompi), y notifica por correo al abogado.

Endpoints:
  GET  /                -> "ok" (para comprobar que el servicio está vivo)
  GET  /webhook         -> verificación del webhook (Meta la llama al configurar)
  POST /webhook         -> recepción de mensajes de WhatsApp y Messenger
"""
import os
import logging
import urllib.parse
import uuid

import requests
from fastapi import FastAPI, Request, Response
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles

import asistente_ia
import flujo
import formularios_web
import memoria
import panel_cierre
from notificaciones import (
    notificar_nuevo_mensaje, notificar_resumen_caso, notificar_archivo_recibido,
    notificar_formulario_web, notificar_cierre_enviado,
)

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

logging.basicConfig(level=logging.INFO)
log = logging.getLogger("asistente_meta")

app = FastAPI(title="Asistente WhatsApp/Facebook — Javier Londoño V. Abogados & Asociados")

# Sirve los formularios PDF ampliados en /formularios/<archivo>.pdf para poder
# enviarlos como documento adjunto por WhatsApp/Messenger (Meta necesita una URL
# pública https, no puede leer un archivo directamente del servidor).
_DIR_FORMULARIOS = os.path.join(os.path.dirname(__file__), "formularios")
if os.path.isdir(_DIR_FORMULARIOS):
    app.mount("/formularios", StaticFiles(directory=_DIR_FORMULARIOS), name="formularios")

VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN", "")
WHATSAPP_TOKEN = os.getenv("WHATSAPP_TOKEN", "")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "")
FACEBOOK_PAGE_TOKEN = os.getenv("FACEBOOK_PAGE_TOKEN", "")
GRAPH_API_VERSION = os.getenv("GRAPH_API_VERSION", "v20.0")
# Render define esta variable automáticamente con la URL pública del servicio.
# Si se despliega en otro sitio, se puede fijar manualmente con BASE_URL.
BASE_URL = os.getenv("RENDER_EXTERNAL_URL") or os.getenv("BASE_URL", "")
# Tamaño máximo de un archivo que el cliente envía, para reenviarlo por correo
# (Gmail rechaza adjuntos más grandes de ~25 MB). Si el cliente envía algo más
# pesado, se le avisa que no se pudo procesar automáticamente.
TAMANO_MAXIMO_ADJUNTO_MB = float(os.getenv("TAMANO_MAXIMO_ADJUNTO_MB", "20"))
# Clave del panel interno de "cierre de negocio" (paso 3, ver panel_cierre.py).
# La define el abogado en Render; si no se configura, esa página queda
# deshabilitada (para no dejarla abierta sin clave por descuido).
PANEL_CIERRE_PASSWORD = os.getenv("PANEL_CIERRE_PASSWORD", "")


@app.get("/")
def salud():
    return {"status": "ok", "despacho": "Javier Londoño V. Abogados & Asociados"}


@app.get("/webhook")
def verificar_webhook(request: Request):
    modo = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if modo == "subscribe" and token == VERIFY_TOKEN and VERIFY_TOKEN:
        return Response(content=challenge, media_type="text/plain")
    return Response(content="Token de verificación inválido", status_code=403)


@app.post("/webhook")
async def recibir_webhook(request: Request):
    datos = await request.json()
    objeto = datos.get("object")
    try:
        if objeto == "whatsapp_business_account":
            _procesar_whatsapp(datos)
        elif objeto == "page":
            _procesar_messenger(datos)
        else:
            log.info(f"Objeto de webhook no manejado: {objeto}")
    except Exception:
        log.exception("Error procesando el webhook")
    return {"status": "recibido"}


# ---------------------------------------------------------------------------
# FORMULARIOS WEB (se llenan directo en el navegador, sin descargar nada)
# ---------------------------------------------------------------------------

@app.get("/formulario/{slug}")
def ver_formulario(slug: str, contacto: str = "", canal: str = ""):
    html = formularios_web.generar_html_formulario(slug, contacto=contacto, canal=canal)
    if not html:
        return Response(content="Formulario no encontrado.", status_code=404)
    return HTMLResponse(content=html)


@app.post("/formulario/{slug}/enviar")
async def enviar_formulario(slug: str, request: Request, contacto: str = "", canal: str = ""):
    if slug == "inicio":
        # El formulario inicial (datos personales + elección del tema) no solo
        # avisa al abogado: también debe continuar la conversación por
        # WhatsApp/Messenger, así que se procesa aparte.
        return await _enviar_formulario_inicio(request, contacto, canal)

    form_def = formularios_web.FORMULARIOS.get(slug)
    if not form_def:
        return Response(content="Formulario no encontrado.", status_code=404)

    datos = await request.form()

    # Arma {etiqueta bonita: valor} en el mismo orden del formulario, uniendo los
    # checkboxes marcados (llegan como varias entradas con el mismo "name").
    respuestas = {}
    for seccion in form_def["secciones"]:
        for campo in seccion["campos"]:
            cid = campo["id"]
            if campo["tipo"] == "checkboxes":
                valores = datos.getlist(cid)
                if valores:
                    respuestas[campo["etiqueta"]] = ", ".join(valores)
            else:
                valor = datos.get(cid)
                if valor:
                    respuestas[campo["etiqueta"]] = valor

    # Archivos adjuntados en el propio formulario.
    archivos = []
    tamano_total_mb = 0.0
    for adjunto in datos.getlist("anexos"):
        if not getattr(adjunto, "filename", ""):
            continue
        contenido = await adjunto.read()
        if not contenido:
            continue
        tamano_total_mb += len(contenido) / (1024 * 1024)
        if tamano_total_mb > TAMANO_MAXIMO_ADJUNTO_MB:
            log.warning(f"Formulario web de {contacto}: se superó el tamaño máximo de adjuntos, se detiene ahí.")
            break
        archivos.append({"filename": adjunto.filename, "content_bytes": contenido})

    contacto_real = urllib.parse.unquote(contacto) if contacto else "(no identificado)"
    notificar_formulario_web(canal or "Formulario web", contacto_real, form_def["titulo"], respuestas, archivos)

    if contacto:
        try:
            memoria.agregar_turno(contacto_real, "user", f"[completó el formulario web: {form_def['titulo']}]")
        except Exception:
            pass

    html = formularios_web.generar_html_gracias(slug)
    return HTMLResponse(content=html)


async def _enviar_formulario_inicio(request: Request, contacto: str, canal: str):
    """
    Procesa el formulario inicial (datos personales + tema del caso, ver
    formularios_web.FORMULARIOS["inicio"]). A diferencia de los formularios
    por tema, este además debe avanzar el estado de la conversación y seguir
    hablando con la persona por el mismo canal (WhatsApp o Messenger) en el
    punto donde quedó — igual que si hubiera respondido esas preguntas por chat.
    """
    form_def = formularios_web.FORMULARIOS.get("inicio")
    datos = await request.form()

    nombre = (datos.get("nombre_completo") or "").strip()
    documento = (datos.get("documento_identidad") or "").strip()
    correo = (datos.get("correo") or "").strip()
    ciudad = (datos.get("ciudad_departamento") or "").strip()
    area_titulo = (datos.get("area") or "").strip()

    archivos = []
    tamano_total_mb = 0.0
    for adjunto in datos.getlist("anexos"):
        if not getattr(adjunto, "filename", ""):
            continue
        contenido = await adjunto.read()
        if not contenido:
            continue
        tamano_total_mb += len(contenido) / (1024 * 1024)
        if tamano_total_mb > TAMANO_MAXIMO_ADJUNTO_MB:
            log.warning(f"Formulario inicial de {contacto}: se superó el tamaño máximo de adjuntos, se detiene ahí.")
            break
        archivos.append({"filename": adjunto.filename, "content_bytes": contenido})

    contacto_real = urllib.parse.unquote(contacto) if contacto else ""

    opcion = None
    for op in flujo.AREAS_MENU:
        if op["titulo"] == area_titulo:
            opcion = op
            break

    if form_def:
        respuestas_notif = {
            "Nombre completo": nombre,
            "Documento de identidad": documento,
            "Correo electrónico": correo,
            "Ciudad y departamento": ciudad,
            "Tema seleccionado": area_titulo,
        }
        notificar_formulario_web(
            canal or "Formulario web", contacto_real or "(no identificado)",
            form_def["titulo"], respuestas_notif, archivos,
        )

    if contacto_real and opcion and nombre:
        estado = memoria.obtener_estado(contacto_real)
        estado["area"] = opcion["id"]
        estado["respuestas"] = {
            "nombre": nombre,
            "documento_identidad": documento,
            "correo": correo,
            "ciudad_departamento": ciudad,
        }
        estado["indice"] = 1  # el "nombre" ya quedó respondido en este formulario
        estado["etapa"] = "formulario"
        memoria.guardar_estado(contacto_real, estado)
        try:
            memoria.agregar_turno(contacto_real, "user", f"[completó el formulario inicial: {nombre} — {opcion['titulo']}]")
        except Exception:
            pass

        primer_nombre = nombre.split()[0] if nombre else ""
        preguntas = flujo._preguntas_actuales(estado)
        if estado["indice"] < len(preguntas):
            siguiente = preguntas[estado["indice"]]["texto"]
            mensaje_confirmacion = f"Gracias, {primer_nombre}. Ya tengo sus datos para *{opcion['titulo']}*.\n\n{siguiente}"
        else:
            mensaje_confirmacion = f"Gracias, {primer_nombre}."

        if canal == "Messenger":
            _enviar_messenger_texto(contacto_real, mensaje_confirmacion)
        else:
            _enviar_whatsapp_texto(contacto_real, mensaje_confirmacion)

    html = formularios_web.generar_html_gracias("inicio")
    return HTMLResponse(content=html)


# ---------------------------------------------------------------------------
# PANEL DE "CIERRE DE NEGOCIO" (paso 3, uso interno del abogado)
# ---------------------------------------------------------------------------
# Después de la consulta personal con el cliente, el abogado entra aquí,
# escribe los datos del caso y aprueba (o corrige) los borradores que redacta
# la IA antes de que se le envíen al cliente por WhatsApp/Messenger. Ver
# panel_cierre.py para el detalle de cada pantalla.

def _clave_panel_valida(clave: str) -> bool:
    return bool(PANEL_CIERRE_PASSWORD) and clave == PANEL_CIERRE_PASSWORD


@app.get("/panel/cierre")
def ver_panel_cierre_login():
    return HTMLResponse(content=panel_cierre.generar_html_login())


@app.post("/panel/cierre")
async def entrar_panel_cierre(request: Request):
    datos = await request.form()
    clave = datos.get("clave") or ""
    if not _clave_panel_valida(clave):
        return HTMLResponse(content=panel_cierre.generar_html_login(error=True))
    return HTMLResponse(content=panel_cierre.generar_html_formulario_datos(clave))


@app.post("/panel/cierre/generar")
async def generar_documentos_cierre_ruta(request: Request):
    datos_form = await request.form()
    clave = datos_form.get("clave") or ""
    if not _clave_panel_valida(clave):
        return HTMLResponse(content=panel_cierre.generar_html_login(error=True))

    datos = {
        "canal": (datos_form.get("canal") or "").strip(),
        "contacto": (datos_form.get("contacto") or "").strip(),
        "nombre_cliente": (datos_form.get("nombre_cliente") or "").strip(),
        "documento_identidad": (datos_form.get("documento_identidad") or "").strip(),
        "ciudad": (datos_form.get("ciudad") or "").strip(),
        "area": (datos_form.get("area") or "").strip(),
        "resumen_caso": (datos_form.get("resumen_caso") or "").strip(),
        "honorarios": (datos_form.get("honorarios") or "").strip(),
        "notas": (datos_form.get("notas") or "").strip(),
    }
    try:
        documentos = asistente_ia.generar_documentos_cierre(datos)
    except Exception:
        log.exception("Error generando documentos de cierre con IA")
        return HTMLResponse(
            content=panel_cierre.generar_html_error(
                "No se pudieron generar los borradores (revise que la IA esté configurada). Intente de nuevo."
            ),
            status_code=500,
        )

    return HTMLResponse(content=panel_cierre.generar_html_revision(clave, datos, documentos))


@app.post("/panel/cierre/enviar")
async def enviar_documentos_cierre_ruta(request: Request):
    datos_form = await request.form()
    clave = datos_form.get("clave") or ""
    if not _clave_panel_valida(clave):
        return HTMLResponse(content=panel_cierre.generar_html_login(error=True))

    datos = {
        "canal": (datos_form.get("canal") or "").strip(),
        "contacto": (datos_form.get("contacto") or "").strip(),
        "nombre_cliente": (datos_form.get("nombre_cliente") or "").strip(),
        "area": (datos_form.get("area") or "").strip(),
        "contrato": (datos_form.get("contrato") or "").strip(),
        "poder": (datos_form.get("poder") or "").strip(),
        "requerimientos": (datos_form.get("requerimientos") or "").strip(),
    }

    cierre_id = uuid.uuid4().hex
    memoria.guardar_cierre(cierre_id, datos)

    if not BASE_URL:
        log.warning("Falta BASE_URL/RENDER_EXTERNAL_URL: no se pudo armar el enlace de cierre.")
        enlace = "(no se pudo generar el enlace: falta configurar BASE_URL)"
    else:
        enlace = f"{BASE_URL.rstrip('/')}/cierre/{cierre_id}"
        primer_nombre = datos["nombre_cliente"].split()[0] if datos["nombre_cliente"] else ""
        mensaje = (
            f"¡Hola{', ' + primer_nombre if primer_nombre else ''}! Gracias por confiarnos su caso. "
            f"Aquí puede ver el contrato, el poder y los documentos que necesitamos para continuar:\n{enlace}"
        )
        if datos["canal"] == "Messenger":
            _enviar_messenger_texto(datos["contacto"], mensaje)
        else:
            _enviar_whatsapp_texto(datos["contacto"], mensaje)

    notificar_cierre_enviado(
        datos["canal"], datos["contacto"], datos["nombre_cliente"], datos["area"],
        datos["contrato"], datos["poder"], datos["requerimientos"], enlace,
    )

    return HTMLResponse(content=panel_cierre.generar_html_confirmacion(datos, enlace))


@app.get("/cierre/{cierre_id}")
def ver_documentos_cierre(cierre_id: str):
    datos = memoria.obtener_cierre(cierre_id)
    if not datos:
        return Response(content="Enlace no encontrado o vencido.", status_code=404)
    return HTMLResponse(content=panel_cierre.generar_html_cliente(datos))


# ---------------------------------------------------------------------------
# LÓGICA COMÚN DE CONVERSACIÓN
# ---------------------------------------------------------------------------

def _atender_contacto(canal: str, contacto_id: str, texto_usuario: str):
    """
    Procesa un mensaje entrante de cualquier canal a través del motor de flujo,
    y devuelve la lista de mensajes genéricos a enviar de vuelta.
    """
    es_nuevo = memoria.es_contacto_nuevo(contacto_id)
    memoria.registrar_contacto_csv(canal, contacto_id, texto_usuario)

    if es_nuevo:
        notificar_nuevo_mensaje(canal, contacto_id, texto_usuario)

    estado = memoria.obtener_estado(contacto_id)
    nuevo_estado, mensajes, evento = flujo.procesar(estado, texto_usuario)
    memoria.guardar_estado(contacto_id, nuevo_estado)

    if not mensajes:
        # Ya se completó el formulario (o el cliente sigue escribiendo después del
        # cierre): seguimos la conversación en modo libre con el asistente de IA.
        historial = memoria.obtener_historial(contacto_id)
        try:
            respuesta = asistente_ia.responder(texto_usuario, historial=historial)
        except Exception:
            log.exception("Error generando respuesta libre con IA")
            respuesta = "Ya registré su mensaje. El abogado lo revisará y le responderá pronto."
        memoria.agregar_turno(contacto_id, "user", texto_usuario)
        memoria.agregar_turno(contacto_id, "assistant", respuesta)
        mensajes = [{"tipo": "texto", "texto": respuesta}]

    if evento == "resumen_listo":
        area_nombre = asistente_ia.NOMBRES_AREA.get(nuevo_estado.get("area"), "Consulta")
        formulario_enviado = flujo._area_web(nuevo_estado) or flujo._area_pdf(nuevo_estado)
        notificar_resumen_caso(
            canal, contacto_id, area_nombre,
            nuevo_estado.get("respuestas", {}),
            nuevo_estado.get("viabilidad", ""),
            quiere_consulta=(nuevo_estado.get("etapa") == "pago_enviado"),
            formulario_enviado=formulario_enviado,
        )

    return mensajes


def _atender_archivo_recibido(canal: str, contacto_id: str, nombre_archivo: str, contenido: bytes,
                               mime_type: str, caption: str = "") -> str:
    """
    Registra y reenvía por correo un archivo (foto, PDF, audio, etc.) que el cliente
    envió por el chat, y devuelve el texto de confirmación que se le responde.
    Se usa tanto para WhatsApp como para Messenger.
    """
    nota = f"[archivo adjunto: {nombre_archivo}]" + (f" — {caption}" if caption else "")
    es_nuevo = memoria.es_contacto_nuevo(contacto_id)
    memoria.registrar_contacto_csv(canal, contacto_id, nota)
    if es_nuevo:
        notificar_nuevo_mensaje(canal, contacto_id, nota)
    memoria.agregar_turno(contacto_id, "user", nota)

    tamano_mb = len(contenido) / (1024 * 1024)
    if tamano_mb > TAMANO_MAXIMO_ADJUNTO_MB:
        log.warning(f"Archivo de {contacto_id} pesa {tamano_mb:.1f} MB, supera el máximo configurado; no se reenvía por correo.")
        return (
            "Recibí su archivo, pero pesa demasiado para reenviarlo automáticamente por correo. "
            "Si puede, envíelo en partes más pequeñas o coméntele al abogado en su próxima llamada."
        )

    enviado = notificar_archivo_recibido(canal, contacto_id, nombre_archivo, contenido, mime_type, caption)
    if enviado:
        return "📎 Recibí su archivo, gracias. Ya se lo hice llegar al abogado junto con su caso. Si tiene más documentos, puede enviarlos también por aquí."
    return "Recibí su archivo, pero tuve un problema técnico reenviándolo — igual quedó registrada su conversación; si puede, coméntelo también quedará más seguro."


# ---------------------------------------------------------------------------
# WHATSAPP
# ---------------------------------------------------------------------------

def _procesar_whatsapp(datos: dict):
    for entrada in datos.get("entry", []):
        for cambio in entrada.get("changes", []):
            valor = cambio.get("value", {})
            mensajes_entrantes = valor.get("messages")
            if not mensajes_entrantes:
                continue  # actualización de estado (leído/entregado), la ignoramos

            for mensaje in mensajes_entrantes:
                mensaje_id = mensaje.get("id")
                if memoria.es_mensaje_duplicado(mensaje_id):
                    log.info(f"WhatsApp: mensaje {mensaje_id} ya procesado (reintento de Meta), se ignora.")
                    continue

                remitente = mensaje.get("from")
                # CORRECCIÓN: a veces Meta manda un mensaje sin remitente
                # identificado (por ejemplo pruebas del propio panel de Meta).
                # Antes el programa seguía adelante igual e intentaba responder
                # sin saber a quién, lo que producía el error "the parameter to
                # is required" y el cliente real nunca recibía respuesta a su
                # "hola". Ahora se registra el mensaje completo en el log (para
                # poder revisar exactamente qué mandó Meta) y se detiene ahí,
                # igual que ya se hacía en la parte de Facebook Messenger.
                if not remitente:
                    log.warning(f"WhatsApp: mensaje sin remitente identificado, se ignora. Datos completos: {mensaje}")
                    continue

                tipo = mensaje.get("type")

                if tipo == "text":
                    texto_usuario = mensaje.get("text", {}).get("body", "")
                elif tipo == "interactive":
                    interactivo = mensaje.get("interactive", {})
                    if interactivo.get("type") == "list_reply":
                        texto_usuario = interactivo["list_reply"]["id"]
                    elif interactivo.get("type") == "button_reply":
                        texto_usuario = interactivo["button_reply"]["id"]
                    else:
                        texto_usuario = ""
                elif tipo in ("document", "image", "audio", "video", "sticker"):
                    log.info(f"WhatsApp de {remitente}: archivo ({tipo})")
                    _atender_archivo_whatsapp(remitente, mensaje, tipo)
                    continue
                else:
                    _enviar_whatsapp_texto(remitente, "Por ahora solo puedo leer mensajes de texto, archivos o las opciones del menú. ¿Podría escribir su respuesta en un mensaje de texto?")
                    continue

                log.info(f"WhatsApp de {remitente}: {texto_usuario}")
                mensajes_salida = _atender_contacto("WhatsApp", remitente, texto_usuario)
                for m in mensajes_salida:
                    _enviar_mensaje_whatsapp(remitente, m)


def _atender_archivo_whatsapp(remitente: str, mensaje: dict, tipo: str):
    """
    Descarga un documento/foto/audio/video que el cliente envió por WhatsApp
    (WhatsApp solo entrega un "media id"; hay que pedirle a la API la URL real y
    descargarla con el mismo token) y lo reenvía por correo al abogado.
    """
    objeto_media = mensaje.get(tipo, {})
    media_id = objeto_media.get("id")
    caption = objeto_media.get("caption", "")
    if not media_id:
        _enviar_whatsapp_texto(remitente, "No pude leer ese archivo, ¿podría reenviarlo?")
        return

    contenido, mime_type, nombre_archivo = _descargar_media_whatsapp(media_id)
    if contenido is None:
        _enviar_whatsapp_texto(remitente, "Tuve un problema descargando su archivo, ¿podría reenviarlo en un momento?")
        return

    nombre_archivo = objeto_media.get("filename") or nombre_archivo
    respuesta = _atender_archivo_recibido("WhatsApp", remitente, nombre_archivo, contenido, mime_type, caption)
    _enviar_whatsapp_texto(remitente, respuesta)


def _descargar_media_whatsapp(media_id: str):
    """
    Devuelve (contenido_bytes, mime_type, nombre_archivo_sugerido) o (None, None, None)
    si algo falla. WhatsApp requiere dos pasos: primero pedir la URL real del
    archivo (expira pronto), luego descargarla, ambos con el token de la app.
    """
    if not WHATSAPP_TOKEN:
        log.warning("Falta WHATSAPP_TOKEN: no se puede descargar el archivo del cliente.")
        return None, None, None
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}"}
    try:
        r = requests.get(f"https://graph.facebook.com/{GRAPH_API_VERSION}/{media_id}", headers=headers, timeout=15)
        if r.status_code >= 300:
            log.error(f"Error consultando media de WhatsApp: {r.status_code} {r.text}")
            return None, None, None
        info = r.json()
        url = info.get("url")
        mime_type = info.get("mime_type", "application/octet-stream")
        if not url:
            return None, None, None

        r2 = requests.get(url, headers=headers, timeout=30)
        if r2.status_code >= 300:
            log.error(f"Error descargando media de WhatsApp: {r2.status_code}")
            return None, None, None

        extension = mime_type.split("/")[-1].split(";")[0]
        nombre_archivo = f"{media_id}.{extension}"
        return r2.content, mime_type, nombre_archivo
    except Exception:
        log.exception("Excepción descargando archivo de WhatsApp")
        return None, None, None


def _enviar_mensaje_whatsapp(destino: str, mensaje: dict):
    tipo = mensaje.get("tipo")
    if tipo == "texto":
        _enviar_whatsapp_texto(destino, mensaje["texto"])
    elif tipo == "lista":
        _enviar_whatsapp_lista(destino, mensaje["cuerpo"], mensaje.get("boton", "Ver opciones"), mensaje["opciones"])
    elif tipo == "botones":
        _enviar_whatsapp_botones(destino, mensaje["cuerpo"], mensaje["opciones"])
    elif tipo == "documento":
        _enviar_whatsapp_documento(destino, mensaje["archivo"], mensaje.get("titulo", ""), mensaje.get("descripcion", ""))
    elif tipo == "formulario_web":
        _enviar_whatsapp_formulario_web(destino, mensaje["slug"], mensaje.get("descripcion", ""), canal="WhatsApp")


def _graph_post_whatsapp(body: dict):
    if not (WHATSAPP_TOKEN and WHATSAPP_PHONE_NUMBER_ID):
        log.warning("Falta WHATSAPP_TOKEN o WHATSAPP_PHONE_NUMBER_ID: no se pudo responder por WhatsApp.")
        return
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {"Authorization": f"Bearer {WHATSAPP_TOKEN}", "Content-Type": "application/json"}
    try:
        r = requests.post(url, headers=headers, json=body, timeout=15)
        if r.status_code >= 300:
            log.error(f"Error enviando WhatsApp: {r.status_code} {r.text}")
    except Exception:
        log.exception("Excepción enviando mensaje de WhatsApp")


def _enviar_whatsapp_texto(numero_destino: str, texto: str):
    _graph_post_whatsapp({
        "messaging_product": "whatsapp", "to": numero_destino, "type": "text",
        "text": {"body": texto[:4096]},
    })


def _enviar_whatsapp_lista(numero_destino: str, cuerpo: str, boton: str, opciones: list):
    _graph_post_whatsapp({
        "messaging_product": "whatsapp", "to": numero_destino, "type": "interactive",
        "interactive": {
            "type": "list",
            "body": {"text": cuerpo[:1024]},
            "action": {
                "button": boton[:20],
                "sections": [{"title": "Opciones", "rows": [
                    {"id": o["id"], "title": o["titulo"][:24]} for o in opciones
                ]}],
            },
        },
    })


def _enviar_whatsapp_documento(numero_destino: str, archivo: str, titulo: str, descripcion: str):
    if not BASE_URL:
        log.warning("Falta BASE_URL/RENDER_EXTERNAL_URL: no se pudo enviar el formulario PDF, se avisa por texto.")
        _enviar_whatsapp_texto(
            numero_destino,
            f"{descripcion}\n\n(No fue posible adjuntar el archivo automáticamente; el abogado se lo hará llegar.)",
        )
        return
    link = f"{BASE_URL.rstrip('/')}/formularios/{archivo}"
    if descripcion:
        _enviar_whatsapp_texto(numero_destino, descripcion)
    _graph_post_whatsapp({
        "messaging_product": "whatsapp", "to": numero_destino, "type": "document",
        "document": {"link": link, "filename": archivo, "caption": titulo[:1024]},
    })


def _enviar_whatsapp_formulario_web(numero_destino: str, slug: str, descripcion: str, canal: str):
    if not BASE_URL:
        log.warning("Falta BASE_URL/RENDER_EXTERNAL_URL: no se pudo armar el enlace del formulario web.")
        _enviar_whatsapp_texto(numero_destino, f"{descripcion}\n\n(El abogado le hará llegar el formulario.)")
        return
    link = (f"{BASE_URL.rstrip('/')}/formulario/{slug}"
            f"?contacto={urllib.parse.quote(numero_destino)}&canal={urllib.parse.quote(canal)}")
    _enviar_whatsapp_texto(numero_destino, f"{descripcion}\n{link}")


def _enviar_whatsapp_botones(numero_destino: str, cuerpo: str, opciones: list):
    _graph_post_whatsapp({
        "messaging_product": "whatsapp", "to": numero_destino, "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": cuerpo[:1024]},
            "action": {"buttons": [
                {"type": "reply", "reply": {"id": o["id"], "title": o["titulo"][:20]}} for o in opciones[:3]
            ]},
        },
    })


# ---------------------------------------------------------------------------
# FACEBOOK MESSENGER
# ---------------------------------------------------------------------------

def _procesar_messenger(datos: dict):
    for entrada in datos.get("entry", []):
        for evento_msg in entrada.get("messaging", []):
            remitente = evento_msg.get("sender", {}).get("id")
            mensaje = evento_msg.get("message", {})
            if not remitente:
                continue

            mensaje_id = mensaje.get("mid")
            if memoria.es_mensaje_duplicado(mensaje_id):
                log.info(f"Messenger: mensaje {mensaje_id} ya procesado (reintento de Meta), se ignora.")
                continue

            adjuntos = mensaje.get("attachments")
            if adjuntos:
                log.info(f"Messenger de {remitente}: {len(adjuntos)} archivo(s)")
                for adjunto in adjuntos:
                    _atender_archivo_messenger(remitente, adjunto)
                continue

            texto_usuario = None
            if mensaje.get("quick_reply"):
                texto_usuario = mensaje["quick_reply"].get("payload")
            elif mensaje.get("text"):
                texto_usuario = mensaje["text"]

            if not texto_usuario:
                continue

            log.info(f"Messenger de {remitente}: {texto_usuario}")
            mensajes_salida = _atender_contacto("Facebook", remitente, texto_usuario)
            for m in mensajes_salida:
                _enviar_mensaje_messenger(remitente, m)


def _atender_archivo_messenger(remitente: str, adjunto: dict):
    """
    Messenger entrega directamente una URL (temporal) para cada adjunto, sin el
    paso extra de "media id" que pide WhatsApp.
    """
    tipo = adjunto.get("type", "file")
    url = adjunto.get("payload", {}).get("url")
    if not url:
        _enviar_messenger_texto(remitente, "No pude leer ese archivo, ¿podría reenviarlo?")
        return

    try:
        r = requests.get(url, timeout=30)
        if r.status_code >= 300:
            log.error(f"Error descargando adjunto de Messenger: {r.status_code}")
            _enviar_messenger_texto(remitente, "Tuve un problema descargando su archivo, ¿podría reenviarlo en un momento?")
            return
        contenido = r.content
        mime_type = r.headers.get("Content-Type", "application/octet-stream")
    except Exception:
        log.exception("Excepción descargando archivo de Messenger")
        _enviar_messenger_texto(remitente, "Tuve un problema descargando su archivo, ¿podría reenviarlo en un momento?")
        return

    extension = mime_type.split("/")[-1].split(";")[0] if "/" in mime_type else tipo
    nombre_archivo = f"messenger_{tipo}.{extension}"
    respuesta = _atender_archivo_recibido("Facebook", remitente, nombre_archivo, contenido, mime_type)
    _enviar_messenger_texto(remitente, respuesta)


def _enviar_mensaje_messenger(psid: str, mensaje: dict):
    tipo = mensaje.get("tipo")
    if tipo == "texto":
        _enviar_messenger_texto(psid, mensaje["texto"])
    elif tipo in ("lista", "botones"):
        # Messenger: convertimos la lista/botones en texto numerado (más simple y
        # funciona igual de bien con el mismo motor de flujo, que ya acepta "1", "2"...).
        cuerpo = mensaje["cuerpo"]
        lineas = [f"{i+1}. {o['titulo']}" for i, o in enumerate(mensaje["opciones"])]
        texto = cuerpo + "\n\n" + "\n".join(lineas) + "\n\nResponda con el número de la opción."
        _enviar_messenger_texto(psid, texto)
    elif tipo == "documento":
        _enviar_messenger_documento(psid, mensaje["archivo"], mensaje.get("descripcion", ""))
    elif tipo == "formulario_web":
        _enviar_messenger_formulario_web(psid, mensaje["slug"], mensaje.get("descripcion", ""))


def _enviar_messenger_documento(psid: str, archivo: str, descripcion: str):
    if not FACEBOOK_PAGE_TOKEN:
        log.warning("Falta FACEBOOK_PAGE_TOKEN: no se pudo responder por Messenger.")
        return
    if not BASE_URL:
        log.warning("Falta BASE_URL/RENDER_EXTERNAL_URL: no se pudo enviar el formulario PDF por Messenger.")
        _enviar_messenger_texto(psid, f"{descripcion}\n\n(El abogado le hará llegar el formulario.)")
        return
    link = f"{BASE_URL.rstrip('/')}/formularios/{archivo}"
    if descripcion:
        _enviar_messenger_texto(psid, descripcion)
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/me/messages"
    params = {"access_token": FACEBOOK_PAGE_TOKEN}
    body = {
        "recipient": {"id": psid},
        "message": {"attachment": {"type": "file", "payload": {"url": link, "is_reusable": True}}},
    }
    try:
        r = requests.post(url, params=params, json=body, timeout=15)
        if r.status_code >= 300:
            log.error(f"Error enviando documento por Messenger: {r.status_code} {r.text}")
    except Exception:
        log.exception("Excepción enviando documento por Messenger")


def _enviar_messenger_formulario_web(psid: str, slug: str, descripcion: str):
    if not BASE_URL:
        log.warning("Falta BASE_URL/RENDER_EXTERNAL_URL: no se pudo armar el enlace del formulario web.")
        _enviar_messenger_texto(psid, f"{descripcion}\n\n(El abogado le hará llegar el formulario.)")
        return
    link = (f"{BASE_URL.rstrip('/')}/formulario/{slug}"
            f"?contacto={urllib.parse.quote(psid)}&canal=Messenger")
    _enviar_messenger_texto(psid, f"{descripcion}\n{link}")


def _enviar_messenger_texto(psid: str, texto: str):
    if not FACEBOOK_PAGE_TOKEN:
        log.warning("Falta FACEBOOK_PAGE_TOKEN: no se pudo responder por Messenger.")
        return
    url = f"https://graph.facebook.com/{GRAPH_API_VERSION}/me/messages"
    params = {"access_token": FACEBOOK_PAGE_TOKEN}
    body = {"recipient": {"id": psid}, "message": {"text": texto[:2000]}}
    try:
        r = requests.post(url, params=params, json=body, timeout=15)
        if r.status_code >= 300:
            log.error(f"Error enviando Messenger: {r.status_code} {r.text}")
    except Exception:
        log.exception("Excepción enviando mensaje de Messenger")


if __name__ == "__main__":
    import uvicorn
    puerto = int(os.getenv("PORT", 8000))
    uvicorn.run("app:app", host="0.0.0.0", port=puerto)
