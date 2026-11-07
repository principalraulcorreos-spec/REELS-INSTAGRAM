# REELS-INSTAGRAM — edición de reels de trading en la nube

Todo el render se hace en la nube, no en la PC de Raúl.

## Estructura
- `docs/` — `plan-reel.md` (cómo armar y renderizar un reel, LEER PRIMERO), `reels-narracion-trade.md` (formato actual, sin cara), `reels-reacciones.md` (formato con cara + biblioteca de clips), `publicaciones-estado.md` (qué se publicó dónde).
- `scripts/setup.sh` — instala dependencias y descarga modelos de Kokoro.
- `scripts/ocr_mt5.py` — OCR de la tabla de MT5 → CSV con balance, patrimonio y P/L.
- `scripts/voz.py` — voz Kokoro em_alex vel. 1.2 con tiempos por palabra.
- `scripts/render_reel.py` — render del reel desde `planes/*.json`.
- `scripts/generar_sonidos.py` — efectos sintetizados; `scripts/unir_partes.py` — une grabaciones partidas.
- `planes/` — un JSON por reel (`2026-10-28.json` es el ejemplo completo).
- `assets/sonidos/`, `assets/fuentes/` (Anton, Montserrat), `assets/reacciones/` (video de reacciones, pendiente).
- `grabaciones/` y `salida/` — NO van a git (pesan 1–1.6 GB; GitHub rechaza >100 MB).

## Flujo
1. `bash scripts/setup.sh`
2. Poner la grabación de OBS en `grabaciones/` (stagear desde la PC; partida en <400 MB si hace falta).
3. OCR → entradas, salidas, SL/TP, P/L (patrimonio − balance). Hora server MT5 = local + 9 h.
4. Escribir `planes/AAAA-MM-DD.json` y `python scripts/render_reel.py planes/AAAA-MM-DD.json`.
5. Revisar frames y loudness (~-14 LUFS), entregar `salida/Reel_AAAA-MM-DD_NAS100.mp4`.
6. Actualizar `docs/` con los datos del reel y el estado de publicación; commit del plan.
