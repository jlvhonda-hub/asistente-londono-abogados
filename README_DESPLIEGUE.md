# Asistente de WhatsApp Business + Facebook Messenger

Este es un servicio web pequeño (independiente del programa de escritorio) que:

- Recibe los mensajes que le escriben al WhatsApp Business del despacho (317 821 5004)
  y a la página de Facebook.
- Saluda y muestra un único menú con los temas específicos que maneja el despacho
  (Alimentos, Custodia y Visitas, Divorcio, Unión Marital de Hecho, Patria Potestad,
  Sucesión, Trámite Notarial/Registral, Accidente de Tránsito/SOAT, Pertenencia,
  División de Bienes, Daños por Obra Pública, u Otra consulta) — el cliente elige
  directamente el tema de su caso en un solo paso, sin categorías intermedias.
- Hace 2-3 preguntas cortas de triage (nombre, qué pasó, si hay urgencia).
- Con esas respuestas, genera con IA una **impresión preliminar de viabilidad** (nunca
  un concepto jurídico definitivo — siempre remite a la consulta con el abogado).
- Le envía automáticamente el **formulario PDF ampliado** correspondiente al tema
  específico (carpeta `formularios/`), para que el cliente lo diligencie con calma y
  lo devuelva por el mismo chat junto con sus documentos de soporte. En los temas
  con más volumen de información y documentos (Sucesión, Trámite Notarial/Registral,
  Accidente de Tránsito/SOAT, Pertenencia, División de Bienes, Daños por Obra
  Pública) además le envía un **segundo formulario complementario de anexos**, para
  relacionar ordenadamente los documentos de soporte.
- **Recibe archivos del cliente**: si el cliente envía por el chat una foto, PDF,
  audio u otro archivo (por ejemplo el formulario diligenciado, una cédula, una
  escritura, fotos del accidente), el asistente lo descarga automáticamente y se lo
  reenvía por correo al abogado como adjunto, y le confirma al cliente que quedó
  recibido — no hace falta que el abogado esté revisando el chat en el momento.
- Ofrece agendar una **consulta pagada** y, si el cliente acepta, le envía el enlace de
  pago de Wompi.
- Le envía un correo a **javerlon.abogados@gmail.com** con cada contacto nuevo, y otro
  con el resumen completo del caso (todas las respuestas + el tema elegido + el/los
  formulario(s) que se le enviaron + la viabilidad generada + si aceptó o no la
  consulta), para que nada se pierda.

### Flujo de conversación

```
Saludo → elegir el tema específico del caso (menú plano, un solo paso)
   → 2-3 preguntas cortas de triage → impresión de viabilidad (IA)
   → envío automático del formulario PDF ampliado del tema
     (+ formulario de anexos, en los temas con más volumen de documentos)
   → "¿Desea agendar consulta pagada?" → Sí: enlace de pago Wompi
                                        → No: cierre cordial
(en cualquier momento de la conversación, si el cliente envía un archivo, se
reenvía por correo al abogado automáticamente; y después del flujo, sigue la
conversación libre con el asistente de IA)
```

**Nota:** el menú de temas se envía como texto numerado (no como el menú
interactivo nativo de WhatsApp), porque WhatsApp solo permite hasta 10 opciones en
ese tipo de menú y aquí hay más de 10 temas — con texto numerado no hay ese límite
y funciona igual en WhatsApp y en Messenger.

El texto de las preguntas y el "saludo" se puede editar libremente en `flujo.py`
(diccionarios `PREGUNTAS_TRIAGE`/`PREGUNTAS_OTRO` y variable `SALUDO`); la lista de
temas y qué PDF corresponde a cada uno se edita en el diccionario `AREAS_MENU` del
mismo archivo — no requiere tocar el resto del código. Los formularios PDF en sí
están en la carpeta `formularios/` y se pueden reemplazar por versiones actualizadas
sin tocar código, siempre que se mantenga el mismo nombre de archivo (o se
actualice el nombre en `AREAS_MENU`).

**¿Por qué un servicio aparte y no dentro del programa de escritorio?** Porque Meta
exige que el webhook esté en un servidor con dirección web pública (https) encendido
las 24 horas — algo que un programa de escritorio en su computador no puede ofrecer
(si apaga el computador, WhatsApp dejaría de poder entregarle mensajes).

## Costos (para una oficina de bajo flujo)

- **Responder a un cliente que escribe primero es gratuito** dentro de una ventana de
  24 horas desde su mensaje (así funciona la tarifa vigente de Meta desde julio de
  2025: solo cobra el envío de plantillas fuera de esa ventana, algo que este
  asistente no hace). Para un despacho que solo contesta a quien lo contacta, el uso
  normal no debería generar costo en WhatsApp.
- El hosting recomendado (Render, plan gratuito) no pide tarjeta de crédito. Su única
  limitación: el servicio "se duerme" tras 15 minutos sin mensajes y tarda ~1 minuto
  en responder el primer mensaje después de dormirse. Para un despacho de bajo flujo
  esto es aceptable (el cliente recibe la respuesta con un pequeño retraso la primera
  vez, luego responde normal). Si en el futuro esto molesta, se puede pasar a un plan
  pago económico (desde ~5 USD/mes) para que nunca se duerma.
- OpenAI cobra por uso de la IA (unos pocos centavos de dólar por cada 100
  conversaciones aproximadamente, usando el modelo económico configurado por
  defecto). Puede ver su consumo en https://platform.openai.com/usage

## Paso 1 — Crear la app de Meta y conectar el número de WhatsApp

1. Vaya a https://developers.facebook.com/ e inicie sesión con la cuenta de Facebook
   asociada al negocio.
2. "Mis apps" → "Crear app" → tipo **Negocio (Business)**.
3. Dentro de la app, agregue el producto **WhatsApp**.
4. Meta le asigna automáticamente un número de prueba gratuito para hacer pruebas
   (puede enviar mensajes a hasta 5 números verificados). Anote:
   - **Temporary access token** (válido 24h, luego genera uno permanente — ver abajo)
   - **Phone number ID**
5. Para usar su número real (317 821 5004) en vez del número de prueba: en
   "WhatsApp" → "Configuración de API" → agregue su número y verifíquelo por SMS o
   llamada. Meta puede pedirle verificar el negocio (Meta Business Verification,
   gratuito) antes de habilitarlo para producción sin límites.
6. Para un token permanente (que no expire en 24h): cree un **System User** en
   Meta Business Suite → Configuración del negocio → Usuarios del sistema, asígnele
   permisos sobre la app de WhatsApp, y genere un token desde ahí con duración
   "Nunca expira".

## Paso 2 — Subir este código a GitHub (sin necesidad de usar git)

No hace falta instalar nada ni usar comandos — se puede hacer arrastrando archivos
desde el navegador:

1. Cree una cuenta gratuita en https://github.com si no tiene una (con su correo
   javerlon.abogados@gmail.com, por ejemplo).
2. "+" (arriba a la derecha) → **"New repository"**.
   - **Repository name**: `asistente-londono-abogados`
   - Márquelo **Private** (privado)
   - No marque "Add a README" (para que quede vacío)
   - "Create repository"
3. En la página del repositorio recién creado, busque el enlace **"uploading an
   existing file"** (aparece en el mensaje de bienvenida del repo vacío).
4. Arrastre ahí **todos los archivos y carpetas que están dentro de `asistente_meta/`**
   (app.py, flujo.py, asistente_ia.py, memoria.py, notificaciones.py, requirements.txt,
   Procfile, render.yaml, .env.example, README_DESPLIEGUE.md, .gitignore, y **la carpeta
   `formularios/` completa con los 12 PDF** — sin esta carpeta el asistente no podrá
   enviarle el formulario al cliente) — **menos el archivo `.env`** si llegó a crear uno
   para pruebas locales (ese nunca se sube).
5. Abajo, "Commit changes" (puede dejar el mensaje que propone GitHub por defecto).

Con eso el repositorio ya está listo para conectarlo a Render en el siguiente paso.

*(Si en algún momento prefiere usar git desde una terminal, también funciona igual:
`git init`, `git remote add origin <URL-del-repo>`, `git add .`, `git commit -m "inicial"`,
`git push -u origin main` — pero no es necesario.)*

## Paso 3 — Desplegar gratis en Render

1. Cree una cuenta gratuita en https://render.com (no pide tarjeta de crédito).
2. "New +" → "Web Service" → conecte su repositorio de GitHub.
3. Configure:
   - **Root Directory**: déjelo en blanco (si subió los archivos directo a la raíz del
     repositorio, como en el Paso 2). Si en cambio subió toda la carpeta `asistente_meta`
     dentro del repo, escriba aquí `asistente_meta`.
   - **Build Command**: `pip install -r requirements.txt`
   - **Start Command**: `uvicorn app:app --host 0.0.0.0 --port $PORT`
   - **Plan**: Free
4. En la pestaña **Environment**, agregue todas las variables del archivo
   `.env.example` con sus valores reales (OPENAI_API_KEY, WHATSAPP_TOKEN,
   WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_VERIFY_TOKEN — invente usted mismo este
   último, cualquier texto largo sirve —, IMAP_USER, IMAP_PASS, etc.)
5. Despliegue. Render le dará una URL pública parecida a:
   `https://asistente-londono-abogados.onrender.com`

   (Alternativa: si prefiere no hacerlo manualmente, Render puede leer el archivo
   `render.yaml` incluido y crear el servicio automáticamente con "New +" → "Blueprint".)

## Paso 4 — Conectar el webhook en Meta

1. En el panel de Meta, dentro del producto WhatsApp → "Configuración" → "Webhook".
2. **Callback URL**: `https://SU-URL-DE-RENDER.onrender.com/webhook`
3. **Verify Token**: el mismo valor exacto que puso en `WHATSAPP_VERIFY_TOKEN`.
4. Haga clic en "Verificar y guardar" (Meta llamará una vez a su servidor para
   confirmar que el token coincide).
5. Suscríbase al campo **messages**.

## Paso 5 — (Opcional) Conectar también Facebook Messenger

1. En la misma app de Meta, agregue el producto **Messenger**.
2. Vincule la página de Facebook del despacho y genere un **Page Access Token**;
   péguelo en la variable `FACEBOOK_PAGE_TOKEN` en Render.
3. En "Messenger" → "Webhooks", use la misma URL (`.../webhook`) y el mismo
   Verify Token, y suscríbase al campo **messages**.

## Paso 5.5 — Enlace de pago de Wompi (consulta pagada)

Como ya tiene cuenta en Wompi, solo necesita crear **un enlace de pago reutilizable**
(no requiere programar nada ni usar la API de Wompi):

1. Entre a https://comercios.wompi.co (panel de comercio) → **Links de pago**.
2. Cree un link nuevo:
   - **Nombre**: "Consulta jurídica" (o el que prefiera)
   - **Monto**: el valor fijo de la consulta (por ejemplo $80.000 COP) — o déjelo libre
     si quiere que el cliente digite el monto
   - **Tipo de uso**: "Reutilizable" (para que sirva para todos los clientes, no solo uno)
3. Wompi le entrega una URL parecida a: `https://checkout.wompi.co/l/AbC123`
4. Copie esa URL en la variable `WOMPI_LINK_CONSULTA` en Render, y ajuste
   `PRECIO_CONSULTA` para que el texto que ve el cliente coincida con el monto real
   configurado en Wompi.

**Nota:** el asistente solo *envía* este enlace cuando el cliente acepta la consulta;
la confirmación del pago la sigue viendo usted directamente en su panel de Wompi (por
correo o en el dashboard), igual que hoy. Si más adelante quiere que el sistema
detecte automáticamente cuándo se pagó (y por ejemplo agende la cita solo), se puede
agregar la integración con la API de Wompi y su webhook de confirmación — es un paso
más avanzado que vale la pena solo si el volumen de consultas crece.

## Paso 6 — Probar

1. Desde un celular distinto, escriba un WhatsApp al 317 821 5004 (o al número de
   prueba, mientras esté en modo prueba).
2. Debe recibir el saludo y el menú de áreas en unos segundos (o hasta ~1 minuto si
   el servicio estaba dormido por inactividad).
3. Elija el tema de su caso escribiendo el número (por ejemplo "9" para Pertenencia),
   y responda las 2-3 preguntas cortas de triage.
4. Al terminar, debe recibir la impresión de viabilidad, luego el **formulario PDF
   ampliado** como documento adjunto, y por último la pregunta sobre agendar consulta
   pagada; si acepta, debe llegar el enlace de Wompi.
5. Revise que lleguen los dos correos a javerlon.abogados@gmail.com: el de "nuevo
   contacto" (al primer mensaje) y el de "resumen del caso" (al terminar el formulario).
6. Envíe también una foto o un PDF por el mismo chat (por ejemplo el formulario ya
   diligenciado) y verifique que le llegue por correo como adjunto, y que el
   asistente le confirme al cliente que lo recibió.
7. Puede ver los registros en vivo en Render: pestaña "Logs" del servicio.

## Notas y límites a tener en cuenta

- El archivo `contactos.csv` que genera el servicio es solo un respaldo temporal en
  el propio servidor; en el plan gratuito **se puede perder** si el servicio se
  redespliega. El correo de notificación es la copia confiable — revise su bandeja
  de entrada regularmente, o en el futuro se puede conectar a Google Sheets u otra
  base de datos gratuita si el volumen de mensajes crece.
- Los archivos que envían los clientes (fotos, PDF, audios) **no se guardan** en el
  servidor: se descargan en el momento y se reenvían de inmediato por correo como
  adjunto — el correo es la única copia que queda, así que también conviene
  guardarlos o organizarlos desde el correo. Si un archivo pesa más de 20 MB (el
  límite típico de Gmail para adjuntos), el asistente le avisa al cliente que no
  pudo reenviarlo automáticamente; ese límite se puede ajustar con la variable
  `TAMANO_MAXIMO_ADJUNTO_MB` en Render si hiciera falta.
- El asistente de IA da información general y recolecta datos de contacto; nunca
  sustituye el criterio del abogado. Esto ya está indicado en sus instrucciones
  (`asistente_ia.py`), pero puede ajustar el texto del `SYSTEM_PROMPT` en ese
  archivo en cualquier momento para cambiar el tono o las reglas del asistente.
- Si en algún momento el flujo de mensajes crece y el "sueño" del plan gratuito de
  Render empieza a generar respuestas demasiado lentas, la solución más simple es
  pasar a un plan pago económico (Render Starter, o alternativas como Railway) —
  no requiere cambiar nada del código.

---

**Fuentes consultadas para esta guía (septiembre de 2026):**
- [Pricing on the WhatsApp Business Platform (Meta, oficial)](https://developers.facebook.com/documentation/business-messaging/whatsapp/pricing)
- [Platforms with a real free tier for developers in 2026 (Render)](https://render.com/articles/platforms-with-a-real-free-tier-for-developers-in-2026)
- [Links de pago (Wompi, documentación oficial)](https://docs.wompi.co/en/docs/colombia/links-de-pago/)
