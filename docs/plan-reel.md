# Plan del reel (JSON) — referencia

Un reel = un archivo en `planes/AAAA-MM-DD.json`. Se renderiza con:

```
python scripts/render_reel.py planes/AAAA-MM-DD.json
```

Tiempos: cualquier elemento acepta `t_src` (segundo de la grabación) o `t` (segundo del reel, 0–30).
El reel: 0–3 s hook · 3 s → fin de tramos: el trade · fin de tramos → 30 s: tarjeta de resultado.

| Campo | Qué es |
|---|---|
| `grabacion` | mp4 de OBS (en `grabaciones/`, no va a git) |
| `salida` | mp4 final (en `salida/`) |
| `grafica` | recorte de la gráfica de MT5 en la grabación `{x,y,w,h}` |
| `hook` | `{t_src, monto}`: frame congelado y el "LLEGUÉ A IR ±$X" |
| `tramos` | lista `{src:[a,b], dur}`; velocidad = (b−a)/dur. La suma de `dur` debe dar ~24.7 s (3 → 27.7). Lento en momentos clave, x50+ en tramos muertos |
| `eventos` | `{t_src, tipo, rotulo?, vol?, sin_rotulo?}`. Tipos: `entrada`, `add`, `tp_movido`, `sl_movido`, `pico`, `volteo`, `espera`, `stop`, `tp`, `cierre`. Cada tipo trae su rótulo y sus sonidos (ver `SFX_EVENTO` en render_reel.py) |
| `barra` | estados de la barra superior `{t_src, titulo, lineas[], naranja[]}` (máx. 3 líneas en total) |
| `pl` | puntos `[t_src, valor]` (se interpola) |
| `pl_csv` | CSV de `ocr_mt5.py`; usa solo filas `valido=1`. Se puede combinar con `pl` |
| `pl_trade_desde` + `balance_inicial` | desde ese t_src la caja dice "P/L DEL TRADE" y (con CSV) el valor es patrimonio − balance inicial |
| `narracion` | `{t o t_src, texto, dice?}`. `dice` = lo que pronuncia la voz si es distinto del subtítulo. Si dos líneas se enciman, la segunda se recorre |
| `resultado` | `{monto, lineas[], balance:[antes, después], frase}` |
| `sonidos_extra` | `{t o t_src, nombre, vol}` con cualquier archivo de `assets/sonidos/` |
| `vol_drone`, `duracion_hook`, `duracion_total` | opcionales (0.22 / 3 / 30) |

## Pasos con una grabación nueva
1. Stagear la grabación desde la PC (si pesa >400 MB, partirla allá con `ffmpeg -c copy -f segment -segment_time 420` y unir aquí con `scripts/unir_partes.py`).
2. Sacar un frame (`ffmpeg -ss 600 -i X -frames:v 1 f.png`) para ubicar la gráfica y la tabla.
3. OCR de la tabla: `python scripts/ocr_mt5.py X --tabla x,y,w,h --invertir --desde A --hasta B -o grabaciones/X_ocr.csv`.
4. Con el CSV ubicar entradas, pico, stop/TP y escribir el plan (copiar `planes/2026-10-28.json`).
5. Render, revisar frames y audio, ajustar tramos/narración.
6. Anotar el reel en `docs/` y en el estado de publicación.

## Sonidos
`assets/sonidos/` trae efectos sintetizados (`scripts/generar_sonidos.py`). Para usar los originales, ponerlos con el mismo nombre (`epic_hit.mp3`, `braams.wav`, …); el render busca `.wav`, `.mp3`, `.ogg`, `.m4a`.
