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

NOMBRE_DESPACHO = "Javier Londoño V. Abogados & Asociados"

# Tipos de campo soportados: "texto", "area" (texto largo), "select",
# "checkboxes" (multi-selección), "fecha".
FORMULARIOS = {
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
