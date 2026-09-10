# -*- coding: utf-8 -*-
"""
asistente_ia.py (copia autónoma para el servicio web asistente_meta)
Mismo "cerebro" que usa el programa de escritorio (asistente_ia.py en la carpeta
principal), para que las respuestas del despacho sean consistentes ya sea que el
cliente escriba por WhatsApp, Facebook o que el abogado use el programa de escritorio.
"""
import os

from openai import OpenAI

MODELO_POR_DEFECTO = os.getenv("OPENAI_MODEL", "gpt-4o-mini")

NOMBRE_DESPACHO = os.getenv("NOMBRE_DESPACHO", "Javier Londoño V. Abogados & Asociados")
HORARIO_ATENCION = os.getenv("HORARIO_ATENCION", "Lunes a viernes, 8:00 a.m. a 5:00 p.m.")
ESPECIALIDADES = os.getenv("ESPECIALIDADES", "Derecho de Familia, Derecho Notarial, Derecho Civil (incluye procesos de pertenencia/prescripción) y gestión de Accidentes de Tránsito")

SYSTEM_PROMPT = f"""Eres el asistente virtual de atención al cliente del despacho "{NOMBRE_DESPACHO}",
que escribe por WhatsApp o Facebook Messenger a nombre del despacho.

Especialidades del despacho: {ESPECIALIDADES}.
Horario de atención: {HORARIO_ATENCION}.

Tu trabajo en esta conversación:
1. Saludar de forma cálida y profesional, identificándote como el asistente virtual del despacho.
2. Entender brevemente el motivo de contacto de la persona (tipo de caso: familia, notarial,
   tránsito, u otro).
3. Recolectar datos básicos útiles para que el abogado dé seguimiento: nombre completo, y un
   resumen breve de la situación o consulta. Pide un dato a la vez, sin agobiar.
4. Puedes explicar de forma general y educativa cómo funcionan los procesos de tu especialidad
   en Colombia (por ejemplo, qué es una demanda de alimentos o una sucesión), pero SIEMPRE aclara
   que esto no es una asesoría jurídica definitiva y que el abogado revisará el caso personalmente.
5. Nunca des cifras exactas de honorarios, ni te comprometas en nombre del abogado a plazos o
   resultados de un proceso.
6. Si la persona quiere agendar una cita o hablar directamente con el abogado, dile que el
   despacho se pondrá en contacto pronto (o indícale el horario de atención) y que ya se avisó
   internamente de su mensaje.
7. Sé breve: mensajes cortos y claros, como se escribe en un chat, no como un documento formal.
8. Si detectas una emergencia o urgencia real (por ejemplo, una audiencia el mismo día, una
   medida de protección urgente), dilo explícitamente en tu respuesta para que quede claro que
   requiere atención prioritaria.
"""


def obtener_cliente():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("No se encontró OPENAI_API_KEY en las variables de entorno del servicio.")
    return OpenAI(api_key=api_key)


NOMBRES_AREA = {
    "area_alimentos": "Alimentos (Derecho de Familia)",
    "area_custodia": "Custodia y Visitas (Derecho de Familia)",
    "area_divorcio": "Divorcio (Derecho de Familia)",
    "area_union_marital": "Unión Marital de Hecho (Derecho de Familia)",
    "area_patria_potestad": "Patria Potestad (Derecho de Familia)",
    "area_sucesion": "Sucesión (Derecho Notarial)",
    "area_tramite_notarial": "Trámite Notarial / Registral (Derecho Notarial)",
    "area_transito": "Accidente de Tránsito / Reclamación a Aseguradora - SOAT",
    "area_pertenencia": "Pertenencia / Prescripción Adquisitiva (Derecho Civil)",
    "area_divisorio": "División de Bienes - Proindiviso (Derecho Civil)",
    "area_danos_obra": "Daños por Obra Pública (Derecho Civil)",
    "area_otro": "Consulta general",
}


def generar_viabilidad(area_id: str, respuestas: dict) -> str:
    """
    A partir de las respuestas del formulario de intake, genera una impresión
    preliminar y NO vinculante sobre el caso, en 4-6 líneas, en tono cercano
    (WhatsApp), y siempre recomendando la consulta con el abogado para un
    concepto definitivo.
    """
    area_nombre = NOMBRES_AREA.get(area_id, "Consulta")
    contexto = "\n".join(f"- {k}: {v}" for k, v in respuestas.items() if v)

    instruccion = (
        f"Un posible cliente completó un formulario breve de intake sobre {area_nombre}. "
        "Con base ÚNICAMENTE en los datos que dio (no invente hechos adicionales), escriba una "
        "respuesta breve (máximo 6 líneas, apta para WhatsApp) que:\n"
        "1) Resuma en una frase que entendió su situación.\n"
        "2) Dé una primera impresión general y prudente de viabilidad (por ejemplo: 'este tipo de "
        "casos suele tener buen fundamento cuando...', o 'esto requiere revisar unos documentos "
        "clave antes de poder decir más'), sin garantizar resultados ni dar cifras.\n"
        "3) Mencione, si aplica, uno o dos documentos o datos que sería bueno tener listos.\n"
        "4) Cierre indicando que esta es una impresión preliminar y que el abogado dará un "
        "concepto completo en la consulta.\n"
        "No use encabezados ni listas con viñetas, escriba como un mensaje de chat natural."
    )

    mensaje_completo = f"Datos del formulario:\n{contexto}\n\nInstrucción:\n{instruccion}"
    return responder(mensaje_completo)


def responder(mensaje_usuario: str, historial=None) -> str:
    """
    historial: lista de {"role": "user"/"assistant", "content": "..."} de la conversación
    reciente con este mismo contacto (memoria de corto plazo).
    """
    cliente = obtener_cliente()
    mensajes = [{"role": "system", "content": SYSTEM_PROMPT}]
    if historial:
        mensajes.extend(historial)
    mensajes.append({"role": "user", "content": mensaje_usuario})

    respuesta = cliente.chat.completions.create(
        model=MODELO_POR_DEFECTO,
        messages=mensajes,
        temperature=0.4,
        max_tokens=500,
    )
    return respuesta.choices[0].message.content.strip()
