# -*- coding: utf-8 -*-
"""
formularios_web.py
Formularios que el cliente llena directamente en el navegador (sin descargar
nada), como reemplazo del PDF que antes había que diligenciar por fuera y
devolver por WhatsApp. Pensado primero que nada para verse bien en el celular,
que es donde la mayoría de los clientes lo van a abrir.

Cómo se usa (ver app.py):
  GET  /formulario/{slug}          -> muestra el formulario (HTML)
  POST /formulario/{slug}/enviar   -> recibe las respuestas + archivos adjuntos,
                                       los envía por correo al abogado (ver
                                       notificaciones.notificar_formulario_web)
                                       y muestra una página de agradecimiento.

Para agregar un área nueva más adelante: agregar una entrada a FORMULARIOS con
su slug, título y secciones/campos — no hace falta tocar nada más de este
archivo, ni de app.py.
"""

import flujo

NOMBRE_DESPACHO = "Javier Londoño V. Abogados & Asociados"

# Tipos de campo soportados: "texto", "area" (texto largo), "select",
# "checkboxes" (multi-selección), "fecha".
FORMULARIOS = {
    # Formulario inicial: se envía justo después del saludo. En una sola
    # pantalla se piden los datos personales y se elige el tema del caso (las
    # opciones se toman directamente de flujo.AREAS_MENU, para no tener que
    # mantener la lista duplicada en dos archivos). Al enviarse, app.py lo
    # procesa de forma especial: además de avisarle al abogado, continúa la
    # conversación por WhatsApp/Messenger con la siguiente pregunta.
    "inicio": {
        "titulo": "Datos iniciales de la consulta",
        "secciones": [
            {
                "titulo": "Sus datos",
                "campos": [
                    {"id": "nombre_completo", "etiqueta": "Nombre completo", "tipo": "texto", "requerido": True},
                    {"id": "documento_identidad", "etiqueta": "Documento de identidad", "tipo": "texto"},
                    {"id": "correo", "etiqueta": "Correo electrónico", "tipo": "texto"},
                    {"id": "ciudad_departamento", "etiqueta": "Ciudad y departamento", "tipo": "texto"},
                ],
            },
            {
                "titulo": "Motivo de la consulta",
                "campos": [
                    {"id": "area", "etiqueta": "¿Cuál de estos temas se parece más a su caso?", "tipo": "select",
                     "requerido": True, "opciones": [op["titulo"] for op in flujo.AREAS_MENU]},
                ],
            },
        ],
    },
    "alimentos": {
        "titulo": "Formulario ampliado — Alimentos",
        "secciones": [
            {
                "titulo": "1. Identificación de la consulta y del cliente",
                "campos": [
                    {"id": "nombre_completo", "etiqueta": "Nombre completo", "tipo": "texto", "requerido": True},
                    {"id": "documento_identidad", "etiqueta": "Documento de identidad", "tipo": "texto"},
                    {"id": "correo", "etiqueta": "Correo electrónico", "tipo": "texto"},
                    {"id": "ciudad_departamento", "etiqueta": "Ciudad y departamento", "tipo": "texto"},
                    {"id": "direccion", "etiqueta": "Dirección de residencia", "tipo": "texto"},
                ],
            },
            {
                "titulo": "2. Datos de las partes y del beneficiario",
                "campos": [
                    {"id": "nombre_obligado", "etiqueta": "Nombre de la persona obligada a suministrar alimentos", "tipo": "texto"},
                    {"id": "documento_obligado", "etiqueta": "Documento del obligado, si lo conoce", "tipo": "texto"},
                    {"id": "ciudad_obligado", "etiqueta": "Ciudad de residencia del obligado", "tipo": "texto"},
                    {"id": "nombre_beneficiario", "etiqueta": "Nombre del beneficiario de los alimentos", "tipo": "texto"},
                    {"id": "edad_beneficiario", "etiqueta": "Edad del beneficiario", "tipo": "texto"},
                    {"id": "parentesco", "etiqueta": "Parentesco con la persona obligada", "tipo": "texto"},
                    {"id": "situacion_beneficiario", "etiqueta": "Situación del beneficiario", "tipo": "select",
                     "opciones": ["Menor de edad", "Mayor de edad estudiante", "Persona con discapacidad",
                                  "Cónyuge / compañero(a)", "Otro"]},
                ],
            },
            {
                "titulo": "3. Situación actual de los alimentos",
                "campos": [
                    {"id": "cuota_fijada", "etiqueta": "¿Existe cuota fijada actualmente?", "tipo": "select",
                     "opciones": ["Sí - por juez", "Sí - por comisaría / defensoría", "Sí - por conciliación",
                                  "Acuerdo privado", "No", "No sabe"]},
                    {"id": "valor_cuota", "etiqueta": "Valor actual de la cuota, si existe", "tipo": "texto"},
                    {"id": "fecha_acuerdo", "etiqueta": "Fecha aproximada del acuerdo o decisión", "tipo": "texto"},
                    {"id": "incumplimientos", "etiqueta": "Describa incumplimientos, retrasos o pagos parciales", "tipo": "area"},
                ],
            },
            {
                "titulo": "4. Necesidades y capacidad económica",
                "campos": [
                    {"id": "gastos_beneficiario", "etiqueta": "Gastos mensuales del beneficiario (alimentación, vivienda, educación, salud, transporte, otros)", "tipo": "area"},
                    {"id": "ingresos_solicitante", "etiqueta": "Ingresos y actividad económica de quien solicita los alimentos", "tipo": "area"},
                    {"id": "info_ingresos_obligado", "etiqueta": "Información que conozca sobre ingresos, empleo, bienes o capacidad económica del obligado", "tipo": "area"},
                    {"id": "gastos_extraordinarios", "etiqueta": "¿Hay gastos extraordinarios?", "tipo": "checkboxes",
                     "opciones": ["Salud", "Educación", "Terapias", "Transporte especial", "Vivienda", "Otros"]},
                ],
            },
            {
                "titulo": "5. Actuaciones y pruebas",
                "campos": [
                    {"id": "actuaciones", "etiqueta": "Actuaciones realizadas", "tipo": "checkboxes",
                     "opciones": ["Conciliación", "Comisaría de Familia", "Defensoría / ICBF", "Proceso judicial",
                                  "Denuncia por inasistencia alimentaria", "Ninguna"]},
                    {"id": "radicados", "etiqueta": "Indique radicados, fechas, entidades o juzgados si existen", "tipo": "area"},
                    {"id": "pruebas_disponibles", "etiqueta": "Pruebas disponibles", "tipo": "checkboxes",
                     "opciones": ["Registro civil", "Recibos y facturas", "Certificados escolares",
                                  "Historia / órdenes médicas", "Extractos / comprobantes de pago",
                                  "Chats / mensajes", "Decisiones previas", "Otros"]},
                ],
            },
            {
                "titulo": "Información complementaria",
                "campos": [
                    {"id": "relato_adicional", "etiqueta": "Relato adicional o información que considere importante", "tipo": "area"},
                    {"id": "resultado_esperado", "etiqueta": "¿Qué resultado espera obtener o cuál es su principal objetivo?", "tipo": "area"},
                    {"id": "urgencia", "etiqueta": "¿Existe alguna fecha, audiencia, vencimiento o situación urgente? Indique cuál.", "tipo": "area"},
                ],
            },
        ],
    },
    "custodia_visitas": {
        "titulo": "Formulario ampliado — Custodia y Visitas",
        "secciones": [
            {
                "titulo": "1. Identificación de la consulta y del cliente",
                "campos": [
                    {"id": "nombre_completo", "etiqueta": "Nombre completo", "tipo": "texto", "requerido": True},
                    {"id": "documento_identidad", "etiqueta": "Documento de identidad", "tipo": "texto"},
                    {"id": "correo", "etiqueta": "Correo electrónico", "tipo": "texto"},
                    {"id": "ciudad_departamento", "etiqueta": "Ciudad y departamento", "tipo": "texto"},
                    {"id": "direccion", "etiqueta": "Dirección de residencia", "tipo": "texto"},
                    {"id": "parentesco_solicitante", "etiqueta": "¿Qué es usted del menor o los menores?", "tipo": "select",
                     "opciones": ["Madre", "Padre", "Abuelo(a)", "Otro familiar", "Otro"]},
                ],
            },
            {
                "titulo": "2. Datos de la otra parte y de los menores",
                "campos": [
                    {"id": "nombre_otra_parte", "etiqueta": "Nombre completo de la otra parte (padre/madre)", "tipo": "texto"},
                    {"id": "documento_otra_parte", "etiqueta": "Documento de la otra parte, si lo conoce", "tipo": "texto"},
                    {"id": "ciudad_otra_parte", "etiqueta": "Ciudad de residencia de la otra parte", "tipo": "texto"},
                    {"id": "menores_involucrados", "etiqueta": "Nombres y edades de los menores involucrados", "tipo": "area"},
                    {"id": "con_quien_viven", "etiqueta": "¿Con quién viven actualmente los menores?", "tipo": "select",
                     "opciones": ["Con la madre", "Con el padre", "Alternado entre ambos", "Con un tercero (abuelos u otro)", "Otro"]},
                ],
            },
            {
                "titulo": "3. Situación actual de custodia y visitas",
                "campos": [
                    {"id": "custodia_fijada", "etiqueta": "¿Existe custodia o visitas fijadas actualmente?", "tipo": "select",
                     "opciones": ["Sí - por juez", "Sí - por comisaría / defensoría", "Sí - por conciliación",
                                  "Acuerdo privado (de palabra o escrito)", "No", "No sabe"]},
                    {"id": "fecha_acuerdo", "etiqueta": "Fecha aproximada del acuerdo o decisión", "tipo": "texto"},
                    {"id": "regimen_visitas_actual", "etiqueta": "Describa el régimen de visitas actual (días, horarios, entregas)", "tipo": "area"},
                    {"id": "incumplimientos", "etiqueta": "Describa incumplimientos, restricciones o dificultades para ver a los menores", "tipo": "area"},
                ],
            },
            {
                "titulo": "4. Motivo de la solicitud",
                "campos": [
                    {"id": "que_solicita", "etiqueta": "¿Qué está buscando?", "tipo": "checkboxes",
                     "opciones": ["Fijar custodia", "Modificar custodia", "Fijar régimen de visitas",
                                  "Modificar régimen de visitas", "Restablecer visitas suspendidas",
                                  "Restricción de visitas por riesgo", "Otro"]},
                    {"id": "razones_solicitud", "etiqueta": "Explique las razones de su solicitud", "tipo": "area"},
                    {"id": "riesgo_menor", "etiqueta": "¿Hay alguna situación de riesgo para el menor que deba conocer el despacho? (maltrato, negligencia, consumo de sustancias, etc.)", "tipo": "area"},
                ],
            },
            {
                "titulo": "5. Actuaciones y pruebas",
                "campos": [
                    {"id": "actuaciones", "etiqueta": "Actuaciones realizadas", "tipo": "checkboxes",
                     "opciones": ["Conciliación", "Comisaría de Familia", "Defensoría / ICBF", "Proceso judicial",
                                  "Denuncia penal", "Medida de protección", "Ninguna"]},
                    {"id": "radicados", "etiqueta": "Indique radicados, fechas, entidades o juzgados si existen", "tipo": "area"},
                    {"id": "pruebas_disponibles", "etiqueta": "Pruebas disponibles", "tipo": "checkboxes",
                     "opciones": ["Registro civil", "Certificados escolares", "Historia / órdenes médicas",
                                  "Chats / mensajes", "Fotos / videos", "Testigos", "Decisiones previas", "Otros"]},
                ],
            },
            {
                "titulo": "Información complementaria",
                "campos": [
                    {"id": "relato_adicional", "etiqueta": "Relato adicional o información que considere importante", "tipo": "area"},
                    {"id": "resultado_esperado", "etiqueta": "¿Qué resultado espera obtener o cuál es su principal objetivo?", "tipo": "area"},
                    {"id": "urgencia", "etiqueta": "¿Existe alguna fecha, audiencia, vencimiento o situación urgente? Indique cuál.", "tipo": "area"},
                ],
            },
        ],
    },
    "divorcio": {
        "titulo": "Formulario ampliado — Divorcio",
        "secciones": [
            {
                "titulo": "1. Identificación de la consulta y del cliente",
                "campos": [
                    {"id": "nombre_completo", "etiqueta": "Nombre completo", "tipo": "texto", "requerido": True},
                    {"id": "documento_identidad", "etiqueta": "Documento de identidad", "tipo": "texto"},
                    {"id": "correo", "etiqueta": "Correo electrónico", "tipo": "texto"},
                    {"id": "ciudad_departamento", "etiqueta": "Ciudad y departamento", "tipo": "texto"},
                    {"id": "direccion", "etiqueta": "Dirección de residencia", "tipo": "texto"},
                ],
            },
            {
                "titulo": "2. Datos del matrimonio y de la separación",
                "campos": [
                    {"id": "nombre_conyuge", "etiqueta": "Nombre completo del cónyuge", "tipo": "texto"},
                    {"id": "fecha_matrimonio", "etiqueta": "Fecha del matrimonio", "tipo": "texto"},
                    {"id": "lugar_matrimonio", "etiqueta": "Lugar del matrimonio", "tipo": "texto"},
                    {"id": "tipo_matrimonio", "etiqueta": "Tipo de matrimonio", "tipo": "select",
                     "opciones": ["Civil", "Religioso", "Otro"]},
                    {"id": "registro_civil_matrimonio", "etiqueta": "¿Cuenta con registro civil de matrimonio?", "tipo": "select",
                     "opciones": ["Sí", "No", "No sabe"]},
                    {"id": "fecha_separacion", "etiqueta": "Fecha aproximada de separación física", "tipo": "texto"},
                    {"id": "actualmente_conviven", "etiqueta": "¿Actualmente conviven?", "tipo": "select",
                     "opciones": ["Sí", "No"]},
                ],
            },
            {
                "titulo": "3. Hijos, custodia y alimentos",
                "campos": [
                    {"id": "tienen_hijos", "etiqueta": "¿Tienen hijos en común?", "tipo": "select",
                     "opciones": ["Sí", "No"]},
                    {"id": "hijos_datos", "etiqueta": "Nombres, edades y documento de cada hijo (si lo conoce), y con quién viven actualmente", "tipo": "area"},
                    {"id": "acuerdo_custodia_alimentos", "etiqueta": "¿Existe acuerdo o decisión previa sobre custodia, alimentos o visitas? Descríbalo", "tipo": "area"},
                    {"id": "condicion_medica_hijo", "etiqueta": "¿Algún hijo tiene condición médica, discapacidad o necesidad especial relevante?", "tipo": "area"},
                ],
            },
            {
                "titulo": "4. Situaciones de urgencia o protección",
                "campos": [
                    {"id": "violencia_riesgo", "etiqueta": "¿Existe violencia intrafamiliar, amenaza, medida de protección o riesgo actual?", "tipo": "select",
                     "opciones": ["Sí", "No", "Prefiero explicarlo al abogado"]},
                    {"id": "descripcion_riesgo", "etiqueta": "Describa brevemente la situación de riesgo o protección, si aplica (entidad, radicado, fecha)", "tipo": "area"},
                    {"id": "urgencia_riesgo", "etiqueta": "¿Hay una audiencia, citación o término próximo relacionado? Indique fecha y detalle", "tipo": "area"},
                ],
            },
            {
                "titulo": "5. Situación patrimonial",
                "campos": [
                    {"id": "capitulaciones", "etiqueta": "¿Celebraron capitulaciones matrimoniales?", "tipo": "select",
                     "opciones": ["Sí", "No", "No sabe"]},
                    {"id": "sociedad_liquidada", "etiqueta": "¿La sociedad conyugal ya fue liquidada?", "tipo": "select",
                     "opciones": ["Sí", "No", "No sabe"]},
                    {"id": "bienes_matrimonio", "etiqueta": "Bienes adquiridos durante el matrimonio (inmuebles, vehículos, empresas, cuentas, otros)", "tipo": "area"},
                    {"id": "deudas_matrimonio", "etiqueta": "Deudas u obligaciones adquiridas durante el matrimonio", "tipo": "area"},
                    {"id": "bienes_propios", "etiqueta": "Bienes que considera propios de cada cónyuge (anteriores, herencias, donaciones)", "tipo": "area"},
                    {"id": "bienes_limitaciones", "etiqueta": "¿Existen bienes con embargo, hipoteca, prenda, leasing u otra limitación?", "tipo": "area"},
                ],
            },
            {
                "titulo": "6. Forma de trámite y hechos relevantes",
                "campos": [
                    {"id": "acuerdo_divorcio", "etiqueta": "¿Existe acuerdo entre ambos cónyuges para divorciarse?", "tipo": "select",
                     "opciones": ["Sí", "No", "No está claro"]},
                    {"id": "temas_acuerdo_desacuerdo", "etiqueta": "Indique sobre qué temas ya están de acuerdo y en cuáles hay desacuerdo (hijos, alimentos, visitas, bienes, deudas, vivienda)", "tipo": "area"},
                    {"id": "hechos_relevantes", "etiqueta": "Relate cronológicamente los hechos que considera importantes para el estudio del caso", "tipo": "area"},
                    {"id": "intentos_previos", "etiqueta": "¿Se ha intentado conciliación, negociación, trámite notarial o proceso judicial anteriormente? Indique entidad, radicado y resultado", "tipo": "area"},
                    {"id": "abogado_contraparte", "etiqueta": "Nombre y datos del abogado de la contraparte, si los conoce", "tipo": "texto"},
                ],
            },
            {
                "titulo": "Información complementaria",
                "campos": [
                    {"id": "relato_adicional", "etiqueta": "Relato adicional o información que considere importante", "tipo": "area"},
                    {"id": "resultado_esperado", "etiqueta": "¿Qué resultado espera obtener o cuál es su principal objetivo?", "tipo": "area"},
                    {"id": "urgencia", "etiqueta": "¿Existe alguna fecha, audiencia, vencimiento o situación urgente? Indique cuál.", "tipo": "area"},
                ],
            },
        ],
    },
    "union_marital": {
        "titulo": "Formulario ampliado — Unión Marital de Hecho",
        "secciones": [
            {
                "titulo": "1. Identificación de la consulta y del cliente",
                "campos": [
                    {"id": "nombre_completo", "etiqueta": "Nombre completo", "tipo": "texto", "requerido": True},
                    {"id": "documento_identidad", "etiqueta": "Documento de identidad", "tipo": "texto"},
                    {"id": "correo", "etiqueta": "Correo electrónico", "tipo": "texto"},
                    {"id": "ciudad_departamento", "etiqueta": "Ciudad y departamento", "tipo": "texto"},
                    {"id": "direccion", "etiqueta": "Dirección de residencia", "tipo": "texto"},
                ],
            },
            {
                "titulo": "2. Datos de la pareja y convivencia",
                "campos": [
                    {"id": "nombre_pareja", "etiqueta": "Nombre completo de la pareja o expareja", "tipo": "texto"},
                    {"id": "documento_pareja", "etiqueta": "Documento de la pareja, si lo conoce", "tipo": "texto"},
                    {"id": "fecha_inicio_convivencia", "etiqueta": "Fecha aproximada de inicio de convivencia", "tipo": "texto"},
                    {"id": "fecha_fin_convivencia", "etiqueta": "Fecha de terminación, si ya terminó", "tipo": "texto"},
                    {"id": "actualmente_conviven", "etiqueta": "¿Actualmente conviven?", "tipo": "select",
                     "opciones": ["Sí", "No", "Intermitentemente"]},
                    {"id": "lugares_periodos", "etiqueta": "Lugares donde convivieron y periodos aproximados", "tipo": "area"},
                    {"id": "estado_civil_convivencia", "etiqueta": "Estado civil durante la convivencia", "tipo": "select",
                     "opciones": ["Ambos solteros", "Alguno casado", "Alguno con sociedad conyugal vigente", "No sabe"]},
                ],
            },
            {
                "titulo": "3. Bienes, deudas y aportes",
                "campos": [
                    {"id": "bienes_convivencia", "etiqueta": "Bienes adquiridos durante la convivencia — liste titular registrado, fecha aproximada y forma de adquisición", "tipo": "area"},
                    {"id": "deudas_convivencia", "etiqueta": "Deudas adquiridas durante la convivencia", "tipo": "area"},
                    {"id": "aportes_economicos", "etiqueta": "Aportes económicos o de trabajo de cada integrante de la pareja", "tipo": "area"},
                ],
            },
            {
                "titulo": "4. Hijos, acuerdos y actuaciones",
                "campos": [
                    {"id": "tuvieron_hijos", "etiqueta": "¿Tuvieron hijos en común?", "tipo": "select",
                     "opciones": ["Sí", "No"]},
                    {"id": "hijos_acuerdos", "etiqueta": "Si hay hijos, indique nombres, edades y acuerdos sobre custodia, visitas y alimentos", "tipo": "area"},
                    {"id": "actuaciones", "etiqueta": "Actuaciones realizadas", "tipo": "checkboxes",
                     "opciones": ["Conciliación", "Notaría", "Demanda judicial", "Acuerdo privado", "Ninguna"]},
                    {"id": "fechas_radicados", "etiqueta": "Indique fechas, radicados o documentos existentes", "tipo": "area"},
                    {"id": "objetivo_principal", "etiqueta": "Objetivo principal", "tipo": "select",
                     "opciones": ["Declarar unión marital", "Declarar sociedad patrimonial", "Liquidar sociedad patrimonial",
                                  "Defenderse de reclamación", "Reconocer bienes / aportes", "Otro"]},
                ],
            },
            {
                "titulo": "Información complementaria",
                "campos": [
                    {"id": "relato_adicional", "etiqueta": "Relato adicional o información que considere importante", "tipo": "area"},
                    {"id": "resultado_esperado", "etiqueta": "¿Qué resultado espera obtener o cuál es su principal objetivo?", "tipo": "area"},
                    {"id": "urgencia", "etiqueta": "¿Existe alguna fecha, audiencia, vencimiento o situación urgente? Indique cuál.", "tipo": "area"},
                ],
            },
        ],
    },
    "patria_potestad": {
        "titulo": "Formulario ampliado — Patria Potestad",
        "secciones": [
            {
                "titulo": "1. Identificación de la consulta y del cliente",
                "campos": [
                    {"id": "nombre_completo", "etiqueta": "Nombre completo", "tipo": "texto", "requerido": True},
                    {"id": "documento_identidad", "etiqueta": "Documento de identidad", "tipo": "texto"},
                    {"id": "correo", "etiqueta": "Correo electrónico", "tipo": "texto"},
                    {"id": "ciudad_departamento", "etiqueta": "Ciudad y departamento", "tipo": "texto"},
                    {"id": "direccion", "etiqueta": "Dirección de residencia", "tipo": "texto"},
                ],
            },
            {
                "titulo": "2. Datos del menor y de los progenitores",
                "campos": [
                    {"id": "nombre_menor", "etiqueta": "Nombre completo del menor", "tipo": "texto"},
                    {"id": "edad_menor", "etiqueta": "Edad del menor", "tipo": "texto"},
                    {"id": "nombre_otro_progenitor", "etiqueta": "Nombre del otro progenitor", "tipo": "texto"},
                    {"id": "documento_otro_progenitor", "etiqueta": "Documento del otro progenitor, si lo conoce", "tipo": "texto"},
                    {"id": "ciudad_otro_progenitor", "etiqueta": "Ciudad / país donde reside el otro progenitor", "tipo": "texto"},
                ],
            },
            {
                "titulo": "3. Situación que origina la consulta",
                "campos": [
                    {"id": "motivo_principal", "etiqueta": "Motivo principal", "tipo": "select",
                     "opciones": ["Ausencia prolongada", "Abandono", "Incumplimiento grave de deberes", "Violencia / maltrato",
                                  "Condena o situación penal", "Imposibilidad de ubicar al progenitor",
                                  "Desacuerdo para trámites del menor", "Otro"]},
                    {"id": "hechos_situacion", "etiqueta": "Describa los hechos, fechas y duración de la situación", "tipo": "area"},
                    {"id": "contacto_otro_progenitor", "etiqueta": "¿El otro progenitor mantiene contacto con el menor? ¿Cumple obligaciones económicas?", "tipo": "area"},
                ],
            },
            {
                "titulo": "4. Decisiones, procesos y trámite requerido",
                "campos": [
                    {"id": "actuaciones_existentes", "etiqueta": "Actuaciones o decisiones existentes", "tipo": "checkboxes",
                     "opciones": ["Custodia", "Alimentos", "Visitas", "Medidas de protección", "Proceso penal",
                                  "Proceso de patria potestad previo", "Ninguna"]},
                    {"id": "juzgado_radicado", "etiqueta": "Indique juzgado, comisaría, radicado y resultado si existe", "tipo": "area"},
                    {"id": "tramite_requerido", "etiqueta": "Trámite que necesita realizar respecto del menor", "tipo": "checkboxes",
                     "opciones": ["Pasaporte / salida del país", "Matrícula / educación", "Salud", "Administración de bienes",
                                  "Cambio de residencia", "Otro"]},
                    {"id": "razon_intervencion", "etiqueta": "Explique por qué requiere intervención jurídica en este momento", "tipo": "area"},
                ],
            },
            {
                "titulo": "Información complementaria",
                "campos": [
                    {"id": "relato_adicional", "etiqueta": "Relato adicional o información que considere importante", "tipo": "area"},
                    {"id": "resultado_esperado", "etiqueta": "¿Qué resultado espera obtener o cuál es su principal objetivo?", "tipo": "area"},
                    {"id": "urgencia", "etiqueta": "¿Existe alguna fecha, audiencia, vencimiento o situación urgente? Indique cuál.", "tipo": "area"},
                ],
            },
        ],
    },
    "sucesion": {
        "titulo": "Formulario ampliado — Sucesión",
        "secciones": [
            {
                "titulo": "1. Identificación de la consulta y del cliente",
                "campos": [
                    {"id": "nombre_completo", "etiqueta": "Nombre completo", "tipo": "texto", "requerido": True},
                    {"id": "documento_identidad", "etiqueta": "Documento de identidad", "tipo": "texto"},
                    {"id": "correo", "etiqueta": "Correo electrónico", "tipo": "texto"},
                    {"id": "ciudad_departamento", "etiqueta": "Ciudad y departamento", "tipo": "texto"},
                    {"id": "direccion", "etiqueta": "Dirección de residencia", "tipo": "texto"},
                ],
            },
            {
                "titulo": "2. Datos del causante",
                "campos": [
                    {"id": "nombre_causante", "etiqueta": "Nombre completo de la persona fallecida", "tipo": "texto"},
                    {"id": "documento_causante", "etiqueta": "Documento de identidad del causante", "tipo": "texto"},
                    {"id": "fecha_fallecimiento", "etiqueta": "Fecha de fallecimiento", "tipo": "texto"},
                    {"id": "ultimo_domicilio", "etiqueta": "Último domicilio y lugar de fallecimiento", "tipo": "texto"},
                    {"id": "registro_defuncion", "etiqueta": "¿Existe registro civil de defunción?", "tipo": "select",
                     "opciones": ["Sí", "No", "En trámite"]},
                ],
            },
            {
                "titulo": "3. Herederos y testamento",
                "campos": [
                    {"id": "posibles_herederos", "etiqueta": "Posibles herederos", "tipo": "checkboxes",
                     "opciones": ["Cónyuge / compañero(a)", "Hijos", "Padres", "Hermanos", "Sobrinos", "Otros"]},
                    {"id": "herederos_datos", "etiqueta": "Liste nombres, parentesco, documento y datos de contacto de los posibles herederos", "tipo": "area"},
                    {"id": "menores_discapacidad", "etiqueta": "¿Hay menores de edad o personas con apoyos / discapacidad entre los interesados?", "tipo": "select",
                     "opciones": ["Sí", "No", "No sabe"]},
                    {"id": "existe_testamento", "etiqueta": "¿Existe testamento? Indique notaría, fecha y datos conocidos si existe", "tipo": "area"},
                ],
            },
            {
                "titulo": "4. Activos, pasivos y trámite",
                "campos": [
                    {"id": "bienes_conocidos", "etiqueta": "Bienes conocidos", "tipo": "checkboxes",
                     "opciones": ["Inmuebles", "Vehículos", "Cuentas bancarias", "CDT / inversiones",
                                  "Acciones / participaciones", "Negocios", "Muebles de valor", "Otros"]},
                    {"id": "bienes_datos", "etiqueta": "Liste bienes, ubicación, matrícula/placa/cuenta y valor aproximado", "tipo": "area"},
                    {"id": "deudas_causante", "etiqueta": "Deudas, impuestos, créditos u obligaciones pendientes", "tipo": "area"},
                    {"id": "sociedad_conyugal_pendiente", "etiqueta": "¿Había sociedad conyugal o patrimonial pendiente de liquidar?", "tipo": "select",
                     "opciones": ["Sí", "No", "No sabe"]},
                    {"id": "estado_tramite", "etiqueta": "Estado del trámite (notaría, juzgado, no iniciado) — indique radicado y actuaciones realizadas", "tipo": "area"},
                    {"id": "conflicto_interesados", "etiqueta": "¿Existe conflicto entre interesados? Describa desacuerdos sobre herederos, bienes o reparto", "tipo": "area"},
                ],
            },
            {
                "titulo": "Información complementaria",
                "campos": [
                    {"id": "relato_adicional", "etiqueta": "Relato adicional o información que considere importante", "tipo": "area"},
                    {"id": "resultado_esperado", "etiqueta": "¿Qué resultado espera obtener o cuál es su principal objetivo?", "tipo": "area"},
                    {"id": "urgencia", "etiqueta": "¿Existe alguna fecha, audiencia, vencimiento o situación urgente? Indique cuál.", "tipo": "area"},
                ],
            },
        ],
    },
    "tramite_notarial": {
        "titulo": "Formulario ampliado — Trámite Notarial / Registral",
        "secciones": [
            {
                "titulo": "1. Identificación de la consulta y del cliente",
                "campos": [
                    {"id": "nombre_completo", "etiqueta": "Nombre completo", "tipo": "texto", "requerido": True},
                    {"id": "documento_identidad", "etiqueta": "Documento de identidad", "tipo": "texto"},
                    {"id": "correo", "etiqueta": "Correo electrónico", "tipo": "texto"},
                    {"id": "ciudad_departamento", "etiqueta": "Ciudad y departamento", "tipo": "texto"},
                    {"id": "direccion", "etiqueta": "Dirección de residencia", "tipo": "texto"},
                ],
            },
            {
                "titulo": "2. Datos del inmueble y del documento",
                "campos": [
                    {"id": "direccion_inmueble", "etiqueta": "Dirección / ubicación del inmueble", "tipo": "texto"},
                    {"id": "matricula_inmobiliaria", "etiqueta": "Matrícula inmobiliaria", "tipo": "texto"},
                    {"id": "municipio_registral", "etiqueta": "Municipio / círculo registral", "tipo": "texto"},
                    {"id": "escritura_numero_fecha", "etiqueta": "Número y fecha de escritura, y notaría donde se otorgó, si existe", "tipo": "texto"},
                    {"id": "tipo_tramite", "etiqueta": "Tipo de trámite", "tipo": "select",
                     "opciones": ["Compraventa", "Aclaración / corrección", "Sucesión", "Cancelación de gravamen",
                                  "Hipoteca", "Englobe / desenglobe", "Afectación a vivienda familiar",
                                  "Patrimonio de familia", "Registro pendiente / devuelto", "Otro"]},
                ],
            },
            {
                "titulo": "3. Problema o actuación requerida",
                "campos": [
                    {"id": "explicacion_tramite", "etiqueta": "Explique el trámite que desea realizar o el inconveniente presentado", "tipo": "area"},
                    {"id": "presentado_registro", "etiqueta": "¿El documento fue presentado a registro? Indique fecha de radicación y número de turno si lo conoce", "tipo": "area"},
                    {"id": "nota_devolutiva", "etiqueta": "Si hubo nota devolutiva o rechazo, transcriba o resuma las causales", "tipo": "area"},
                ],
            },
            {
                "titulo": "4. Titulares, gravámenes y documentos",
                "campos": [
                    {"id": "titulares", "etiqueta": "Nombre e identificación de propietarios, vendedores, compradores u otros interesados", "tipo": "area"},
                    {"id": "situaciones_registrales", "etiqueta": "Situaciones registrales conocidas", "tipo": "checkboxes",
                     "opciones": ["Hipoteca", "Embargo", "Patrimonio de familia", "Afectación a vivienda familiar",
                                  "Usufructo", "Falsa tradición", "Limitación / condición", "Ninguna / no sabe"]},
                    {"id": "documentos_disponibles", "etiqueta": "Documentos disponibles", "tipo": "checkboxes",
                     "opciones": ["Escritura", "Certificado de tradición", "Nota devolutiva", "Paz y salvo predial",
                                  "Paz y salvo valorización", "Certificado catastral", "Poder", "Registros civiles", "Otros"]},
                ],
            },
            {
                "titulo": "Información complementaria",
                "campos": [
                    {"id": "relato_adicional", "etiqueta": "Relato adicional o información que considere importante", "tipo": "area"},
                    {"id": "resultado_esperado", "etiqueta": "¿Qué resultado espera obtener o cuál es su principal objetivo?", "tipo": "area"},
                    {"id": "urgencia", "etiqueta": "¿Existe alguna fecha, audiencia, vencimiento o situación urgente? Indique cuál.", "tipo": "area"},
                ],
            },
        ],
    },
    "reclamacion_aseguradora_transito": {
        "titulo": "Formulario ampliado — Accidente de Tránsito / Reclamación a Aseguradora",
        "secciones": [
            {
                "titulo": "1. Identificación de la consulta y del cliente",
                "campos": [
                    {"id": "nombre_completo", "etiqueta": "Nombre completo", "tipo": "texto", "requerido": True},
                    {"id": "documento_identidad", "etiqueta": "Documento de identidad", "tipo": "texto"},
                    {"id": "correo", "etiqueta": "Correo electrónico", "tipo": "texto"},
                    {"id": "ciudad_departamento", "etiqueta": "Ciudad y departamento", "tipo": "texto"},
                    {"id": "direccion", "etiqueta": "Dirección de residencia", "tipo": "texto"},
                ],
            },
            {
                "titulo": "2. Datos del accidente",
                "campos": [
                    {"id": "fecha_hora_accidente", "etiqueta": "Fecha y hora aproximada del accidente", "tipo": "texto"},
                    {"id": "lugar_accidente", "etiqueta": "Lugar exacto / municipio del accidente", "tipo": "texto"},
                    {"id": "descripcion_accidente", "etiqueta": "Describa brevemente cómo ocurrió el accidente", "tipo": "area"},
                    {"id": "tipo_afectacion", "etiqueta": "Tipo de afectación", "tipo": "checkboxes",
                     "opciones": ["Daños al vehículo", "Lesiones personales", "Fallecimiento", "Daños a otros bienes",
                                  "Incapacidad / pérdida de ingresos", "Otro"]},
                    {"id": "autoridad_transito", "etiqueta": "¿Intervino autoridad de tránsito o policía? Indique número de informe / IPAT si lo conoce", "tipo": "area"},
                ],
            },
            {
                "titulo": "3. Vehículos, conductores y seguros",
                "campos": [
                    {"id": "placa_propia", "etiqueta": "Placa de su vehículo", "tipo": "texto"},
                    {"id": "placa_tercero", "etiqueta": "Placa del otro vehículo", "tipo": "texto"},
                    {"id": "conductores_datos", "etiqueta": "Nombre y datos de conductores, propietarios y terceros involucrados", "tipo": "area"},
                    {"id": "aseguradora_propia", "etiqueta": "Aseguradora propia y número de póliza", "tipo": "texto"},
                    {"id": "aseguradora_tercero", "etiqueta": "Aseguradora del tercero si la conoce", "tipo": "texto"},
                    {"id": "coberturas", "etiqueta": "Coberturas que conoce", "tipo": "checkboxes",
                     "opciones": ["Responsabilidad civil", "Pérdida total", "Daños parciales", "Asistencia jurídica", "SOAT", "Desconoce"]},
                ],
            },
            {
                "titulo": "4. Daños, lesiones y reclamación",
                "campos": [
                    {"id": "danos_materiales", "etiqueta": "Daños materiales y valor estimado / cotizaciones disponibles", "tipo": "area"},
                    {"id": "lesiones_tratamientos", "etiqueta": "Lesiones, atención médica, incapacidades y tratamientos", "tipo": "area"},
                    {"id": "gastos_perdidas", "etiqueta": "Gastos y pérdidas económicas derivados del accidente", "tipo": "area"},
                    {"id": "reclamacion_previa", "etiqueta": "¿Ya presentó reclamación a la aseguradora? Indique fecha y número de siniestro", "tipo": "area"},
                    {"id": "respuesta_aseguradora", "etiqueta": "Respuesta de la aseguradora", "tipo": "select",
                     "opciones": ["Aprobó", "Negó", "Objetó / pidió documentos", "Oferta parcial", "Sin respuesta", "No aplica"]},
                    {"id": "explicacion_respuesta", "etiqueta": "Explique razones de negación, objeción u oferta si existen", "tipo": "area"},
                    {"id": "pruebas_disponibles", "etiqueta": "Pruebas disponibles", "tipo": "checkboxes",
                     "opciones": ["IPAT / croquis", "Fotos / videos", "Póliza", "Cotizaciones / facturas",
                                  "Historia clínica", "Incapacidades", "Testigos", "Comunicaciones con aseguradora", "Otros"]},
                ],
            },
            {
                "titulo": "Información complementaria",
                "campos": [
                    {"id": "relato_adicional", "etiqueta": "Relato adicional o información que considere importante", "tipo": "area"},
                    {"id": "resultado_esperado", "etiqueta": "¿Qué resultado espera obtener o cuál es su principal objetivo?", "tipo": "area"},
                    {"id": "urgencia", "etiqueta": "¿Existe alguna fecha, audiencia, vencimiento o situación urgente? Indique cuál.", "tipo": "area"},
                ],
            },
        ],
    },
    "pertenencia": {
        "titulo": "Formulario ampliado — Pertenencia / Prescripción Adquisitiva",
        "secciones": [
            {
                "titulo": "1. Identificación de la consulta y del cliente",
                "campos": [
                    {"id": "nombre_completo", "etiqueta": "Nombre completo", "tipo": "texto", "requerido": True},
                    {"id": "documento_identidad", "etiqueta": "Documento de identidad", "tipo": "texto"},
                    {"id": "correo", "etiqueta": "Correo electrónico", "tipo": "texto"},
                    {"id": "ciudad_departamento", "etiqueta": "Ciudad y departamento", "tipo": "texto"},
                    {"id": "direccion", "etiqueta": "Dirección de residencia", "tipo": "texto"},
                ],
            },
            {
                "titulo": "2. Identificación del inmueble",
                "campos": [
                    {"id": "direccion_inmueble", "etiqueta": "Dirección o ubicación del inmueble", "tipo": "texto"},
                    {"id": "municipio_inmueble", "etiqueta": "Municipio / departamento", "tipo": "texto"},
                    {"id": "matricula_chip", "etiqueta": "Matrícula inmobiliaria y/o cédula catastral (CHIP), si las conoce", "tipo": "texto"},
                    {"id": "propietario_registrado", "etiqueta": "Nombre del propietario registrado, si lo conoce", "tipo": "texto"},
                    {"id": "tipo_inmueble", "etiqueta": "Tipo de inmueble", "tipo": "select",
                     "opciones": ["Casa / apartamento", "Lote", "Finca / rural", "Local / bodega", "Otro"]},
                ],
            },
            {
                "titulo": "3. Posesión",
                "campos": [
                    {"id": "fecha_inicio_posesion", "etiqueta": "Fecha aproximada en que inició la posesión y años que lleva en posesión", "tipo": "texto"},
                    {"id": "forma_ingreso", "etiqueta": "Forma en que ingresó al inmueble", "tipo": "select",
                     "opciones": ["Compra informal", "Cesión", "Herencia / sucesión no formalizada", "Permiso inicial",
                                  "Ocupación directa", "Otro"]},
                    {"id": "explicacion_posesion", "etiqueta": "Explique cómo adquirió la posesión y de quién la recibió", "tipo": "area"},
                    {"id": "actos_senor_dueno", "etiqueta": "Actos de señor y dueño que ha realizado", "tipo": "checkboxes",
                     "opciones": ["Pago de impuestos", "Servicios públicos", "Construcciones / mejoras", "Cercas / linderos",
                                  "Arrendamiento a terceros", "Cultivos / explotación", "Mantenimiento", "Otros"]},
                    {"id": "mejoras_descripcion", "etiqueta": "Describa mejoras, construcciones, inversiones y fechas aproximadas", "tipo": "area"},
                    {"id": "caracteristicas_posesion", "etiqueta": "Características de la posesión y si ha tenido interrupciones u oposición — explique", "tipo": "area"},
                ],
            },
            {
                "titulo": "4. Titularidad, vecinos y pruebas",
                "campos": [
                    {"id": "situacion_titular", "etiqueta": "Situación del titular registrado", "tipo": "select",
                     "opciones": ["Lo conoce", "Falleció", "No se conoce ubicación", "Ha reclamado el inmueble",
                                  "Nunca ha reclamado", "No sabe"]},
                    {"id": "vecinos_testigos", "etiqueta": "Nombre y contacto de vecinos o testigos que conozcan la posesión", "tipo": "area"},
                    {"id": "pruebas_disponibles", "etiqueta": "Pruebas disponibles", "tipo": "checkboxes",
                     "opciones": ["Recibos servicios", "Impuesto predial", "Facturas de mejoras", "Contratos / cesiones",
                                  "Fotos antiguas", "Certificados catastrales", "Declaraciones / testigos", "Otros"]},
                    {"id": "proceso_existente", "etiqueta": "¿Existe proceso judicial o administrativo sobre el inmueble? Indique proceso, radicado, entidad y estado", "tipo": "area"},
                ],
            },
            {
                "titulo": "Información complementaria",
                "campos": [
                    {"id": "relato_adicional", "etiqueta": "Relato adicional o información que considere importante", "tipo": "area"},
                    {"id": "resultado_esperado", "etiqueta": "¿Qué resultado espera obtener o cuál es su principal objetivo?", "tipo": "area"},
                    {"id": "urgencia", "etiqueta": "¿Existe alguna fecha, audiencia, vencimiento o situación urgente? Indique cuál.", "tipo": "area"},
                ],
            },
        ],
    },
    "divisorio_proindiviso": {
        "titulo": "Formulario ampliado — Divisorio / Proindiviso",
        "secciones": [
            {
                "titulo": "1. Identificación de la consulta y del cliente",
                "campos": [
                    {"id": "nombre_completo", "etiqueta": "Nombre completo", "tipo": "texto", "requerido": True},
                    {"id": "documento_identidad", "etiqueta": "Documento de identidad", "tipo": "texto"},
                    {"id": "correo", "etiqueta": "Correo electrónico", "tipo": "texto"},
                    {"id": "ciudad_departamento", "etiqueta": "Ciudad y departamento", "tipo": "texto"},
                    {"id": "direccion", "etiqueta": "Dirección de residencia", "tipo": "texto"},
                ],
            },
            {
                "titulo": "2. Identificación del bien y copropietarios",
                "campos": [
                    {"id": "direccion_bien", "etiqueta": "Dirección / ubicación del inmueble o bien", "tipo": "texto"},
                    {"id": "matricula_municipio", "etiqueta": "Matrícula inmobiliaria si aplica, y municipio / departamento", "tipo": "texto"},
                    {"id": "copropietarios", "etiqueta": "Liste todos los copropietarios y el porcentaje o cuota de cada uno si lo conoce", "tipo": "area"},
                    {"id": "origen_copropiedad", "etiqueta": "Origen de la copropiedad", "tipo": "select",
                     "opciones": ["Compra conjunta", "Sucesión", "Sociedad / liquidación", "Adjudicación judicial", "Otro"]},
                ],
            },
            {
                "titulo": "3. Uso, posesión y gastos",
                "campos": [
                    {"id": "uso_actual", "etiqueta": "Uso actual del bien", "tipo": "select",
                     "opciones": ["Lo ocupa un copropietario", "Lo ocupan varios", "Está arrendado", "Está desocupado", "Otro"]},
                    {"id": "quien_usa_administra", "etiqueta": "Explique quién usa o administra el bien y desde cuándo", "tipo": "area"},
                    {"id": "gastos_quien_paga", "etiqueta": "Impuestos, administración, servicios, créditos y otros gastos: quién los paga", "tipo": "area"},
                    {"id": "mejoras_inversiones", "etiqueta": "Mejoras o inversiones realizadas por cada copropietario", "tipo": "area"},
                ],
            },
            {
                "titulo": "4. Intentos de acuerdo y objetivo",
                "campos": [
                    {"id": "intento_acuerdo", "etiqueta": "¿Han intentado vender o dividir voluntariamente? Describa propuestas, acuerdos fallidos u ofertas", "tipo": "area"},
                    {"id": "objetivo_principal", "etiqueta": "Objetivo principal", "tipo": "select",
                     "opciones": ["División material", "Venta del bien y reparto", "Comprar cuotas de otros",
                                  "Vender su cuota", "Rendición de cuentas / frutos", "Otro"]},
                    {"id": "gravamenes", "etiqueta": "¿Existen embargos, hipotecas u otras limitaciones? Indique gravámenes, procesos o acreedores conocidos", "tipo": "area"},
                ],
            },
            {
                "titulo": "Información complementaria",
                "campos": [
                    {"id": "relato_adicional", "etiqueta": "Relato adicional o información que considere importante", "tipo": "area"},
                    {"id": "resultado_esperado", "etiqueta": "¿Qué resultado espera obtener o cuál es su principal objetivo?", "tipo": "area"},
                    {"id": "urgencia", "etiqueta": "¿Existe alguna fecha, audiencia, vencimiento o situación urgente? Indique cuál.", "tipo": "area"},
                ],
            },
        ],
    },
    "danos_obra_publica": {
        "titulo": "Formulario ampliado — Daños por Obra Pública",
        "secciones": [
            {
                "titulo": "1. Identificación de la consulta y del cliente",
                "campos": [
                    {"id": "nombre_completo", "etiqueta": "Nombre completo", "tipo": "texto", "requerido": True},
                    {"id": "documento_identidad", "etiqueta": "Documento de identidad", "tipo": "texto"},
                    {"id": "correo", "etiqueta": "Correo electrónico", "tipo": "texto"},
                    {"id": "ciudad_departamento", "etiqueta": "Ciudad y departamento", "tipo": "texto"},
                    {"id": "direccion", "etiqueta": "Dirección de residencia", "tipo": "texto"},
                ],
            },
            {
                "titulo": "2. Ubicación y obra que origina el daño",
                "campos": [
                    {"id": "predio_afectado", "etiqueta": "Dirección / vereda / predio afectado", "tipo": "texto"},
                    {"id": "municipio_obra", "etiqueta": "Municipio / departamento", "tipo": "texto"},
                    {"id": "nombre_obra", "etiqueta": "Nombre de la obra, concesión, contratista o proyecto si lo conoce", "tipo": "texto"},
                    {"id": "responsables_conocidos", "etiqueta": "Entidad pública, concesionario, contratista, interventoría u otros responsables conocidos", "tipo": "area"},
                    {"id": "fecha_inicio_afectaciones", "etiqueta": "Fecha aproximada en que comenzaron las afectaciones", "tipo": "texto"},
                ],
            },
            {
                "titulo": "3. Hechos y daños",
                "campos": [
                    {"id": "tipo_afectacion", "etiqueta": "Tipo de afectación", "tipo": "checkboxes",
                     "opciones": ["Desvío / acumulación de aguas", "Deslizamiento / movimiento de tierra", "Inundación",
                                  "Grietas / daño estructural", "Pérdida de cultivos", "Pérdida de acceso / servidumbre",
                                  "Daños a redes / servicios", "Pérdida de valor del inmueble", "Riesgo para habitantes", "Otro"]},
                    {"id": "relato_hechos_obra", "etiqueta": "Relate cronológicamente los hechos y cómo la obra se relaciona con los daños", "tipo": "area"},
                    {"id": "danos_materiales_economicos", "etiqueta": "Describa los daños materiales y económicos sufridos, y si ha habido que abandonar o restringir el uso del predio", "tipo": "area"},
                ],
            },
            {
                "titulo": "4. Avisos, peticiones y pruebas",
                "campos": [
                    {"id": "actuaciones_realizadas", "etiqueta": "Actuaciones realizadas", "tipo": "checkboxes",
                     "opciones": ["Petición a entidad", "Queja al contratista / concesión", "Alcaldía / gestión del riesgo",
                                  "Personería / Defensoría", "Inspección técnica", "Acción judicial", "Ninguna"]},
                    {"id": "fechas_radicados_respuesta", "etiqueta": "Indique fechas, radicados, entidades y respuesta recibida", "tipo": "area"},
                    {"id": "riesgos_actuales", "etiqueta": "Indique si existen riesgos actuales que requieran atención urgente", "tipo": "area"},
                    {"id": "pruebas_disponibles", "etiqueta": "Pruebas disponibles", "tipo": "checkboxes",
                     "opciones": ["Fotos / videos antes y después", "Informes técnicos", "Conceptos geológicos / ingeniería",
                                  "Escrituras / certificados", "Avalúos", "Facturas / reparaciones", "Peticiones y respuestas",
                                  "Testigos", "Registros de lluvias / emergencias", "Otros"]},
                    {"id": "valor_perjuicios", "etiqueta": "Valor aproximado de pérdidas, reparaciones, cultivos, ingresos dejados de percibir u otros perjuicios", "tipo": "area"},
                ],
            },
            {
                "titulo": "Información complementaria",
                "campos": [
                    {"id": "relato_adicional", "etiqueta": "Relato adicional o información que considere importante", "tipo": "area"},
                    {"id": "resultado_esperado", "etiqueta": "¿Qué resultado espera obtener o cuál es su principal objetivo?", "tipo": "area"},
                    {"id": "urgencia", "etiqueta": "¿Existe alguna fecha, audiencia, vencimiento o situación urgente? Indique cuál.", "tipo": "area"},
                ],
            },
        ],
    },
}


def _campo_html(campo: dict) -> str:
    cid = campo["id"]
    etiqueta = campo["etiqueta"]
    req = " required" if campo.get("requerido") else ""
    marca_req = " *" if campo.get("requerido") else ""
    tipo = campo["tipo"]

    if tipo == "area":
        control = f'<textarea id="{cid}" name="{cid}" rows="3"{req}></textarea>'
    elif tipo == "select":
        opciones_html = "".join(f'<option value="{o}">{o}</option>' for o in campo.get("opciones", []))
        control = f'<select id="{cid}" name="{cid}"{req}><option value="">Seleccione...</option>{opciones_html}</select>'
    elif tipo == "checkboxes":
        cajas = "".join(
            f'<label class="chk"><input type="checkbox" name="{cid}" value="{o}"> {o}</label>'
            for o in campo.get("opciones", [])
        )
        return f'<div class="campo"><span class="etiqueta">{etiqueta}</span><div class="chk-grupo">{cajas}</div></div>'
    else:  # "texto"
        control = f'<input type="text" id="{cid}" name="{cid}"{req}>'

    return f'<div class="campo"><label for="{cid}">{etiqueta}{marca_req}</label>{control}</div>'


def generar_html_formulario(slug: str, contacto: str = "", canal: str = "") -> str:
    """Devuelve la página HTML completa del formulario, o None si el slug no existe."""
    form = FORMULARIOS.get(slug)
    if not form:
        return None

    secciones_html = ""
    for seccion in form["secciones"]:
        campos_html = "".join(_campo_html(c) for c in seccion["campos"])
        secciones_html += f'<fieldset><legend>{seccion["titulo"]}</legend>{campos_html}</fieldset>'

    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{form['titulo']} — {NOMBRE_DESPACHO}</title>
<style>
  :root {{ --azul: #0b3c5d; --azul-claro: #0b66a3; --fondo: #eef2f7; }}
  * {{ box-sizing: border-box; }}
  body {{ font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; background: var(--fondo);
          margin: 0; padding: 0 0 40px 0; color: #222; }}
  header {{ background: var(--azul); color: white; padding: 18px 16px; }}
  header h1 {{ margin: 0; font-size: 1.15rem; }}
  header p {{ margin: 4px 0 0 0; font-size: 0.85rem; color: #cfe3f5; }}
  main {{ max-width: 640px; margin: 0 auto; padding: 16px; }}
  .aviso {{ background: #fff8e1; border: 1px solid #f0d896; border-radius: 8px; padding: 10px 14px;
            font-size: 0.85rem; margin-bottom: 16px; }}
  fieldset {{ background: white; border: none; border-radius: 10px; padding: 14px 16px; margin-bottom: 14px;
              box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  legend {{ font-weight: 600; color: var(--azul); padding: 0 4px; font-size: 0.95rem; }}
  .campo {{ margin-bottom: 12px; }}
  label, .etiqueta {{ display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 4px; color: #333; }}
  input[type=text], textarea, select {{ width: 100%; padding: 9px 10px; border: 1px solid #ccd6e0;
      border-radius: 6px; font-size: 0.95rem; font-family: inherit; }}
  textarea {{ resize: vertical; }}
  .chk-grupo {{ display: flex; flex-wrap: wrap; gap: 6px 16px; }}
  .chk {{ display: flex; align-items: center; gap: 6px; font-weight: 400; font-size: 0.9rem; }}
  .chk input {{ width: auto; }}
  .archivos {{ background: white; border-radius: 10px; padding: 14px 16px; margin-bottom: 14px;
               box-shadow: 0 1px 3px rgba(0,0,0,0.08); }}
  .archivos input {{ width: 100%; }}
  .autorizacion {{ display: flex; gap: 8px; align-items: flex-start; font-size: 0.85rem; margin-bottom: 16px; }}
  button {{ background: var(--azul-claro); color: white; border: none; border-radius: 8px; padding: 13px 20px;
            font-size: 1rem; font-weight: 600; width: 100%; cursor: pointer; }}
  button:active {{ background: var(--azul); }}
</style>
</head>
<body>
<header>
  <h1>{NOMBRE_DESPACHO}</h1>
  <p>{form['titulo']} — información para el estudio inicial de su caso</p>
</header>
<main>
  <div class="aviso">
    Complete lo que sepa o le aplique; si algo no aplica o no lo sabe, déjelo en blanco o escriba
    "No aplica". Este formulario es confidencial y su diligenciamiento no constituye aceptación del
    caso ni concepto jurídico definitivo.
  </div>
  <form method="post" action="/formulario/{slug}/enviar?contacto={contacto}&canal={canal}" enctype="multipart/form-data">
    {secciones_html}
    <div class="archivos">
      <label for="anexos">Documentos de soporte que quiera adjuntar (opcional): cédula, recibos, certificados, fotos, etc.</label>
      <input type="file" id="anexos" name="anexos" multiple>
    </div>
    <label class="autorizacion">
      <input type="checkbox" name="autorizacion_datos" value="Sí" required style="width:auto; margin-top:3px;">
      <span>Autorizo el tratamiento de mis datos para estudiar y gestionar esta consulta.</span>
    </label>
    <button type="submit">Enviar formulario</button>
  </form>
</main>
</body>
</html>"""


def generar_html_gracias(slug: str) -> str:
    form = FORMULARIOS.get(slug, {})
    titulo = form.get("titulo", "Formulario")
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Formulario enviado — {NOMBRE_DESPACHO}</title>
<style>
  body {{ font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; background: #eef2f7;
          margin: 0; display: flex; align-items: center; justify-content: center; min-height: 100vh; }}
  .tarjeta {{ background: white; border-radius: 12px; padding: 32px 24px; max-width: 440px; text-align: center;
              box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
  h1 {{ color: #0b3c5d; font-size: 1.2rem; }}
  p {{ color: #444; font-size: 0.95rem; line-height: 1.5; }}
  .check {{ font-size: 2.5rem; }}
</style>
</head>
<body>
  <div class="tarjeta">
    <div class="check">✅</div>
    <h1>¡Formulario recibido!</h1>
    <p>Gracias por diligenciar el <strong>{titulo}</strong>. Ya le llegó al abogado junto con los
    documentos que adjuntó. Puede volver al chat de WhatsApp para seguir la conversación.</p>
  </div>
</body>
</html>"""
