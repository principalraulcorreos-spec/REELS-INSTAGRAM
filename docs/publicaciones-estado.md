# Estado de publicación de reels (actualizado 26-oct-2026)

| Reel | IG @mraullrl | Threads | TikTok (raultpl) | YouTube Shorts | FB Raúl Martinez Fitness |
|---|---|---|---|---|---|
| 09-24 MNQ (−$1,009.50) | ✅ | ✅* | ✅ | ✅ | ✅ |
| 09-28 XAUUSD (−$854.71) | ✅ | ✅* | ✅ | ✅ | ✅ |
| 09-29 (+$1,116.86) | ✅ | ✅ | ✅ | ✅ | ✅ |
| 09-30 (+$833.51) | ✅ | ✅ | ✅ | ✅ | ✅ |
| 09-30_2 (−$324 → +$751.38) | ✅ | ✅ | ✅ | ✅ | ✅ |
| 10-01 (−$1,772.87) | ✅ | ✅ | ✅ | ✅ | ✅ |
| 10-02 (+$1,394.75) | ✅ | ✅ | ✅ | ✅ | ✅ |
| 10-05 (+$687.04) | ✅ | ✅ | ✅ | ✅ | ✅ |
| 10-06 (−$1,921.50) | ✅ | ✅ | ✅ | ✅ | ✅ |
| 10-08 (+$1,259 → −$1,001) | ✅ | ✅ | ✅ | ✅ | ✅ |
| 10-09 (−$868.51, casi 30 lotes) | ✅ | ✅ | ✅ | ❌ | ✅ |
| 10-12 _1 a _4 | ✅ | ✅ | ✅ | ❌ | ✅ |
| 10-13 (−$1,146.28) | ✅ | ✅ | ✅ | ❌ | ✅ |
| 10-14 abuela (−$865.71) | ✅ | ✅ | ✅ | ❌ | ✅ |
| 10-15 segunda puerta (−$1,015.20) | ✅ (duplicado: 2 veces) | ✅ | ✅ | ✅ | ✅ |
| 10-19 banca (+$1,279.04) | ✅ | ✅ | ✅ | ❌ | ✅ |
| 10-23 (−$1,501.50 → +$1,085.70) | ✅ | ✅ | ✅ | ❌ | ✅ |
| 10-26 (+$150.25 TP) | ✅ | ✅ | ✅ | ❌ | ✅ |

\* En Threads hay 2 videos sin texto del 29-sep; se asumieron como MNQ y XAUUSD.

Pendiente YouTube: límite diario de cargas alcanzado tras 10 subidas (pide verificación por teléfono o esperar 24 h). Faltan 10-09, 10-12 x4, 10-13, 10-14, 10-19, 10-23, 10-26.
Reels del 16-oct y 20-oct no existen en la PC (no se publicaron en ningún lado).

## Notas de publicación
- TikTok: cuenta raultpl. Flujo que funciona: tiktokstudio/upload → file input → JS focus en [contenteditable] + execCommand('selectAll') → Delete → type → clic JS en "Publicar" → esperar "Vídeo publicado" → navigate force:true a /upload.
- YouTube Studio: /videos/upload?d=ud abre el diálogo. Título y descripción: JS focus en #title-textarea #textbox / #description-textarea #textbox + selectAll + type. Radio VIDEO_MADE_FOR_KIDS_NOT_MFK, #next-button x3, radio PUBLIC, #done-button. Límite diario ~10-12 videos sin verificar.
- Facebook página Raúl Martinez Fitness: facebook.com/reels/create/ → file input "Subir un vídeo para un reel" → Siguiente x2 → descripción → Publicar → esperar ~20 s antes de navegar.
- Instagram: el botón Crear se abre por JS con svg[aria-label="Nueva publicación"]; recorte Original; Siguiente x2; Compartir.
