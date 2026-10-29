# Motion Studio 3.0 — Android + HyperFrames 🎬

Crea videos animados con escenas relacionadas con tu guion desde un Android con GitHub Actions, **sin computadora, Codex ni claves de IA**.

## Motores disponibles

| Motor | Tecnología | Funciones |
|---|---|---|
| **HyperFrames** (nuevo) | [HyperFrames CLI](https://github.com/heygen-com/hyperframes), GSAP, Chromium y FFmpeg | Cuatro escenas (hook, solución, resultados, CTA), transiciones, entrada/salida de texto, formas y maquetas web, storyboard PNG |
| **Clásico** (conservado) | Python, Pillow y FFmpeg | Textos animados y formas geométricas |

HyperFrames se usa **de verdad**: ejecutamos el binario oficial de npm para interpretar una composición HTML creada por Motion Studio y renderizarla a MP4. **No** significa que los presets oficiales o todas las skills del repositorio original ya estén instaladas. Tampoco genera automáticamente escenas a partir de un prompt libre de IA.

El trabajo usa el CLI HyperFrames v0.8.216 y GSAP 3.14.2 (versiones fijadas en el workflow para evitar cambios inesperados).

### Guion con visuales literales (3.1)

En el formulario web hay un campo **Guion / narración** (máximo 480 caracteres). Se divide por frases y crea una escena por cada segmento, con duración aproximada repartida automáticamente; las imágenes corresponden a las palabras de cada frase.

**Ejemplo:** `Claude es similar a ChatGPT. Codex ayuda a programar. GitHub Actions renderiza el video.`

- Primera escena: logos de Claude y ChatGPT enfrentados, etiqueta «SIMILAR».
- Segunda escena: logo y tarjeta de Codex.
- Tercera escena: logo y tarjeta de GitHub.
- Para temas conocidos sin marcas (web, voz, programación, video, ventas, investigación), se representa un concepto visual concreto y no solamente un fondo abstracto.
- Los logos SVG provienen de **simple-icons@16.36.0** y **@lobehub/icons-static-svg@1.101.0**, copiados localmente antes de renderizar para evitar dependencias de CDN. Para ChatGPT se usa el símbolo de OpenAI; para Codex se usa el icono específico de Codex. Si falta un logo, se muestra una tarjeta con siglas. Las marcas pertenecen a sus titulares.
- El motor produce también una entrada `scene_plan` en `metadata.json` y una captura PNG por escena.

**Limitación:** el campo «Guion» todavía **no genera una voz narrada ni sincroniza audio de voz palabra por palabra**. Es sincronización *aproximada por frase* con tiempos repartidos. Para una sincronización real se necesitarán grabación o TTS, marcas temporales y alineación con el audio.

### Características

- Formatos vertical 9:16 (540×960), horizontal 16:9 (960×540) y cuadrado 1:1 (720×720).
- Duraciones configurables entre 6 y 20 segundos; 24 fps.
- Textos, color de marca, estilo y CTA editables.
- Cuatro escenas, cuatro imágenes de storyboard PNG y MP4.
- Efectos de sonido originales sintetizados localmente (desactivables).
- Renderizado en GitHub Actions y descarga vía Artifacts. No se usan servidores de pago por separado, pero GitHub Actions tiene cuotas y límites de ejecución.

## Método 1: GitHub Actions

1. Abre **[Render Motion Studio 3.0](https://github.com/aldo200908-lgtm/Motion-Studio/actions/workflows/render.yml)**.
2. Pulsa **Run workflow**.
3. Selecciona **hyperframes** como motor, escribe los textos y elige estilo, formato, duración, color y sonido.
4. Ejecuta y descarga **motion-studio-mp4** en **Artifacts** de la ejecución.

Si eliges **classic**, se usa el renderizador antiguo.

## Método 2: Interfaz web en Android

1. Activa GitHub Pages desde **Settings → Pages → Deploy from a branch → main → /docs → Save**.
2. Entra a **https://aldo200908-lgtm.github.io/Motion-Studio/** cuando Pages esté publicado.
3. Selecciona **HyperFrames**, llena los campos y pulsa **Preparar video en GitHub**.
4. GitHub abrirá un formulario de Issue prellenado: pulsa **Submit new issue** para autorizar el render.
5. Al finalizar, GitHub comentará en ese Issue con enlace a la ejecución y a sus Artifacts.

**Aviso de privacidad:** los datos de un Issue son visibles públicamente cuando el repositorio es público. No escribas información privada, tokens ni contraseñas. Solamente los Issues creados por la cuenta propietaria **aldo200908-lgtm** con título iniciado por **[Motion Studio]** pueden activar el render.

## Archivos principales

- [docs/index.html](docs/index.html): editor móvil estático (sin claves privadas).
- [scripts/hyperframes_build.py](scripts/hyperframes_build.py): validación de parámetros, creación de HTML+GSAP y efectos de audio.
- [scripts/literal_scenes.py](scripts/literal_scenes.py): detección de marcas, logos locales y comparaciones visuales por frase.
- [.github/workflows/render.yml](.github/workflows/render.yml): ejecución real de HyperFrames CLI, FFmpeg y extracción de storyboards.
- [scripts/motion_v2.py](scripts/motion_v2.py): motor clásico conservado intacto.

El HTML se compone por código propio, no se acepta HTML o JavaScript arbitrario a través del formulario. El renderizador usa Node 22+ y FFmpeg; no necesita ejecutar modelos de IA.

## Licencias y alcance

- HyperFrames: [Apache-2.0](https://github.com/heygen-com/hyperframes/blob/main/LICENSE).
- GSAP: bajo sus términos de licencia; se usa como dependencia npm.
- Referencia visual de la versión clásica: [Barty-Bart/motion-graphics](https://github.com/Barty-Bart/motion-graphics), MIT.

HyperFrames puede renderizar proyectos mucho más complejos con HTML/JS, media y skills para agentes. **Esta integración no incluye aún generación por IA, scraping de webs, narración TTS ni todos los templates oficiales.** Estos necesitarían pipelines adicionales y comprobaciones de compatibilidad, presupuesto y permisos de recursos.
