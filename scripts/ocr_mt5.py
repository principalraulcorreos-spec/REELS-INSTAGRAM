"""OCR de la tabla de operaciones de MT5 en una grabación de OBS.

Saca, cada N segundos, balance, patrimonio y la columna Beneficio, y calcula
P/L flotante = patrimonio − balance. Una lectura es "valida" solo si ese P/L
coincide (±1 USD) con la suma de la columna Beneficio.

Uso:
  python scripts/ocr_mt5.py grabaciones/2026-10-28.mp4 --tabla 0,560,1280,130 \
      --cada 1 --desde 590 --hasta 920 --invertir -o grabaciones/2026-10-28_ocr.csv

--tabla x,y,ancho,alto  (en píxeles de la grabación; ver docs/ para cada layout)
"""
import os
os.environ.setdefault("OMP_THREAD_LIMIT", "1")

import re
import csv
import sys
import argparse
import subprocess
from multiprocessing import Pool

import cv2
import numpy as np
import pytesseract

NUM = r"-?\d{1,3}(?:[  ]\d{3})*(?:\.\d{2})"


def a_float(s):
    return float(s.replace(" ", "").replace(" ", ""))


def duracion(video):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration",
                          "-of", "csv=p=0", video], capture_output=True, text=True).stdout
    return float(out.strip())


def leer_frame(video, t, caja):
    cap = cv2.VideoCapture(video)
    cap.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
    ok, fr = cap.read()
    cap.release()
    if not ok:
        return None
    x, y, w, h = caja
    return fr[y:y + h, x:x + w]


def procesar(args):
    video, t, caja, invertir, escala = args
    img = leer_frame(video, t, caja)
    if img is None:
        return {"t": t, "estado": "sin_frame"}
    if img.mean() < 8:
        return {"t": t, "estado": "negro"}
    g = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    g = cv2.resize(g, None, fx=escala, fy=escala, interpolation=cv2.INTER_CUBIC)
    if invertir:
        g = 255 - g
    g = cv2.threshold(g, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    texto = pytesseract.image_to_string(g, config="--psm 6")
    return analizar(t, texto)


def analizar(t, texto):
    r = {"t": round(t, 3), "estado": "ok", "texto": " | ".join(l for l in texto.splitlines() if l.strip())}
    bal = re.search(r"Balance[:\s]+(" + NUM + ")", texto, re.I)
    eq = re.search(r"(?:Patrimonio|Equity)[:\s]+(" + NUM + ")", texto, re.I)
    beneficios, posiciones = [], 0
    for linea in texto.splitlines():
        if re.search(r"Balance|Patrimonio|Equity", linea, re.I):
            continue
        if re.search(r"\b(buy|sell|compra|venta)\b", linea, re.I):
            nums = re.findall(NUM, linea)
            if nums:
                beneficios.append(a_float(nums[-1]))
                posiciones += 1
    r["balance"] = a_float(bal.group(1)) if bal else ""
    r["patrimonio"] = a_float(eq.group(1)) if eq else ""
    r["posiciones"] = posiciones
    r["suma_beneficio"] = round(sum(beneficios), 2) if beneficios else ""
    if bal and eq:
        r["pl"] = round(r["patrimonio"] - r["balance"], 2)
        r["valido"] = int(beneficios != [] and abs(r["pl"] - r["suma_beneficio"]) <= 1.0
                          or (posiciones == 0 and abs(r["pl"]) < 0.01))
    else:
        r["pl"], r["valido"] = "", 0
    return r


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--tabla", required=True, help="x,y,ancho,alto")
    ap.add_argument("--cada", type=float, default=1.0, help="segundos entre lecturas")
    ap.add_argument("--desde", type=float, default=0)
    ap.add_argument("--hasta", type=float, default=None)
    ap.add_argument("--invertir", action="store_true", help="tema oscuro de MT5")
    ap.add_argument("--escala", type=float, default=3)
    ap.add_argument("--procesos", type=int, default=os.cpu_count() or 2)
    ap.add_argument("-o", "--salida", required=True)
    a = ap.parse_args()

    caja = tuple(int(v) for v in a.tabla.split(","))
    hasta = a.hasta or duracion(a.video)
    ts = np.arange(a.desde, hasta, a.cada)
    trabajos = [(a.video, float(t), caja, a.invertir, a.escala) for t in ts]
    campos = ["t", "estado", "balance", "patrimonio", "pl", "suma_beneficio", "posiciones", "valido", "texto"]
    with Pool(a.procesos) as p, open(a.salida, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=campos, extrasaction="ignore")
        w.writeheader()
        for i, r in enumerate(p.imap(procesar, trabajos, chunksize=4)):
            w.writerow(r)
            if i % 50 == 0:
                print(f"{i}/{len(trabajos)} t={r['t']} pl={r.get('pl')} valido={r.get('valido')}", file=sys.stderr)
    print("listo:", a.salida)


if __name__ == "__main__":
    main()
