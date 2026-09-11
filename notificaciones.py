# -*- coding: utf-8 -*-
"""
notificaciones.py
Envía un correo al abogado cada vez que llega un contacto nuevo por WhatsApp o
Facebook, para que no se pierda ningún cliente potencial aunque el servidor
gratuito no tenga almacenamiento permanente.

IMPORTANTE (cambio de proveedor): este archivo usaba antes Gmail por SMTP
(IMAP_USER/IMAP_PASS). Se cambió a la API de Resend (HTTPS) porque el hosting
gratuito de Render bloquea las conexiones salientes de SMTP hacia Gmail
("[Errno 101] Network is unreachable" — problema conocido y reportado del lado
de Render, no de las credenciales). Resend envía por HTTPS, que sí funciona
normalmente en Render.

Configuración necesaria (variables de entorno en Render):
- RESEND_API_KEY: clave de API de https://resend.com (cuenta gratis).
- NOTIFICAR_A (o, si no está, IMAP_USER, por compatibilidad con el nombre que
  ya se usaba): el correo del despacho al que deben llegar las notificaciones.
  IMPORTANTE: en el plan gratuito de Resend, los correos SOLO se pueden enviar
  a la misma dirección con la que se creó la cuenta de Resend — así que hay que
  registrarse en Resend con ese mismo correo del despacho.
- RESEND_FROM (opcional): remitente que aparece en el correo. Por defecto usa
  el dominio de pruebas de Resend (onboarding@resend.dev), que no requiere
  verificar un dominio propio.
"""
import base64
import os

import requests

RESEND_API_URL = "https://api.resend.com/emails"


def _destino_y_clave():
    clave = os.getenv("RESEND_API_KEY")
    destino = os.getenv("NOTIFICAR_A") or os.getenv("IMAP_USER")
    return destino, clave


def _enviar_via_resend(asunto: str, cuerpo_texto: str, adjuntos: list = None) -> bool:
    """
    Envía un correo por la API de Resend. adjuntos, si se da, es una lista de
    dicts {"filename": ..., "content_bytes": ...} (bytes crudos del archivo;
    esta función se encarga de codificarlos en base64 como pide la API).
    Devuelve True/False según si se pudo enviar.
    """
    destino, clave = _destino_y_clave()
    remitente = os.getenv("RESEND_FROM", "Asistente Despacho <onboarding@resend.dev>")

    if not clave or not destino:
        print("⚠️  Falta RESEND_API_KEY o NOTIFICAR_A/IMAP_USER: no se pudo enviar la notificación por correo.")
        return False

    payload = {
        "from": remitente,
        "to": [destino],
        "subject": asunto,
        "text": cuerpo_texto,
    }
    if adjuntos:
        payload["attachments"] = [
            {
                "filename": a["filename"],
                "content": base64.b64encode(a["content_bytes"]).decode("ascii"),
            }
            for a in adjuntos
        ]

    headers = {"Authorization": f"Bearer {clave}", "Content-Type": "application/json"}
    try:
        r = requests.post(RESEND_API_URL, headers=headers, json=payload, timeout=15)
        if r.status_code >= 300:
            print(f"⚠️  Resend rechazó el correo ({r.status_code}): {r.text}")
            return False
        return True
    except Exception as e:
        print(f"⚠️  No se pudo enviar el correo vía Resend: {e}")
        return False


def notificar_nuevo_mensaje(canal: str, remitente: str, texto: str):
    """
    canal: "WhatsApp" o "Facebook"
    remitente: número de teléfono o ID de la persona que escribió
    texto: el mensaje recibido
    """
    asunto = f"📩 Nuevo mensaje de {canal} — {remitente}"
    cuerpo = f"Canal: {canal}\nDe: {remitente}\n\nMensaje:\n{texto}\n\n— Notificación automática del asistente del despacho."
    return _enviar_via_resend(asunto, cuerpo)


def notificar_resumen_caso(canal: str, contacto: str, area: str, respuestas: dict, viabilidad: str, quiere_consulta: bool, subtema: str = None, formulario_enviado: str = None):
    """
    Envía un correo con el resumen completo del caso cuando el cliente termina el
    formulario de intake: todas sus respuestas, la impresión de viabilidad generada
    por IA, y si aceptó o no la consulta pagada.

    subtema: tema específico dentro del área (por ejemplo "Alimentos" dentro de
    "Derecho de Familia"), si aplica.
    formulario_enviado: nombre del PDF ampliado que se le envió al cliente para
    diligenciar y devolver, si aplica.
    """
    decision = "SÍ quiere agendar consulta pagada" if quiere_consulta else "NO quiere consulta pagada por ahora"
    tema_asunto = f"{area} - {subtema}" if subtema else area
    asunto = f"⚖️ Nuevo caso ({tema_asunto}) — {contacto} — {decision}"

    lineas = [f"Canal: {canal}", f"Contacto: {contacto}", f"Área: {area}"]
    if subtema:
        lineas.append(f"Tema específico: {subtema}")
    if formulario_enviado:
        lineas.append(f"Formulario ampliado enviado al cliente: {formulario_enviado}")
    lineas.append(f"Decisión: {decision}")
    lineas.append("")
    lineas.append("Respuestas del formulario:")
    for k, v in respuestas.items():
        lineas.append(f"  - {k}: {v}")
    lineas.append("")
    lineas.append("Impresión de viabilidad (generada por IA, revisar antes de comunicarla como definitiva):")
    lineas.append(viabilidad)
    cuerpo = "\n".join(lineas)

    return _enviar_via_resend(asunto, cuerpo)


def notificar_archivo_recibido(canal: str, remitente: str, nombre_archivo: str, contenido: bytes,
                                mime_type: str = "application/octet-stream", caption: str = ""):
    """
    Reenvía por correo, como archivo adjunto, un documento/foto que el cliente envió
    por WhatsApp o Messenger (comprobante, cédula, escritura, fotos del accidente,
    etc.). El servidor gratuito no guarda archivos de forma permanente, así que este
    correo es la copia que le queda al abogado.

    contenido: los bytes del archivo ya descargados (WhatsApp/Messenger entregan una
    URL temporal, no el archivo directamente; app.py se encarga de descargarlo antes
    de llamar a esta función).
    """
    asunto = f"📎 Archivo recibido por {canal} — {remitente}"
    lineas = [f"Canal: {canal}", f"Contacto: {remitente}", f"Archivo: {nombre_archivo}"]
    if caption:
        lineas.append(f"Mensaje del cliente: {caption}")
    lineas.append("")
    lineas.append("Se adjunta el archivo que el cliente envió por el chat del despacho.")
    cuerpo = "\n".join(lineas)

    adjuntos = [{"filename": nombre_archivo, "content_bytes": contenido}]
    return _enviar_via_resend(asunto, cuerpo, adjuntos=adjuntos)
