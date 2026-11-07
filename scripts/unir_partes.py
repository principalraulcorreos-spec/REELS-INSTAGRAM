"""Une las partes de una grabación (cortadas en la PC con ffmpeg -c copy) en un solo mp4.

Uso: python scripts/unir_partes.py grabaciones/salida.mp4 parte_00.mp4 parte_01.mp4 ...
Las partes deben ir en orden. Si se cortaron con traslape, pasa --inpoint con los
segundos a saltar al inicio de cada parte (después de la primera), separados por coma.
"""
import os
import sys
import argparse
import subprocess
import tempfile

ap = argparse.ArgumentParser()
ap.add_argument("salida")
ap.add_argument("partes", nargs="+")
ap.add_argument("--inpoint", default="", help="ej. 0,1.2,0.8 (uno por parte después de la primera)")
a = ap.parse_args()

inp = [float(x) for x in a.inpoint.split(",")] if a.inpoint else []
with tempfile.NamedTemporaryFile("w", suffix=".ffconcat", delete=False) as f:
    f.write("ffconcat version 1.0\n")
    for i, p in enumerate(a.partes):
        f.write(f"file '{os.path.abspath(p)}'\n")
        if i > 0 and i - 1 < len(inp) and inp[i - 1] > 0:
            f.write(f"inpoint {inp[i - 1]}\n")
    lista = f.name
subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lista,
                "-c", "copy", a.salida], check=True)
os.unlink(lista)
print("listo:", a.salida)
