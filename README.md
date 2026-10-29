# Motion Studio 2.0 🎬

Generador **offline y determinista** de motion graphics (MP4) que se ejecuta en **GitHub Actions**. Puedes controlarlo desde Android: no requiere computadora, Codex ni API de pago.

## Qué incluye esta versión

- 3 estilos: **High Energy** (títulos cinéticos + geometría), **Engaging** (nodos y recorrido visual), **Clean** (tarjetas editoriales).
- 3 formatos: **vertical 9:16**, **horizontal 16:9** y **cuadrado 1:1**.
- Duración de 6 a 20 segundos, 24 FPS; títulos, texto de apoyo, CTA y color personalizables.
- Efectos de sonido sintetizados originales, opción de video silencioso.
- MP4 H.264 + AAC, metadatos y créditos en los artefactos de GitHub Actions.
- Editor estático móvil en [docs/index.html](docs/index.html). Crea solicitudes mediante GitHub Issues **sin exponer tokens**.

## Opción 1 — GitHub Actions, sin configurar Pages

1. Ve a **Actions → Render Motion Studio 2.0 → Run workflow**.
2. Escribe título, subtítulo y CTA. Selecciona estilo, formato, color, duración y sonido.
3. Ejecuta el workflow. Cuando termine, abre su ejecución.
4. Descarga **motion-studio-mp4** en la sección **Artifacts**; contiene video.mp4 y metadatos.

Enlace directo: https://github.com/aldo200908-lgtm/Motion-Studio/actions/workflows/render.yml

## Opción 2 — Interfaz web desde tu celular

1. En GitHub abre **Settings → Pages**.
2. En **Build and deployment** selecciona **Deploy from a branch**, elige **main** y la carpeta **/docs**, luego guarda.
3. Después de que Pages esté activo, abre **https://aldo200908-lgtm.github.io/Motion-Studio/**.
4. Completa el formulario y toca **Preparar video en GitHub**.
5. GitHub abrirá un formulario de issue prellenado. **Debes tocar Submit new issue**.
6. La solicitud del propietario activa GitHub Actions; cuando termine, se publica un comentario en el issue con enlace a la ejecución.
7. Abre la ejecución y descarga el archivo **motion-studio-mp4**.

**Privacidad:** los títulos y demás parámetros se escriben en el cuerpo de un issue. Si el repositorio es público, esos datos serán públicos. No escribas datos secretos ni información privada. Solo los issues creados por **aldo200908-lgtm** cuyo título empiece con **[Motion Studio]** pueden activar el trabajo de renderizado.

## Qué es, y qué NO es

Las seis skills de [Barty-Bart/motion-graphics](https://github.com/Barty-Bart/motion-graphics) son flujos de trabajo para **agentes de IA** (incluyen herramientas y guías); no constituyen por sí solas un servicio automático que convierta cualquier prompt en MP4 sin agente.

Esta implementación **adapta las direcciones visuales** de explainer-high-energy, explainer-engaging y explainer-default (aquí llamado Clean). Los efectos de sonido son **originales y sintéticos**: no son la librería CC0 ni el análisis de mezcla de la skill original sound-effects. Los módulos motion-broll y object-separation **no están integrados**; necesitan video de entrada y flujos más pesados. No se están ejecutando las seis skills originales.

Por tanto, **no convierte una descripción arbitraria en imágenes o personajes generados con IA**: produce motion graphics de textos y formas definidos por el usuario.

## Organización

- .github/workflows/render.yml — workflow manual, automático de prueba e issues del propietario.
- scripts/motion_v2.py — renderizado determinista con Pillow + FFmpeg.
- scripts/render.py — renderizador de la versión 1 (conservado).
- docs/index.html — formulario web estático para celulares.

## Tecnología

Python 3.11, Pillow y FFmpeg en runners ubuntu-latest. No hay secretos ni claves de terceros. Los efectos de sonido son sintetizados por código propio.

**Licencias:** inspiraciones visuales basadas en el repositorio Barty-Bart/motion-graphics (MIT). Este proyecto no redistribuye sus fuentes ni su biblioteca de efectos de sonido.

## Solución de problemas

Si no aparece el botón **Run workflow**, comprueba que GitHub Actions esté habilitado y que el workflow esté en la rama principal. Para los issues automáticos, GitHub Issues debe estar habilitado. Si la página web aún no carga, activa GitHub Pages con la carpeta **/docs** tal como se indicó anteriormente.
