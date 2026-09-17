# -*- coding: utf-8 -*-
"""
panel_cierre.py
Páginas HTML del "cierre de negocio" (paso 3): una páginita interna, protegida
con una clave, donde el abogado —después de tener la consulta personal con el
cliente y decidir tomar el caso— escribe los datos del caso y con un clic pide
que la IA redacte, para ESE caso concreto, un borrador de:
  1) el contrato de prestación de servicios,
  2) el poder para gestión, y
  3) la lista de requerimientos y soportes que le faltan al cliente.

Los tres borradores aparecen ahí mismo, en cajas de texto que el abogado puede
leer y corregir antes de aprobar. Solo cuando el abogado aprueba (botón
"Aprobar y enviar al cliente") el sistema le manda al cliente, por el mismo
WhatsApp o Messenger de la conversación, un enlace donde puede ver esos
documentos ya definitivos (ver app.py: rutas /panel/cierre* y /cierre/{id}).

Cómo se usa (ver app.py):
  GET  /panel/cierre            -> formulario para escribir la clave
  POST /panel/cierre            -> si la clave es correcta, muestra el
                                    formulario con los datos del caso
  POST /panel/cierre/generar    -> llama a la IA y muestra los tres borradores
                                    para revisar/editar antes de enviar
  POST /panel/cierre/enviar     -> guarda la versión final, se la envía al
                                    cliente y muestra la confirmación
  GET  /cierre/{id}             -> página pública que ve el cliente
"""
import html

import asistente_ia
import flujo

NOMBRE_DESPACHO = asistente_ia.NOMBRE_DESPACHO

ESTILO_BASE = """
  :root { --azul: #0b3c5d; --azul-claro: #0b66a3; --fondo: #eef2f7; }
  * { box-sizing: border-box; }
  body { font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; background: var(--fondo);
         margin: 0; padding: 0 0 40px 0; color: #222; }
  header { background: var(--azul); color: white; padding: 18px 16px; }
  header h1 { margin: 0; font-size: 1.15rem; }
  header p { margin: 4px 0 0 0; font-size: 0.85rem; color: #cfe3f5; }
  main { max-width: 720px; margin: 0 auto; padding: 16px; }
  .aviso { background: #fff8e1; border: 1px solid #f0d896; border-radius: 8px; padding: 10px 14px;
           font-size: 0.85rem; margin-bottom: 16px; }
  .error { background: #fdecea; border: 1px solid #f3b0ab; color: #8a1c12; border-radius: 8px;
           padding: 10px 14px; font-size: 0.85rem; margin-bottom: 16px; }
  fieldset { background: white; border: none; border-radius: 10px; padding: 14px 16px; margin-bottom: 14px;
             box-shadow: 0 1px 3px rgba(0,0,0,0.08); }
  legend { font-weight: 600; color: var(--azul); padding: 0 4px; font-size: 0.95rem; }
  .campo { margin-bottom: 12px; }
  label, .etiqueta { display: block; font-size: 0.85rem; font-weight: 600; margin-bottom: 4px; color: #333; }
  input[type=text], input[type=password], textarea, select { width: 100%; padding: 9px 10px;
      border: 1px solid #ccd6e0; border-radius: 6px; font-size: 0.95rem; font-family: inherit; }
  textarea { resize: vertical; }
  textarea.documento { min-height: 260px; font-family: Georgia, "Times New Roman", serif; line-height: 1.5; }
  .ayuda { font-size: 0.78rem; color: #667; margin-top: 3px; }
  button { background: var(--azul-claro); color: white; border: none; border-radius: 8px; padding: 13px 20px;
           font-size: 1rem; font-weight: 600; width: 100%; cursor: pointer; }
  button:active { background: var(--azul); }
  .resumen { background: white; border-radius: 10px; padding: 14px 16px; margin-bottom: 14px;
             box-shadow: 0 1px 3px rgba(0,0,0,0.08); font-size: 0.9rem; }
  .resumen b { color: var(--azul); }
"""


def _esc(valor) -> str:
    return html.escape(valor or "", quote=True)


def _pagina(titulo: str, subtitulo: str, cuerpo_html: str) -> str:
    return f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{_esc(titulo)} — {NOMBRE_DESPACHO}</title>
<style>{ESTILO_BASE}</style>
</head>
<body>
<header>
  <h1>{NOMBRE_DESPACHO}</h1>
  <p>{_esc(subtitulo)}</p>
</header>
<main>
{cuerpo_html}
</main>
</body>
</html>"""


def generar_html_error(mensaje: str) -> str:
    cuerpo = f'<div class="error">{_esc(mensaje)}</div>'
    return _pagina("Cierre de negocio", "Error", cuerpo)


def generar_html_login(error: bool = False) -> str:
    aviso_error = '<div class="error">Clave incorrecta. Intente de nuevo.</div>' if error else ""
    cuerpo = f"""
  {aviso_error}
  <div class="aviso">Página de uso interno del despacho. Escriba la clave del panel para continuar.</div>
  <form method="post" action="/panel/cierre">
    <fieldset>
      <div class="campo">
        <label for="clave">Clave del panel</label>
        <input type="password" id="clave" name="clave" required autofocus>
      </div>
    </fieldset>
    <button type="submit">Entrar</button>
  </form>
"""
    return _pagina("Cierre de negocio", "Acceso interno", cuerpo)


def _opciones_area_html() -> str:
    return "".join(f'<option value="{_esc(op["titulo"])}">{_esc(op["titulo"])}</option>' for op in flujo.AREAS_MENU)


def generar_html_formulario_datos(clave: str) -> str:
    cuerpo = f"""
  <div class="aviso">
    Use esta página después de haber tenido la consulta personal con el cliente y de decidir que
    el despacho toma el caso. Escriba los datos y lo hablado en la consulta; en el siguiente paso
    la IA redactará, para este caso concreto, el borrador del contrato, el poder para gestión y la
    lista de requerimientos — usted los revisa y corrige antes de que se le envíen al cliente.
  </div>
  <form method="post" action="/panel/cierre/generar">
    <input type="hidden" name="clave" value="{_esc(clave)}">
    <fieldset>
      <legend>Cómo contactar al cliente</legend>
      <div class="campo">
        <label for="canal">Canal por el que escribió el cliente</label>
        <select id="canal" name="canal" required>
          <option value="WhatsApp">WhatsApp</option>
          <option value="Messenger">Messenger (Facebook)</option>
        </select>
      </div>
      <div class="campo">
        <label for="contacto">Número de WhatsApp (con indicativo, sin "+", ej: 573001234567) o ID de Messenger</label>
        <input type="text" id="contacto" name="contacto" required>
        <div class="ayuda">Si es por Messenger y no tiene el ID a la mano, lo encuentra en el correo de
          notificación que le llegó cuando el cliente escribió por primera vez.</div>
      </div>
    </fieldset>
    <fieldset>
      <legend>Datos del cliente y del caso</legend>
      <div class="campo">
        <label for="nombre_cliente">Nombre completo del cliente</label>
        <input type="text" id="nombre_cliente" name="nombre_cliente" required>
      </div>
      <div class="campo">
        <label for="documento_identidad">Documento de identidad (opcional)</label>
        <input type="text" id="documento_identidad" name="documento_identidad">
      </div>
      <div class="campo">
        <label for="ciudad">Ciudad (opcional)</label>
        <input type="text" id="ciudad" name="ciudad">
      </div>
      <div class="campo">
        <label for="area">Área / tema del caso</label>
        <select id="area" name="area" required>
          <option value="">Seleccione...</option>
          {_opciones_area_html()}
        </select>
      </div>
      <div class="campo">
        <label for="resumen_caso">Resumen de lo hablado en la consulta (hechos y lo acordado)</label>
        <textarea id="resumen_caso" name="resumen_caso" rows="5" required></textarea>
      </div>
      <div class="campo">
        <label for="honorarios">Honorarios y forma de pago acordados (opcional; si lo deja en blanco, el
          borrador queda con un espacio marcado para completarlo)</label>
        <input type="text" id="honorarios" name="honorarios">
      </div>
      <div class="campo">
        <label for="notas">Notas adicionales para tener en cuenta en los documentos (opcional)</label>
        <textarea id="notas" name="notas" rows="3"></textarea>
      </div>
    </fieldset>
    <button type="submit">Generar borradores con IA</button>
  </form>
"""
    return _pagina("Cierre de negocio", "Datos del caso", cuerpo)


def generar_html_revision(clave: str, datos: dict, documentos: dict) -> str:
    cuerpo = f"""
  <div class="aviso">
    Estos tres textos los redactó la IA a partir de lo que usted escribió; revíselos y corríjalos
    aquí mismo si hace falta. <b>Solo se le envían al cliente cuando usted haga clic en "Aprobar y
    enviar al cliente"</b> más abajo.
  </div>
  <div class="resumen">
    <b>Cliente:</b> {_esc(datos.get('nombre_cliente'))} &nbsp;·&nbsp;
    <b>Área:</b> {_esc(datos.get('area'))} &nbsp;·&nbsp;
    <b>Canal:</b> {_esc(datos.get('canal'))} &nbsp;·&nbsp;
    <b>Contacto:</b> {_esc(datos.get('contacto'))}
  </div>
  <form method="post" action="/panel/cierre/enviar">
    <input type="hidden" name="clave" value="{_esc(clave)}">
    <input type="hidden" name="canal" value="{_esc(datos.get('canal'))}">
    <input type="hidden" name="contacto" value="{_esc(datos.get('contacto'))}">
    <input type="hidden" name="nombre_cliente" value="{_esc(datos.get('nombre_cliente'))}">
    <input type="hidden" name="area" value="{_esc(datos.get('area'))}">
    <fieldset>
      <legend>Contrato de prestación de servicios (borrador)</legend>
      <textarea class="documento" name="contrato">{_esc(documentos.get('contrato'))}</textarea>
    </fieldset>
    <fieldset>
      <legend>Poder para gestión (borrador)</legend>
      <textarea class="documento" name="poder">{_esc(documentos.get('poder'))}</textarea>
    </fieldset>
    <fieldset>
      <legend>Requerimientos y soportes faltantes</legend>
      <textarea class="documento" name="requerimientos">{_esc(documentos.get('requerimientos'))}</textarea>
    </fieldset>
    <button type="submit">Aprobar y enviar al cliente</button>
  </form>
"""
    return _pagina("Cierre de negocio", "Revisar antes de enviar", cuerpo)


def generar_html_confirmacion(datos: dict, enlace: str) -> str:
    cuerpo = f"""
  <div class="resumen">
    <div class="check" style="font-size:2rem; text-align:center;">✅</div>
    <p style="text-align:center;">Se envió a <b>{_esc(datos.get('nombre_cliente'))}</b> por
    {_esc(datos.get('canal'))} un mensaje con el enlace a sus documentos.</p>
    <p style="text-align:center; word-break: break-all;"><a href="{_esc(enlace)}">{_esc(enlace)}</a></p>
    <p style="text-align:center;">También le llegó una copia de respaldo a su correo.</p>
  </div>
  <form method="get" action="/panel/cierre">
    <button type="submit">Hacer otro cierre</button>
  </form>
"""
    return _pagina("Cierre de negocio", "Enviado", cuerpo)


def generar_html_cliente(datos: dict) -> str:
    """Página pública (sin clave) que ve el cliente en /cierre/{id}."""
    cuerpo = f"""
  <div class="resumen">
    Hola {_esc(datos.get('nombre_cliente'))}, aquí encuentra los documentos de su caso
    ({_esc(datos.get('area'))}), preparados por el despacho después de su consulta.
    Si tiene alguna duda, comuníquese directamente con su abogado.
  </div>
  <fieldset>
    <legend>Contrato de prestación de servicios</legend>
    <pre style="white-space: pre-wrap; font-family: Georgia, 'Times New Roman', serif; line-height:1.5; margin:0;">{_esc(datos.get('contrato'))}</pre>
  </fieldset>
  <fieldset>
    <legend>Poder para gestión</legend>
    <pre style="white-space: pre-wrap; font-family: Georgia, 'Times New Roman', serif; line-height:1.5; margin:0;">{_esc(datos.get('poder'))}</pre>
  </fieldset>
  <fieldset>
    <legend>Requerimientos y documentos que hacen falta</legend>
    <pre style="white-space: pre-wrap; font-family: -apple-system, Segoe UI, Roboto, Arial, sans-serif; margin:0;">{_esc(datos.get('requerimientos'))}</pre>
  </fieldset>
"""
    return _pagina("Sus documentos", "Documentos de su caso", cuerpo)
