"""Voz Kokoro (em_alex, vel. 1.2) con tiempos por palabra para los subtítulos.

Uso suelto: python scripts/voz.py "Llegué a ir más 57 dólares" salida/prueba.wav
"""
import os
import re
import sys
import json
import numpy as np
import soundfile as sf

MODELOS = os.environ.get("KOKORO_DIR", os.path.expanduser("~/models"))
VOZ = os.environ.get("KOKORO_VOZ", "em_alex")
VEL = float(os.environ.get("KOKORO_VEL", "1.2"))
SR_OUT = 48000

_kokoro = None


def _modelo():
    global _kokoro
    if _kokoro is None:
        from kokoro_onnx import Kokoro
        _kokoro = Kokoro(os.path.join(MODELOS, "kokoro-v1.0.onnx"),
                         os.path.join(MODELOS, "voices-v1.0.bin"))
    return _kokoro


def _a_texto_hablado(texto):
    """Convierte cifras de dinero a algo que Kokoro lea bien."""
    def dinero(m):
        signo = {"+": "más ", "-": "menos ", "−": "menos "}.get(m.group(1) or "", "")
        num = m.group(2).replace(",", "")
        entero, _, dec = num.partition(".")
        s = f"{signo}{int(entero)} dólares"
        if dec and int(dec):
            s += f" con {int(dec)}"
        return s
    t = re.sub(r"([+\-−])?\$\s?([\d,]+(?:\.\d+)?)", dinero, texto)
    return t


def _recortar_silencio(x, umbral=0.01):
    idx = np.where(np.abs(x) > umbral)[0]
    if len(idx) == 0:
        return x, 0
    a = max(0, idx[0] - 240)
    b = min(len(x), idx[-1] + 2400)
    return x[a:b], a


def sintetizar(texto):
    """Devuelve (audio float32 mono a 48 kHz, [ {palabra, ini, fin} ] en segundos)."""
    k = _modelo()
    muestras, sr = k.create(_a_texto_hablado(texto), voice=VOZ, speed=VEL, lang="es")
    muestras = np.asarray(muestras, dtype=np.float32)
    muestras, _ = _recortar_silencio(muestras)
    # re-muestrear a 48 kHz
    n = int(len(muestras) * SR_OUT / sr)
    audio = np.interp(np.linspace(0, len(muestras) - 1, n), np.arange(len(muestras)), muestras).astype(np.float32)
    dur = len(audio) / SR_OUT

    palabras = texto.split()
    pesos = np.array([len(re.sub(r"[^\wáéíóúñü ]", "", _a_texto_hablado(p), flags=re.I)) + 1.5
                      for p in palabras], float)
    # pausas tras signos de puntuación
    pesos += np.array([2.5 if re.search(r"[.,;:!?…]$", p) else 0 for p in palabras])
    cum = np.concatenate([[0], np.cumsum(pesos)]) / pesos.sum() * dur
    tiempos = [{"palabra": p, "ini": float(cum[i]), "fin": float(cum[i + 1])} for i, p in enumerate(palabras)]
    return audio, tiempos


if __name__ == "__main__":
    a, ts = sintetizar(sys.argv[1])
    sf.write(sys.argv[2], a, SR_OUT)
    print(json.dumps(ts, ensure_ascii=False, indent=1))
