# Leonida Al Día

Canal de YouTube sobre GTA 6 listo para el lanzamiento (19 de noviembre de 2026):
diez vídeos con guion, voz, gráficos animados, subtítulos, música y montaje, más
miniaturas, metadatos y la marca del canal.

## Qué hay

- `output/NN-slug/` — por cada vídeo: `video.mp4` (1920×1080), `miniatura.jpg`, `metadata.md` (título, descripción con capítulos, etiquetas) y `guion.md`.
- `canal/` — nombre, descripción, banner, avatar y orden de publicación.
- `investigacion.md` — qué temas se eligieron, por qué, fuentes y datos a revisar.
- `content/videos.json` — la fuente de todo: guiones y lo que aparece en pantalla.
- `pipeline/` — el generador.

## Cómo se hace cada vídeo

1. `pipeline/tts.py` — narración con [Piper](https://github.com/OHF-Voice/piper1-gpl) (voz `es_ES-davefx-medium`) y tiempos de cada frase.
2. `pipeline/music.py` — base musical sintetizada desde cero (sin samples).
3. `pipeline/render.js` — `template.html` se anima fotograma a fotograma con Playwright y ffmpeg lo codifica y mezcla con voz y música.
4. `pipeline/meta.py` y `pipeline/brand.js` — metadatos y marca.

Para cambiar un guion, edita `content/videos.json` y ejecuta `./build.sh`.
La pronunciación de anglicismos se ajusta en la tabla `SAY` de `pipeline/tts.py`.

## Derechos

Todos los gráficos y la música son originales; no se usa metraje, logotipos ni arte de
Rockstar Games. Es un canal de fans sin afiliación con Rockstar Games ni Take-Two Interactive.
