# Reels con reacciones — biblioteca y formato

## Video de reacciones
`C:\Users\Raúl\Pictures\Camera Roll\WIN_20261012_07_41_31_Pro.mp4` (79 s, 1920x1080; en la práctica ~15 fps reales). En el repo va en `assets/reacciones/reacciones.mp4`.

| Clip | Segundos | Uso |
|---|---|---|
| Manos en la cara | 0.4–2.4 | Hook / pérdida (a partir de ~1.9 s solo se ven manos: usar 0.4–1.8) |
| Suplicando "por favor" | 2.5–3.9 | Cerca del stop |
| Cara entre las manos, cabeza abajo | 4.0–6.9 | Stop tocado (la cara casi no se ve: mejor usar "Manos a la cabeza" para el stop) |
| Puños arriba, corto | 7.0–8.3 | Va a favor |
| Manos a la cabeza / frustración | 8.8–10.8 | Sigue en contra / stop (8.3–8.7 sale borroso y la segmentación falla) |
| Serio, tenso mirando pantalla | 11.0–15.5 | Esperando / entrada |
| Festejo fuerte con puños + risa | 15.8–18.5 | Pico de ganancia / TP |
| Riendo y señalando | 18.5–23.5 | Ganancia |
| Se acerca a la pantalla con lentes | 32.7–37 | Tensión / 2da entrada (recorte centrado en x≈1100, y≈650, lado ~780; 32.0–32.6 mira hacia abajo) |
| Baile de celebración | 44–56 | TP grande (pantalla completa) |
| Sentado serio | 60–78 | Tensión neutra (recorte centrado y≈560) |

Recorte de cara: la ventana del cuarto se cuela en la segmentación. Lo que funcionó (15-oct): quitar del alfa los píxeles blancos (V>215 y S<50), apertura morfológica + quedarse con el componente más grande, y reemplazar frames donde la máscara falla (área < 60 % de la mediana) por el vecino bueno. Recortes cuadrados usados el 19-oct (centro x,y / lado, en 1920x1080): manos en la cara 1000,520/860; por favor 960,540/900; puños 960,560/900; manos a la cabeza 960,500/860; serio 960,560/820; festejo+riendo (15.8–21) 1000,580/1000; lentes 1100,650/780; sentado 960,560/820.

## Formato del reel (30 s, 720x1280) — versión desde el 14-oct-2026
- Desde el 14-oct las grabaciones de OBS vienen verticales 720x1280 (el 28-oct volvieron a 1280x720 horizontal). 15-oct: gráfica de MT5 y≈60–390, tabla y≈403–465; zoom x 480–720, y 130–390 → 720x780. 19-oct: gráfica M5 y≈60–515, tabla y≈535–600 (OCR con recorte y 525–625), TradingView abajo; zoom x 300–720, y 100–497 → 720x680.
- **Layout:** arriba la cara (recortada, sin fondo, cuadro centrado ~415 px con borde verde/naranja/rojo); abajo zoom a la operación abierta de MT5 y en la unión una caja "P/L abierto  ±$X" (verde/roja).
- **Narración tipo historia de Reddit:** voz Kokoro em_alex (velocidad 1.2) contando una minihistoria que NO es de trading, con subtítulos grandes de 2–3 palabras (palabra activa en amarillo) en el centro. Ducking de efectos cuando habla la voz.
- **Tipo de historia:** gancho de misterio en la primera frase, la duda abierta hasta el final, y la revelación amarrada al desenlace del trade. Nada de historias absurdas sin misterio.
- Sincronizar palabras clave de la historia con los momentos del trade (pico, 2ª entrada, stop).
- Que no se vea el cuarto: solo la cara (segmentación rembg u2net_human_seg).
- Hook 1.8 s: "LLEGUÉ A IR $X… ¿CÓMO TERMINÓ?" (X = máximo/mínimo flotante verificado) + cara.
- Barra superior con datos reales (compras/ventas, SL) + indicador de velocidad (>> x12). Rótulo "ORDEN EJECUTADA" en cada entrada.
- Cierre: pantalla "STOP TOCADO"/resultado con la cara, y outro oscuro con frase + RaulFx.
- Sonidos: order-filled en cada entrada/salida (bajo); Epic Hit en el hook; Whoosh en cada cambio de escena; Riser antes del pico + Melodic Hit en ganancia; Reverse Tension cuando se voltea; Ring Slice / Dynamic SFX en los chistes, Massive Impact + Hollywood Hit en golpes/revelaciones, Writing FX como cinta; reloj durante la espera; bomb timer antes del stop; Braams + Bass Drop en el stop; Deep Hit en el resultado; Creepy Drone de fondo. Loudness -14 LUFS.
- Momentos de entrada/salida y P&L por OCR de la tabla de MT5 (patrimonio − balance; aceptar solo lecturas donde coincida con el total de la columna Beneficio). Hora del servidor MT5 = hora local + 9 h.
- Las grabaciones a veces tienen tramos en negro de ~3 s (OBS): saltarlos.
- La cuenta de las grabaciones es Pepperstone **Demo**.
- Grabaciones de más de 400 MB: partirlas con `ffmpeg -c copy -f segment -segment_time 420` y unirlas en la nube con ffconcat (usar `inpoint` para el traslape).
- Kokoro: `pip install kokoro-onnx` + modelos de GitHub (kokoro-v1.0.onnx, voices-v1.0.bin). rembg con u2net_human_seg.onnx en ~/.u2net. OCR: OMP_THREAD_LIMIT=1 y 2 procesos (1,669 frames ≈ 25 min).

## Historial de reels con reacciones
| Archivo | Sesión | Hook | Resultado / historia |
|---|---|---|---|
| Reel_2026-10-12_NAS100_1 | 07-30-56 | +$857.49 | +$309.06 |
| Reel_2026-10-12_NAS100_2 | 07-36-10 | +$99.96 | -$299.46 |
| Reel_2026-10-12_NAS100_3 | 07-40-51 | -$162.98 | +$30.69 |
| Reel_2026-10-12_NAS100_4 | 07-54-37 | -$765.20 | +$998.08 |
| Reel_2026-10-13_NAS100 | 07-31-49 | +$296.36 | -$1,146.28 |
| Reel_2026-10-14_NAS100 | 07-29-59 | +$104.94 | -$865.71 · "la caja de la abuela" |
| Reel_2026-10-15_NAS100 | 07-30-10 | +$816.00 | -$1,015.20 · "la segunda puerta" |
| Reel_2026-10-19_NAS100 | 08-52-25 | -$297.92 | +$1,279.04 TP · "la banca" · outro "El que aguanta su plan, cobra." |
