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


# ---------------------------------------------------------------------------
# CIERRE DE NEGOCIO (paso 3): redacción con IA de contrato, poder y
# requerimientos, después de que el abogado tuvo la consulta personal con el
# cliente y decide tomar el caso.
# ---------------------------------------------------------------------------

def _redactar_texto_legal(instruccion: str, max_tokens: int = 1200) -> str:
    """
    Llamada genérica a la IA para redactar un documento legal. Se usa un
    "system prompt" distinto al de las conversaciones de WhatsApp: aquí se le
    pide a la IA que redacte como un asistente jurídico que prepara borradores
    para que el abogado los revise, no que converse con un cliente.
    """
    cliente = obtener_cliente()
    system = (
        f"Eres un asistente jurídico que ayuda a un abogado colombiano del despacho "
        f"\"{NOMBRE_DESPACHO}\" a preparar BORRADORES de documentos legales, a partir de los "
        "datos de un caso que el cliente ya aceptó en una consulta personal. Redacta en "
        "español formal, estilo jurídico colombiano. Usa únicamente los datos que se te dan; "
        "cuando falte un dato necesario para el documento, déjalo marcado claramente entre "
        "corchetes (por ejemplo [VALOR DE LOS HONORARIOS], [CIUDAD]) en vez de inventarlo. "
        "Recuerda siempre que es un BORRADOR: el abogado lo revisará, ajustará y firmará "
        "antes de que tenga cualquier efecto. No agregues explicaciones fuera del documento "
        "mismo (ni introducciones tipo \"Aquí tienes el documento\"): responde solo con el "
        "texto del documento."
    )
    respuesta = cliente.chat.completions.create(
        model=MODELO_POR_DEFECTO,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": instruccion},
        ],
        temperature=0.3,
        max_tokens=max_tokens,
    )
    return respuesta.choices[0].message.content.strip()


def _contexto_caso_cierre(datos: dict) -> str:
    return (
        f"Cliente: {datos.get('nombre_cliente') or 'No especificado'}\n"
        f"Documento de identidad: {datos.get('documento_identidad') or 'No especificado'}\n"
        f"Ciudad: {datos.get('ciudad') or 'No especificado'}\n"
        f"Área / tipo de servicio: {datos.get('area') or 'No especificado'}\n"
        f"Resumen de la consulta (hechos y lo hablado con el abogado): "
        f"{datos.get('resumen_caso') or 'No especificado'}\n"
        f"Honorarios y forma de pago acordados: {datos.get('honorarios') or 'No especificados aún'}\n"
        f"Notas adicionales del abogado: {datos.get('notas') or 'Ninguna'}"
    )


def generar_documentos_cierre(datos: dict) -> dict:
    """
    datos: dict con nombre_cliente, documento_identidad, ciudad, area,
    resumen_caso, honorarios, notas (los que falten pueden venir vacíos).

    Devuelve {"contrato": str, "poder": str, "requerimientos": str}, tres
    borradores generados con IA a partir de ese caso concreto (no son
    plantillas fijas). El abogado debe revisarlos y ajustarlos antes de
    enviarlos al cliente.
    """
    contexto = _contexto_caso_cierre(datos)
    nombre = datos.get("nombre_cliente") or "el cliente"
    area = datos.get("area") or "el asunto encomendado"

    instruccion_contrato = (
        "Redacta un BORRADOR de CONTRATO DE PRESTACIÓN DE SERVICIOS PROFESIONALES entre el "
        f"despacho \"{NOMBRE_DESPACHO}\" (el abogado) y {nombre} (el cliente), para el caso "
        "descrito abajo. Incluye: encabezado con las partes, objeto del contrato (según el "
        "área y el resumen del caso), honorarios y forma de pago (o el espacio marcado si no "
        "se dieron), obligaciones del abogado, obligaciones del cliente, confidencialidad, "
        "duración o alcance del encargo, y un cierre para firma de ambas partes con fecha. "
        f"Datos del caso:\n{contexto}"
    )
    instruccion_poder = (
        "Redacta un BORRADOR de PODER ESPECIAL, en el formato usual en Colombia (conforme al "
        f"Código General del Proceso), mediante el cual {nombre} le otorga poder al abogado "
        f"del despacho \"{NOMBRE_DESPACHO}\" para la gestión judicial y/o extrajudicial del "
        f"asunto de {area} descrito abajo. Incluye las facultades típicas necesarias para ese "
        "tipo de trámite (representar, presentar y contestar solicitudes o demandas, conciliar, "
        "recibir, según aplique), y el espacio para firma, presentación personal o autenticación. "
        f"Datos del caso:\n{contexto}"
    )
    instruccion_requerimientos = (
        "A partir de estos datos de un caso que el cliente ya aceptó en consulta, elabora una "
        "lista breve y concreta (texto plano, apto para enviar por WhatsApp, sin encabezados "
        "raros) de: primero, los documentos y soportes que el cliente debe aportar para "
        "iniciar el trámite; segundo, cualquier información que quede pendiente por confirmar. "
        f"Sé específico según el tipo de caso ({area}), no genérico. "
        f"Datos del caso:\n{contexto}"
    )

    return {
        "contrato": _redactar_texto_legal(instruccion_contrato, max_tokens=1400),
        "poder": _redactar_texto_legal(instruccion_poder, max_tokens=1000),
        "requerimientos": _redactar_texto_legal(instruccion_requerimientos, max_tokens=500),
    }
