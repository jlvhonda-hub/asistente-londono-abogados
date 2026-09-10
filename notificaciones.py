# -*- coding: utf-8 -*-
"""
notificaciones.py
Envía un correo al abogado cada vez que llega un contacto nuevo por WhatsApp o
Facebook, para que no se pierda ningún cliente potencial aunque el servidor
gratuito no tenga almacenamiento permanente.

Usa las mismas credenciales de Gmail que ya existían en el proyecto (IMAP_USER/
IMAP_PASS) pero por SMTP, que es el protocolo para *enviar* correo. Gmail permite
usar la misma "contraseña de aplicación" para IMAP y SMTP.

Requiere que en Gmail esté activada una "Contraseña de aplicación" (no la
contraseña normal de la cuenta): https://myaccount.google.com/apppasswords
"""
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication


def notificar_nuevo_mensaje(canal: str, remitente: str, texto: str):
    """
    canal: "WhatsApp" o "Facebook"
    remitente: número de teléfono o ID de la persona que escribió
    texto: el mensaje recibido
    """
    usuario = os.getenv("IMAP_USER")
    clave = os.getenv("IMAP_PASS")
    destino = os.getenv("NOTIFICAR_A", usuario)

    if not usuario or not clave:
        print("⚠️  No se configuraron IMAP_USER/IMAP_PASS: no se pudo enviar la notificación por correo.")
        return False

    asunto = f"📩 Nuevo mensaje de {canal} — {remitente}"
    cuerpo = f"Canal: {canal}\nDe: {remitente}\n\nMensaje:\n{texto}\n\n— Notificación automática del asistente del despacho."

    msg = MIMEText(cuerpo, _charset="utf-8")
    msg["Subject"] = asunto
    msg["From"] = usuario
    msg["To"] = destino

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(usuario, clave)
            servidor.sendmail(usuario, [destino], msg.as_string())
        return True
    except Exception as e:
        print(f"⚠️  No se pudo enviar la notificación por correo: {e}")
        return False


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
    usuario = os.getenv("IMAP_USER")
    clave = os.getenv("IMAP_PASS")
    destino = os.getenv("NOTIFICAR_A", usuario)

    if not usuario or not clave:
        print("⚠️  No se configuraron IMAP_USER/IMAP_PASS: no se pudo enviar el resumen del caso.")
        return False

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

    msg = MIMEText(cuerpo, _charset="utf-8")
    msg["Subject"] = asunto
    msg["From"] = usuario
    msg["To"] = destino

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(usuario, clave)
            servidor.sendmail(usuario, [destino], msg.as_string())
        return True
    except Exception as e:
        print(f"⚠️  No se pudo enviar el resumen del caso: {e}")
        return False


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
    usuario = os.getenv("IMAP_USER")
    clave = os.getenv("IMAP_PASS")
    destino = os.getenv("NOTIFICAR_A", usuario)

    if not usuario or not clave:
        print("⚠️  No se configuraron IMAP_USER/IMAP_PASS: no se pudo reenviar el archivo recibido.")
        return False

    asunto = f"📎 Archivo recibido por {canal} — {remitente}"
    lineas = [f"Canal: {canal}", f"Contacto: {remitente}", f"Archivo: {nombre_archivo}"]
    if caption:
        lineas.append(f"Mensaje del cliente: {caption}")
    lineas.append("")
    lineas.append("Se adjunta el archivo que el cliente envió por el chat del despacho.")
    cuerpo = "\n".join(lineas)

    msg = MIMEMultipart()
    msg["Subject"] = asunto
    msg["From"] = usuario
    msg["To"] = destino
    msg.attach(MIMEText(cuerpo, _charset="utf-8"))

    adjunto = MIMEApplication(contenido, Name=nombre_archivo)
    adjunto["Content-Disposition"] = f'attachment; filename="{nombre_archivo}"'
    msg.attach(adjunto)

    try:
        with smtplib.SMTP_SSL("smtp.gmail.com", 465) as servidor:
            servidor.login(usuario, clave)
            servidor.sendmail(usuario, [destino], msg.as_string())
        return True
    except Exception as e:
        print(f"⚠️  No se pudo reenviar el archivo recibido: {e}")
        return False
