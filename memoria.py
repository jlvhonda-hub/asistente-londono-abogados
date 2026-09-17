# -*- coding: utf-8 -*-
"""
memoria.py
Memoria de corto plazo por conversación (en memoria del proceso) + un registro
de contactos en un archivo CSV local.

Importante (hosting gratuito): en un plan gratuito como el de Render, el disco
se reinicia cada vez que el servicio se re-despliega o se duerme por inactividad
prolongada, así que este CSV es un respaldo adicional, NO el archivo definitivo
de casos. El correo de notificación (notificaciones.py) es la copia confiable.
"""
import csv
import os
import threading
from collections import deque
from datetime import datetime

_LOCK = threading.Lock()
_HISTORIALES = {}  # {contacto_id: [ {"role":..., "content":...}, ... ]}
_ESTADOS = {}  # {contacto_id: {"etapa":..., "area":..., "respuestas":{...}, ...}}
_CIERRES = {}  # {cierre_id: {"contrato":..., "poder":..., "requerimientos":..., ...}}
MAX_TURNOS = 8  # cuántos mensajes recientes se recuerdan por contacto

RUTA_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contactos.csv")

# ---------------------------------------------------------------------------
# Control de mensajes duplicados
# ---------------------------------------------------------------------------
# Meta reintenta la entrega de un mensaje al webhook si no recibe respuesta a
# tiempo (por ejemplo, mientras el servicio gratuito de Render está "despertando"
# tras estar dormido). Sin este control, cada reintento dispara de nuevo todo el
# flujo de conversación y el cliente recibe el mismo mensaje repetido varias veces.
# Cada mensaje de WhatsApp/Messenger trae un identificador único; se recuerda un
# número limitado de IDs recientes (no hace falta guardarlos para siempre) para
# detectar y descartar los reintentos.
_MENSAJES_PROCESADOS_MAX = 500
_mensajes_procesados_set = set()
_mensajes_procesados_orden = deque()


def es_mensaje_duplicado(mensaje_id: str) -> bool:
    """
    Devuelve True si este mensaje_id ya se procesó antes (reintento de Meta) y
    debe ignorarse. Si es la primera vez que se ve, lo registra y devuelve False.
    Si mensaje_id viene vacío (no debería pasar), nunca se considera duplicado.
    """
    if not mensaje_id:
        return False
    with _LOCK:
        if mensaje_id in _mensajes_procesados_set:
            return True
        _mensajes_procesados_set.add(mensaje_id)
        _mensajes_procesados_orden.append(mensaje_id)
        if len(_mensajes_procesados_orden) > _MENSAJES_PROCESADOS_MAX:
            viejo = _mensajes_procesados_orden.popleft()
            _mensajes_procesados_set.discard(viejo)
        return False


def es_contacto_nuevo(contacto_id: str) -> bool:
    return contacto_id not in _ESTADOS


def obtener_estado(contacto_id: str) -> dict:
    with _LOCK:
        return _ESTADOS.get(contacto_id, {"etapa": "nuevo", "area": None, "respuestas": {}, "indice": 0})


def guardar_estado(contacto_id: str, estado: dict):
    with _LOCK:
        _ESTADOS[contacto_id] = estado


def obtener_historial(contacto_id: str):
    return _HISTORIALES.get(contacto_id, [])


def agregar_turno(contacto_id: str, rol: str, contenido: str):
    with _LOCK:
        historial = _HISTORIALES.setdefault(contacto_id, [])
        historial.append({"role": rol, "content": contenido})
        _HISTORIALES[contacto_id] = historial[-MAX_TURNOS:]


def guardar_cierre(cierre_id: str, datos: dict):
    """
    Guarda el paquete de documentos de cierre (contrato, poder, requerimientos,
    ya aprobados por el abogado) para que el cliente los pueda ver en
    /cierre/{cierre_id}. Igual que el resto de esta memoria, vive solo mientras
    el servicio esté corriendo (no sobrevive un redespliegue ni el "sueño" por
    inactividad); pensado para que el cliente abra el enlace poco después de
    que el abogado se lo envía, no semanas después.
    """
    with _LOCK:
        _CIERRES[cierre_id] = datos


def obtener_cierre(cierre_id: str):
    with _LOCK:
        return _CIERRES.get(cierre_id)


def registrar_contacto_csv(canal: str, contacto_id: str, texto: str):
    existe = os.path.exists(RUTA_CSV)
    try:
        with open(RUTA_CSV, "a", newline="", encoding="utf-8") as f:
            escritor = csv.writer(f)
            if not existe:
                escritor.writerow(["fecha", "canal", "contacto", "mensaje"])
            escritor.writerow([datetime.now().strftime("%Y-%m-%d %H:%M:%S"), canal, contacto_id, texto])
    except Exception as e:
        print(f"⚠️  No se pudo escribir en contactos.csv: {e}")
