# -*- coding: utf-8 -*-
"""
flujo.py
Motor de conversación por pasos:
  saludo -> elegir directamente el tema específico del caso (un solo menú plano,
  igual a como ya se tenía armado antes: cada tema es su propia opción, con su
  propio formulario PDF ampliado — sin categorías intermedias)
  -> triage corto (3 preguntas por chat) -> impresión de viabilidad con IA
  -> se envía el formulario PDF ampliado correspondiente (para diligenciar con calma
     y devolver por este mismo chat junto con los documentos de soporte)
  -> oferta de consulta pagada -> enlace de pago Wompi

Este módulo no sabe nada de WhatsApp ni de Facebook: solo recibe el estado de la
conversación y el texto que escribió la persona, y devuelve una lista de mensajes
"genéricos" (texto, lista, botones, documento) que app.py traduce a cada canal.

Tipos de mensaje que puede devolver:
  {"tipo": "texto", "texto": "..."}
  {"tipo": "lista", "cuerpo": "...", "boton": "...", "opciones": [{"id","titulo"}, ...]}
  {"tipo": "botones", "cuerpo": "...", "opciones": [{"id","titulo"}, ...]}
  {"tipo": "documento", "archivo": "alimentos.pdf", "titulo": "...", "descripcion": "..."}
    -> app.py arma la URL pública real (BASE_URL + /formularios/<archivo>) y la envía
       como documento adjunto por WhatsApp/Messenger.

Nota técnica: WhatsApp solo permite hasta 10 opciones en un menú interactivo tipo
"lista", y aquí hay más de 10 temas — por eso el menú de temas se envía como texto
numerado corriente (funciona igual en WhatsApp y en Messenger, y no tiene ese límite).
"""
import os
import asistente_ia

NOMBRE_DESPACHO = os.getenv("NOMBRE_DESPACHO", "Javier Londoño V. Abogados & Asociados")
PRECIO_CONSULTA = os.getenv("PRECIO_CONSULTA", "$150.000 COP")
WOMPI_LINK_CONSULTA = os.getenv("WOMPI_LINK_CONSULTA", "")

# Formulario complementario para casos con más volumen de información/documentos
# de soporte (ver campo "anexos" en AREAS_MENU). Vive en la misma carpeta formularios/.
FORMULARIO_ANEXOS = "anexos_documentos.pdf"

# Menú plano: cada tema específico es su propia opción, con su propio formulario PDF.
# "pdf": None para la opción de "Otra consulta" (no tiene formulario ampliado).
# "web": slug del formulario web (ver formularios_web.py) para los temas que ya
# tienen su formulario en el navegador — si no está presente, se manda el PDF.
# "anexos": True para los temas que suelen requerir más soportes/documentos (bienes
# raíces, sucesiones, siniestros, trámites registrales): además del formulario del
# tema, se les envía también el formulario complementario "anexos_documentos.pdf"
# para que puedan relacionar y aportar ordenadamente los documentos de soporte.
AREAS_MENU = [
    {"id": "area_alimentos", "titulo": "Alimentos", "pdf": "alimentos.pdf", "web": "alimentos", "anexos": False,
     "claves": ["alimentos", "cuota alimentaria", "1"]},
    {"id": "area_custodia", "titulo": "Custodia y Visitas", "pdf": "custodia_visitas.pdf", "web": "custodia_visitas", "anexos": False,
     "claves": ["custodia", "visitas", "2"]},
    {"id": "area_divorcio", "titulo": "Divorcio", "pdf": "divorcio.pdf", "web": "divorcio", "anexos": False,
     "claves": ["divorcio", "3"]},
    {"id": "area_union_marital", "titulo": "Unión Marital de Hecho", "pdf": "union_marital.pdf", "web": "union_marital", "anexos": False,
     "claves": ["union marital", "unión marital", "marital", "4"]},
    {"id": "area_patria_potestad", "titulo": "Patria Potestad", "pdf": "patria_potestad.pdf", "web": "patria_potestad", "anexos": False,
     "claves": ["patria potestad", "5"]},
    {"id": "area_sucesion", "titulo": "Sucesión", "pdf": "sucesion.pdf", "web": "sucesion", "anexos": True,
     "claves": ["sucesion", "sucesión", "herencia", "6"]},
    {"id": "area_tramite_notarial", "titulo": "Trámite Notarial / Registral (poderes, escrituras, etc.)",
     "pdf": "tramite_notarial.pdf", "web": "tramite_notarial", "anexos": True,
     "claves": ["tramite", "trámite", "poder", "escritura", "registro", "7"]},
    {"id": "area_transito", "titulo": "Accidente de Tránsito / Reclamación a Aseguradora - SOAT",
     "pdf": "reclamacion_aseguradora_transito.pdf", "web": "reclamacion_aseguradora_transito", "anexos": True,
     "claves": ["transito", "tránsito", "accidente", "soat", "aseguradora", "8"]},
    {"id": "area_pertenencia", "titulo": "Pertenencia / Prescripción Adquisitiva", "pdf": "pertenencia.pdf",
     "web": "pertenencia", "anexos": True, "claves": ["pertenencia", "prescripcion", "prescripción", "9"]},
    {"id": "area_divisorio", "titulo": "División de Bienes (Proindiviso)", "pdf": "divisorio_proindiviso.pdf",
     "web": "divisorio_proindiviso", "anexos": True, "claves": ["divisorio", "proindiviso", "division de bienes", "división de bienes", "10"]},
    {"id": "area_danos_obra", "titulo": "Daños por Obra Pública", "pdf": "danos_obra_publica.pdf",
     "web": "danos_obra_publica", "anexos": True, "claves": ["danos", "daños", "obra publica", "obra pública", "11"]},
    {"id": "area_otro", "titulo": "Otra consulta", "pdf": None, "anexos": False,
     "claves": ["otro", "otra", "12"]},
]

PREGUNTAS_TRIAGE = [
    {"id": "nombre", "texto": "Para comenzar, ¿cuál es su *nombre completo*?"},
    {"id": "hechos", "texto": "Cuéntenos brevemente qué pasó o cuál es su situación."},
    {"id": "urgencia", "texto": "¿Tiene alguna fecha límite, audiencia o situación urgente? Si no, responda \"no\"."},
]

PREGUNTAS_OTRO = [
    {"id": "nombre", "texto": "Para comenzar, ¿cuál es su *nombre completo*?"},
    {"id": "hechos", "texto": "Cuéntenos en qué podemos ayudarle."},
]

CONSULTA_BOTONES = [
    {"id": "consulta_si", "titulo": "Sí, agendar", "claves": ["si", "sí", "1", "agendar", "quiero"]},
    {"id": "consulta_no", "titulo": "No, gracias", "claves": ["no", "2"]},
]

SALUDO = (
    f"¡Hola! 👋 Gracias por escribir a *{NOMBRE_DESPACHO}*.\n\n"
    "Soy el asistente virtual del despacho. Cuénteme, ¿cuál de estos temas se parece más a su caso?"
)


def _texto_menu_areas():
    lineas = [f"{i+1}. {op['titulo']}" for i, op in enumerate(AREAS_MENU)]
    return "\n".join(lineas) + "\n\nResponda con el número o el nombre del tema."


def _emparejar(texto_usuario: str, opciones: list):
    """
    Empareja lo que escribió la persona con una opción del menú.
    Primero busca coincidencia exacta (id interno, o el número exacto de la
    opción: "9" para la opción 9, sin que "1" haga falsa coincidencia dentro de
    "12"), y solo después busca por palabra clave dentro del texto.
    """
    t = (texto_usuario or "").strip().lower()
    for op in opciones:
        if t == op["id"]:
            return op
    for op in opciones:
        claves_numericas = [c for c in op["claves"] if c.isdigit()]
        if t in claves_numericas:
            return op
    for op in opciones:
        claves_texto = [c for c in op["claves"] if not c.isdigit()]
        if any(clave in t for clave in claves_texto):
            return op
    return None


def estado_inicial():
    return {"etapa": "nuevo", "area": None, "respuestas": {}, "indice": 0}


def _preguntas_actuales(estado):
    return PREGUNTAS_OTRO if estado["area"] == "area_otro" else PREGUNTAS_TRIAGE


def procesar(estado: dict, texto_usuario: str):
    etapa = estado.get("etapa", "nuevo")
    mensajes = []
    evento = None
    texto_lower = (texto_usuario or "").strip().lower()
    if texto_lower in ("menu", "menú", "inicio", "reiniciar"):
        estado = estado_inicial()
        etapa = "nuevo"

    # Si la conversación ya había terminado (con pago o sin él), cualquier mensaje
    # nuevo del cliente reinicia el menú en vez de caer en una etapa "muerta" que
    # ningún bloque de abajo maneja — sin esto, procesar() devolvía una lista vacía
    # de mensajes, y app.py interpretaba eso como pie para pasar a chat libre de IA
    # de forma permanente en esa conversación.
    if etapa in ("pago_enviado", "cerrado_sin_pago"):
        estado = estado_inicial()
        etapa = "nuevo"

    if etapa == "nuevo":
        mensajes.append({"tipo": "texto", "texto": SALUDO + "\n\n" + _texto_menu_areas()})
        estado["etapa"] = "esperando_area"
        return estado, mensajes, evento

    if etapa == "esperando_area":
        opcion = _emparejar(texto_usuario, AREAS_MENU)
        if not opcion:
            mensajes.append({"tipo": "texto", "texto": "No identifiqué el tema. Por favor responda con el número de una de estas opciones:\n\n" + _texto_menu_areas()})
            return estado, mensajes, evento

        estado["area"] = opcion["id"]
        estado["respuestas"] = {}
        estado["indice"] = 0
        estado["etapa"] = "formulario"
        preguntas = _preguntas_actuales(estado)
        mensajes.append({"tipo": "texto", "texto": f"Perfecto, {opcion['titulo']}. Le haré unas preguntas breves."})
        mensajes.append({"tipo": "texto", "texto": preguntas[0]["texto"]})
        return estado, mensajes, evento

    if etapa == "formulario":
        preguntas = _preguntas_actuales(estado)
        idx = estado.get("indice", 0)
        if idx < len(preguntas):
            pregunta_actual = preguntas[idx]
            estado["respuestas"][pregunta_actual["id"]] = texto_usuario
            idx += 1
            estado["indice"] = idx
        if idx < len(preguntas):
            mensajes.append({"tipo": "texto", "texto": preguntas[idx]["texto"]})
            return estado, mensajes, evento

        mensajes.append({"tipo": "texto", "texto": "Gracias. Estoy revisando la información…"})
        area_nombre = asistente_ia.NOMBRES_AREA.get(estado["area"], "Consulta")
        try:
            viabilidad = asistente_ia.generar_viabilidad(estado["area"], estado["respuestas"])
        except Exception:
            viabilidad = (
                "No pude generar el análisis automático en este momento, pero ya registré su caso "
                "y el abogado lo revisará personalmente."
            )
        estado["viabilidad"] = viabilidad
        mensajes.append({"tipo": "texto", "texto": viabilidad})

        web = _area_web(estado)
        if web:
            mensajes.append({
                "tipo": "formulario_web",
                "slug": web,
                "titulo": f"Formulario - {area_nombre}",
                "descripcion": (
                    "Le comparto el formulario para su caso. Lo llena directo desde este enlace, "
                    "sin necesidad de descargar ni imprimir nada, y puede adjuntar ahí mismo los "
                    "documentos que tenga disponibles:"
                ),
            })
        else:
            pdf = _area_pdf(estado)
            if pdf:
                mensajes.append({
                    "tipo": "documento",
                    "archivo": pdf,
                    "titulo": f"Formulario - {area_nombre}",
                    "descripcion": (
                        "Le comparto el formulario ampliado para su caso. Complételo con calma "
                        "(lo que no sepa o no aplique, escriba \"No aplica\" o \"No sé\") y devuélvalo por "
                        "este mismo chat junto con los documentos que tenga disponibles."
                    ),
                })

        if _area_anexos(estado) and FORMULARIO_ANEXOS:
            mensajes.append({
                "tipo": "documento",
                "archivo": FORMULARIO_ANEXOS,
                "titulo": "Formulario complementario - Anexos y documentos",
                "descripcion": (
                    "Este tipo de caso suele requerir varios documentos de soporte. Le comparto además "
                    "este formulario complementario para relacionarlos ordenadamente (escrituras, "
                    "certificados, recibos, fotos, etc.). Puede devolver ambos formularios y los "
                    "documentos juntos, por este mismo chat, cuando los tenga listos."
                ),
            })

        mensajes.append({
            "tipo": "botones",
            "cuerpo": f"¿Desea agendar una *consulta con el abogado* para profundizar en su caso? Valor: {PRECIO_CONSULTA}",
            "opciones": [{"id": o["id"], "titulo": o["titulo"]} for o in CONSULTA_BOTONES],
        })
        estado["etapa"] = "esperando_decision_consulta"
        return estado, mensajes, evento

    if etapa == "esperando_decision_consulta":
        opcion = _emparejar(texto_usuario, CONSULTA_BOTONES)
        if not opcion:
            mensajes.append({"tipo": "texto", "texto": "¿Podría confirmar? Responda \"Sí\" o \"No\", por favor:"})
            mensajes.append({
                "tipo": "botones", "cuerpo": f"Valor de la consulta: {PRECIO_CONSULTA}",
                "opciones": [{"id": o["id"], "titulo": o["titulo"]} for o in CONSULTA_BOTONES],
            })
            return estado, mensajes, evento

        if opcion["id"] == "consulta_si":
            if WOMPI_LINK_CONSULTA:
                mensajes.append({
                    "tipo": "texto",
                    "texto": (
                        f"Excelente. Puede realizar el pago de la consulta ({PRECIO_CONSULTA}) de forma segura aquí:\n"
                        f"{WOMPI_LINK_CONSULTA}\n\n"
                        "Apenas se confirme el pago, el abogado se pondrá en contacto para agendar el horario."
                    ),
                })
            else:
                mensajes.append({
                    "tipo": "texto",
                    "texto": "Perfecto, ya registré su solicitud de consulta. El despacho se pondrá en contacto pronto para coordinar el pago y el horario.",
                })
            estado["etapa"] = "pago_enviado"
        else:
            mensajes.append({
                "tipo": "texto",
                "texto": "Entendido, no hay problema. De todas formas dejé registrada su información y, si el abogado considera que puede orientarlo con algo puntual, se pondrá en contacto. Cuando complete y envíe el formulario, seguimos revisando su caso. ¡Gracias por escribir!",
            })
            estado["etapa"] = "cerrado_sin_pago"

        evento = "resumen_listo"
        return estado, mensajes, evento

    return estado, mensajes, evento


def _area_pdf(estado):
    area_id = estado.get("area")
    for op in AREAS_MENU:
        if op["id"] == area_id:
            return op.get("pdf")
    return None


def _area_web(estado):
    area_id = estado.get("area")
    for op in AREAS_MENU:
        if op["id"] == area_id:
            return op.get("web")
    return None


def _area_anexos(estado):
    area_id = estado.get("area")
    for op in AREAS_MENU:
        if op["id"] == area_id:
            return bool(op.get("anexos"))
    return False


# Alias de compatibilidad (por si algún otro módulo aún llama estos nombres):
def _subtema_nombre(estado):
    return None


def _subtema_pdf(estado):
    return _area_pdf(estado)
