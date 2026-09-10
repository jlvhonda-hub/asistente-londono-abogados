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

import requests
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles

import asistente_ia
import flujo
import memoria
from notificaciones import notificar_nuevo_mensaje, notificar_resumen_caso, notificar_archivo_recibido

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
        formulario_enviado = flujo._area_pdf(nuevo_estado)
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
