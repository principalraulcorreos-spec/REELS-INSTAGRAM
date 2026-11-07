"""Sintetiza los efectos de sonido del formato de reels en assets/sonidos/ (WAV 48 kHz).

Uso: python scripts/generar_sonidos.py
Si tienes los efectos originales (Epic Hit, Braams, etc.), ponlos en assets/sonidos/
con el mismo nombre de archivo y el render usará esos.
"""
import os
import numpy as np
import soundfile as sf

SR = 48000
OUT = os.path.join(os.path.dirname(__file__), "..", "assets", "sonidos")
rng = np.random.default_rng(7)


def t(d):
    return np.arange(int(SR * d)) / SR


def env_exp(n, tau):
    return np.exp(-np.arange(n) / (SR * tau))


def lowpass(x, fc):
    # one-pole low-pass, fc may be an array
    fc = np.broadcast_to(fc, x.shape)
    a = np.exp(-2 * np.pi * fc / SR)
    y = np.zeros_like(x)
    acc = 0.0
    for i in range(len(x)):
        acc = (1 - a[i]) * x[i] + a[i] * acc
        y[i] = acc
    return y


def norm(x, peak=0.89):
    m = np.max(np.abs(x)) or 1
    return x / m * peak


def fade(x, fi=0.003, fo=0.02):
    n = len(x)
    a, b = int(SR * fi), int(SR * fo)
    if a:
        x[:a] *= np.linspace(0, 1, a)
    if b:
        x[-b:] *= np.linspace(1, 0, b)
    return x


def stereo(x, width=0.0):
    if width:
        d = int(SR * 0.012)
        r = np.concatenate([np.zeros(d), x[:-d]])
        return np.stack([x, x * (1 - width) + r * width], 1)
    return np.stack([x, x], 1)


def save(name, x, width=0.0):
    x = fade(norm(x))
    sf.write(os.path.join(OUT, name), stereo(x, width), SR, subtype="PCM_16")
    print("ok", name, f"{len(x)/SR:.2f}s")


def sub_boom(d=2.0, f0=55, f1=32, tau=0.6):
    tt = t(d)
    f = f1 + (f0 - f1) * np.exp(-tt / 0.15)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * env_exp(len(tt), tau)


def noise_burst(d, tau, fc):
    n = rng.standard_normal(int(SR * d))
    return lowpass(n, fc) * env_exp(len(n), tau)


def main():
    os.makedirs(OUT, exist_ok=True)

    # order-filled: dos "ding" cortos tipo notificación de orden
    tt = t(0.35)
    a = np.sin(2 * np.pi * 1318 * tt) * env_exp(len(tt), 0.07)
    b = np.sin(2 * np.pi * 1760 * tt) * env_exp(len(tt), 0.09)
    x = np.zeros(int(SR * 0.45))
    x[: len(a)] += a
    x[int(SR * 0.08): int(SR * 0.08) + len(b)] += b
    save("order_filled.wav", x)

    # epic_hit: boom grave + golpe de ruido + acorde metálico
    d = 3.0
    x = sub_boom(d, 70, 30, 0.9) * 1.0
    x[: int(SR * 0.6)] += noise_burst(0.6, 0.12, 2500) * 0.9
    tt = t(d)
    for f in (110, 165, 220, 330):
        x += np.sin(2 * np.pi * f * tt) * env_exp(len(tt), 0.8) * 0.18
    save("epic_hit.wav", np.tanh(x * 1.6), 0.4)

    # whoosh: ruido con filtro que barre arriba y abajo
    d = 0.7
    tt = t(d)
    e = np.sin(np.pi * tt / d) ** 2
    fc = 300 + 5000 * np.sin(np.pi * tt / d) ** 3
    x = lowpass(rng.standard_normal(len(tt)), fc) * e
    save("whoosh.wav", x, 0.6)

    # riser: ruido + tono que sube 3 s
    d = 3.0
    tt = t(d)
    f = 200 * (2 ** (tt / d * 3))
    tone = np.sin(2 * np.pi * np.cumsum(f) / SR) * 0.35
    nz = lowpass(rng.standard_normal(len(tt)), 400 + 7000 * (tt / d) ** 2) * 0.8
    x = (tone + nz) * (tt / d) ** 2
    save("riser.wav", x, 0.5)

    # melodic_hit: acorde mayor brillante con campana
    d = 2.5
    tt = t(d)
    x = np.zeros_like(tt)
    for f, g in ((523.25, 1), (659.25, .8), (783.99, .7), (1046.5, .5)):
        x += g * (np.sin(2 * np.pi * f * tt) + 0.3 * np.sin(2 * np.pi * 2 * f * tt)) * env_exp(len(tt), 0.7)
    x += sub_boom(d, 90, 50, 0.3) * 0.8
    save("melodic_hit.wav", x, 0.5)

    # reverse_tension: golpe metálico invertido (crece y corta)
    d = 2.0
    tt = t(d)
    x = np.zeros_like(tt)
    for f in (146.8, 207.6, 293.7, 415.3):
        x += np.sin(2 * np.pi * f * tt + rng.uniform(0, 6)) * env_exp(len(tt), 0.5)
    x += noise_burst(d, 0.4, 3000) * 0.5
    save("reverse_tension.wav", x[::-1].copy(), 0.4)

    # reloj: tic-tac 4 s
    d = 4.0
    x = np.zeros(int(SR * d))
    for i in range(8):
        s = int(SR * i * 0.5)
        f = 3200 if i % 2 == 0 else 2400
        c = np.sin(2 * np.pi * f * t(0.03)) * env_exp(int(SR * 0.03), 0.004)
        c += noise_burst(0.03, 0.003, 6000) * 0.5
        x[s: s + len(c)] += c
    save("reloj.wav", x)

    # bomb_timer: bips que se aceleran 3 s
    d = 3.0
    x = np.zeros(int(SR * d))
    pos, gap = 0.0, 0.45
    while pos < d - 0.1:
        s = int(SR * pos)
        b = np.sin(2 * np.pi * 2000 * t(0.07)) * np.hanning(int(SR * 0.07))
        x[s: s + len(b)] += b[: len(x) - s]
        pos += gap
        gap = max(0.07, gap * 0.82)
    save("bomb_timer.wav", x)

    # braams: metal grave distorsionado
    d = 3.5
    tt = t(d)
    x = np.zeros_like(tt)
    for f in (41.2, 82.4, 123.5, 164.8):
        saw = 2 * ((f * tt) % 1) - 1
        x += saw * (0.5 if f > 50 else 1.0)
    x = lowpass(x, 300 + 1200 * env_exp(len(tt), 0.5)) * env_exp(len(tt), 1.2)
    x[: int(SR * 0.05)] *= np.linspace(0, 1, int(SR * 0.05))
    save("braams.wav", np.tanh(x * 3), 0.5)

    # bass_drop: caída de 120 a 30 Hz
    d = 2.5
    tt = t(d)
    f = 30 + 90 * np.exp(-tt / 0.5)
    x = np.sin(2 * np.pi * np.cumsum(f) / SR) * env_exp(len(tt), 1.0)
    save("bass_drop.wav", np.tanh(x * 2))

    # deep_hit: golpe grave seco
    x = sub_boom(1.8, 60, 35, 0.45)
    x[: int(SR * 0.2)] += noise_burst(0.2, 0.03, 1500) * 0.6
    save("deep_hit.wav", np.tanh(x * 1.5))

    # creepy_drone: drone oscuro 30 s (loopeable)
    d = 30.0
    tt = t(d)
    x = np.zeros_like(tt)
    for f, g in ((55, 1), (55.4, .8), (82.4, .4), (116.5, .25)):
        x += g * np.sin(2 * np.pi * f * tt + 0.3 * np.sin(2 * np.pi * 0.07 * tt))
    nz = rng.standard_normal(len(tt))
    x += lowpass(nz, 250) * 0.6
    x *= 0.8 + 0.2 * np.sin(2 * np.pi * 0.11 * tt)
    save("creepy_drone.wav", x, 0.7)


if __name__ == "__main__":
    main()
