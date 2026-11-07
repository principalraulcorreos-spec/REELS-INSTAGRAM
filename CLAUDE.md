# REELS-INSTAGRAM — edición de reels de trading en la nube

Todo el render se hace en la nube, no en la PC de Raúl.

## Estructura
- `docs/` — formatos y notas: `reels-narracion-trade.md` (formato actual, sin cara), `reels-reacciones.md` (formato con cara + biblioteca de clips), `publicaciones-estado.md` (qué se publicó dónde).
- `assets/sonidos/` — efectos (order-filled, Epic Hit, Whoosh, Riser, Melodic Hit, Reverse Tension, reloj, bomb timer, Braams, Bass Drop, Deep Hit, Creepy Drone…).
- `assets/reacciones/` — video de reacciones de Raúl.
- `scripts/` — pipeline (OCR de la tabla de MT5, voz Kokoro, render con ffmpeg).
- `grabaciones/` y `salida/` — NO se suben a git (ver `.gitignore`). Las grabaciones de OBS pesan 1–1.6 GB; GitHub rechaza archivos >100 MB.

## Flujo
1. Conseguir la grabación de OBS (stagear desde la PC, partida en trozos <400 MB si hace falta) y ponerla en `grabaciones/`.
2. OCR de la tabla de MT5 → entradas, salidas, SL/TP, P/L flotante (patrimonio − balance). Hora server = local + 9 h.
3. Guion de voz → Kokoro em_alex vel. 1.2 → subtítulos palabra por palabra.
4. Render 720x1280, 30 s, ~-14 LUFS, a `salida/Reel_AAAA-MM-DD_NAS100.mp4`.
5. Actualizar `docs/` con los datos del reel y el estado de publicación.

## Dependencias
`pip install kokoro-onnx rembg onnxruntime opencv-python-headless pytesseract numpy` + `apt install ffmpeg tesseract-ocr`.
Modelos (no van en git): kokoro-v1.0.onnx y voices-v1.0.bin (releases de kokoro-onnx en GitHub), u2net_human_seg.onnx en ~/.u2net.
