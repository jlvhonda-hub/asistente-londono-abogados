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
from datetime import datetime

_LOCK = threading.Lock()
_HISTORIALES = {}  # {contacto_id: [ {"role":..., "content":...}, ... ]}
_ESTADOS = {}  # {contacto_id: {"etapa":..., "area":..., "respuestas":{...}, ...}}
MAX_TURNOS = 8  # cuántos mensajes recientes se recuerdan por contacto

RUTA_CSV = os.path.join(os.path.dirname(os.path.abspath(__file__)), "contactos.csv")


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
