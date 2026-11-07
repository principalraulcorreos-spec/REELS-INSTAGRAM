"""Render del reel "narrando el trade" (30 s, 720x1280) a partir de un plan JSON.

Uso: python scripts/render_reel.py planes/2026-10-28.json
Formato del plan: docs/plan-reel.md. Ejemplo: planes/2026-10-28.json
"""
import os
import re
import sys
import csv
import json
import math
import shutil
import subprocess
import tempfile

import cv2
import numpy as np
import soundfile as sf
from PIL import Image, ImageDraw, ImageFont

sys.path.insert(0, os.path.dirname(__file__))
import voz  # noqa: E402

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
SON = os.path.join(RAIZ, "assets", "sonidos")
FUENTES = os.path.join(RAIZ, "assets", "fuentes")

W, H, FPS = 720, 1280, 30
SR = 48000
VERDE, ROJO, NARANJA, AMARILLO = (0, 214, 110), (255, 59, 59), (255, 149, 0), (255, 221, 0)
BLANCO, NEGRO, GRIS = (255, 255, 255), (0, 0, 0), (150, 150, 160)
FONDO = (10, 12, 18)

ROTULOS = {
    "entrada": ("ORDEN EJECUTADA", (40, 120, 255)),
    "add": ("ORDEN EJECUTADA", NARANJA),
    "tp_movido": ("TP MOVIDO", NARANJA),
    "sl_movido": ("SL MOVIDO", NARANJA),
    "stop": ("STOP TOCADO", ROJO),
    "tp": ("TP TOCADO", VERDE),
    "cierre": ("CIERRE MANUAL", (120, 120, 140)),
}
# sonidos automáticos por tipo de evento: (archivo, desfase_s, volumen)
SFX_EVENTO = {
    "entrada": [("order_filled", 0, .55)],
    "add": [("order_filled", 0, .55)],
    "tp_movido": [("whoosh", -0.2, .5)],
    "sl_movido": [("whoosh", -0.2, .5)],
    "pico": [("riser", -3.0, .45), ("melodic_hit", 0, .7)],
    "volteo": [("reverse_tension", -2.0, .6)],
    "espera": [("reloj", 0, .35)],
    "stop": [("bomb_timer", -3.0, .45), ("braams", 0, .8), ("bass_drop", 0, .7), ("order_filled", 0, .5)],
    "tp": [("order_filled", 0, .55), ("melodic_hit", 0, .8)],
    "cierre": [("order_filled", 0, .55)],
}


# ---------------------------------------------------------------- utilidades
def fuente(tam, tipo="anton"):
    if tipo == "anton":
        return ImageFont.truetype(os.path.join(FUENTES, "Anton-Regular.ttf"), tam)
    f = ImageFont.truetype(os.path.join(FUENTES, "Montserrat.ttf"), tam)
    try:
        f.set_variation_by_name("Bold" if tipo == "bold" else "SemiBold")
    except Exception:
        pass
    return f


def ruta(p):
    return p if os.path.isabs(p) else os.path.join(RAIZ, p)


def dinero(v, signo=True):
    s = f"${abs(v):,.2f}"
    if not signo:
        return s
    return ("+" if v >= 0 else "−") + s


def texto_centrado(d, cx, y, txt, f, color, stroke=0, scolor=NEGRO):
    w = d.textlength(txt, font=f)
    d.text((cx - w / 2, y), txt, font=f, fill=color, stroke_width=stroke, stroke_fill=scolor)


class Tiempo:
    """Convierte tiempo de la grabación (t_src) a tiempo del reel (t_out) y viceversa."""

    def __init__(self, tramos, t0):
        self.tramos = []
        t = t0
        for tr in tramos:
            a, b = tr["src"]
            self.tramos.append((a, b, t, t + tr["dur"]))
            t += tr["dur"]
        self.fin = t

    def a_out(self, ts):
        for a, b, o0, o1 in self.tramos:
            if a <= ts <= b:
                return o0 + (ts - a) / (b - a) * (o1 - o0)
        if ts < self.tramos[0][0]:
            return self.tramos[0][2]
        return self.fin

    def a_src(self, to):
        for a, b, o0, o1 in self.tramos:
            if o0 <= to <= o1:
                return a + (to - o0) / (o1 - o0) * (b - a)
        return self.tramos[-1][1] if to > self.fin else self.tramos[0][0]

    def velocidad(self, to):
        for a, b, o0, o1 in self.tramos:
            if o0 <= to < o1:
                return (b - a) / (o1 - o0)
        return 1.0


def t_de(item, tm):
    if "t" in item:
        return float(item["t"])
    return tm.a_out(float(item["t_src"]))


# ------------------------------------------------------------------- video
def preparar_grafica(plan, tm, tmp, ancho, alto):
    g = plan["grafica"]
    crop = f"crop={g['w']}:{g['h']}:{g['x']}:{g['y']},scale={ancho}:{alto}:flags=lanczos"
    partes = []
    for i, tr in enumerate(plan["tramos"]):
        a, b = tr["src"]
        vel = (b - a) / tr["dur"]
        out = os.path.join(tmp, f"tr{i:02d}.mp4")
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a), "-i", ruta(plan["grabacion"]),
                        "-t", str(b - a), "-an",
                        "-vf", f"{crop},setpts=(PTS-STARTPTS)/{vel},fps={FPS}",
                        "-t", str(tr["dur"]), "-c:v", "libx264", "-preset", "veryfast", "-crf", "16",
                        out], check=True)
        partes.append(out)
    lista = os.path.join(tmp, "lista.txt")
    with open(lista, "w") as f:
        for p in partes:
            f.write(f"file '{p}'\n")
    base = os.path.join(tmp, "grafica.mp4")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "concat", "-safe", "0", "-i", lista,
                    "-c", "copy", base], check=True)
    return base


def frame_en(plan, ts, ancho, alto):
    g = plan["grafica"]
    cap = cv2.VideoCapture(ruta(plan["grabacion"]))
    cap.set(cv2.CAP_PROP_POS_MSEC, ts * 1000)
    ok, fr = cap.read()
    cap.release()
    if not ok:
        return Image.new("RGB", (ancho, alto), FONDO)
    fr = fr[g["y"]:g["y"] + g["h"], g["x"]:g["x"] + g["w"]]
    fr = cv2.resize(fr, (ancho, alto), interpolation=cv2.INTER_LANCZOS4)
    return Image.fromarray(cv2.cvtColor(fr, cv2.COLOR_BGR2RGB))


# --------------------------------------------------------------------- P/L
def serie_pl(plan):
    if "pl_csv" in plan:
        pts = []
        base_ini = plan.get("balance_inicial")
        desde = plan.get("pl_trade_desde", 1e18)
        with open(ruta(plan["pl_csv"]), encoding="utf-8") as f:
            for r in csv.DictReader(f):
                if r.get("valido") != "1":
                    continue
                t = float(r["t"])
                if t >= desde and base_ini is not None:
                    v = float(r["patrimonio"]) - float(base_ini)
                else:
                    v = float(r["pl"])
                pts.append((t, v))
        pts += [tuple(p) for p in plan.get("pl", [])]
    else:
        pts = [tuple(p) for p in plan["pl"]]
    pts.sort()
    return np.array([p[0] for p in pts]), np.array([p[1] for p in pts])


def pl_en(serie, ts):
    xs, ys = serie
    if len(xs) == 0:
        return 0.0
    return float(np.interp(ts, xs, ys))


# --------------------------------------------------------------- narración
def preparar_voz(plan, tm):
    pistas, palabras = [], []
    fin_prev = 0.0
    for item in plan.get("narracion", []):
        t0 = max(t_de(item, tm), fin_prev + 0.05)
        audio, ts = voz.sintetizar(item.get("dice", item["texto"]))
        texto = item["texto"].split()
        if len(texto) != len(ts):  # si "dice" difiere, reparte el texto mostrado en el mismo tiempo
            dur = len(audio) / SR
            pesos = np.array([len(p) + 1.5 for p in texto], float)
            cum = np.concatenate([[0], np.cumsum(pesos)]) / pesos.sum() * dur
            ts = [{"palabra": p, "ini": cum[i], "fin": cum[i + 1]} for i, p in enumerate(texto)]
        pistas.append((t0, audio))
        for w in ts:
            palabras.append({"palabra": w["palabra"], "ini": t0 + w["ini"], "fin": t0 + w["fin"]})
        fin_prev = t0 + len(audio) / SR
        if fin_prev > plan.get("_total", 30) - 0.1:
            print(f"AVISO: la narración '{item['texto'][:30]}…' termina en {fin_prev:.1f}s", file=sys.stderr)
    return pistas, palabras


def bloques_subtitulos(palabras):
    bloques, actual = [], []
    for w in palabras:
        actual.append(w)
        largo = sum(len(x["palabra"]) for x in actual) + len(actual) - 1
        if len(actual) >= 3 or largo >= 15 or re.search(r"[.,;:!?…]$", w["palabra"]):
            bloques.append(actual)
            actual = []
    if actual:
        bloques.append(actual)
    for i, b in enumerate(bloques):
        sig = bloques[i + 1][0]["ini"] if i + 1 < len(bloques) else b[-1]["fin"] + 0.3
        b_fin = min(sig, b[-1]["fin"] + 0.6)
        for w in b:
            w["bloque_fin"] = b_fin
    return bloques


# ------------------------------------------------------------------- audio
def cargar_sfx(nombre):
    for ext in (".mp3", ".ogg", ".m4a", ".wav"):  # los originales (mp3) ganan a los sintetizados
        p = os.path.join(SON, nombre + ext)
        if os.path.exists(p):
            if ext == ".wav":
                x, sr = sf.read(p, dtype="float32", always_2d=True)
            else:
                raw = subprocess.run(["ffmpeg", "-v", "error", "-i", p, "-f", "f32le", "-ac", "2", "-ar", str(SR), "-"],
                                     capture_output=True, check=True).stdout
                x, sr = np.frombuffer(raw, np.float32).reshape(-1, 2), SR
            if x.shape[1] == 1:
                x = np.repeat(x, 2, 1)
            if sr != SR:
                n = int(len(x) * SR / sr)
                x = np.stack([np.interp(np.linspace(0, len(x) - 1, n), np.arange(len(x)), x[:, c]) for c in range(2)], 1)
            return x.astype(np.float32)
    print(f"AVISO: falta el sonido {nombre}", file=sys.stderr)
    return np.zeros((1, 2), np.float32)


def mezclar(dest, x, t, vol):
    i = int(t * SR)
    if i < 0:
        x, i = x[-i:], 0
    n = min(len(x), len(dest) - i)
    if n > 0:
        dest[i:i + n] += x[:n] * vol


def construir_audio(plan, tm, pistas, total, hook, fin):
    sfx = np.zeros((int(total * SR), 2), np.float32)
    vozp = np.zeros_like(sfx)
    drone = cargar_sfx("creepy_drone")
    reps = int(math.ceil(len(sfx) / len(drone)))
    mezclar(sfx, np.tile(drone, (reps, 1)), 0, plan.get("vol_drone", 0.22))
    mezclar(sfx, cargar_sfx("epic_hit"), 0, .8)
    mezclar(sfx, cargar_sfx("whoosh"), hook - 0.3, .6)
    mezclar(sfx, cargar_sfx("whoosh"), fin - 0.3, .6)
    mezclar(sfx, cargar_sfx("deep_hit"), fin, .85)
    for ev in plan.get("eventos", []):
        t = t_de(ev, tm)
        for nombre, dt, vol in SFX_EVENTO.get(ev["tipo"], []):
            mezclar(sfx, cargar_sfx(nombre), t + dt, vol * ev.get("vol", 1))
    for s in plan.get("sonidos_extra", []):
        mezclar(sfx, cargar_sfx(s["nombre"]), t_de(s, tm), s.get("vol", .6))
    for t0, a in pistas:
        mezclar(vozp, np.stack([a, a], 1), t0, 1.0)
    # ducking: baja efectos cuando habla la voz
    act = np.abs(vozp[:, 0])
    k = int(SR * 0.15)
    act = np.convolve(act, np.ones(k) / k, mode="same")
    act = np.clip(act / (act.max() or 1) * 4, 0, 1)
    k2 = int(SR * 0.25)
    act = np.convolve(act, np.ones(k2) / k2, mode="same")
    duck = 1 - 0.55 * act
    mix = sfx * duck[:, None] + vozp * 1.15
    mix /= max(1.0, np.abs(mix).max() / 0.95)
    return mix


# ------------------------------------------------------------------ dibujo
class Lienzo:
    def __init__(self, plan, tm, serie, bloques, ancho_g, alto_g):
        self.plan, self.tm, self.serie, self.bloques = plan, tm, serie, bloques
        self.ag, self.hg = ancho_g, alto_g
        self.yg = 200
        self.ypl = self.yg + alto_g + 18
        self.ysub = max(self.ypl + 130, 1010)
        self.f_tit = fuente(46)
        self.f_bar = fuente(24, "bold")
        self.f_vel = fuente(34)
        self.f_pl = fuente(58)
        self.f_pll = fuente(22, "bold")
        self.f_sub = fuente(64)
        self.f_rot = fuente(70)
        self.f_marca = fuente(22, "bold")
        self.eventos = sorted([dict(e, _t=t_de(e, tm)) for e in plan.get("eventos", [])], key=lambda e: e["_t"])
        self.barras = sorted([dict(b, _t=t_de(b, tm)) for b in plan.get("barra", [])], key=lambda b: b["_t"])
        self.pl_desde = tm.a_out(plan["pl_trade_desde"]) if "pl_trade_desde" in plan else 1e9

    # --- partes comunes
    def subtitulos(self, d, t):
        for b in self.bloques:
            if b[0]["ini"] <= t < b[0]["bloque_fin"]:
                palabras = [w["palabra"].upper() for w in b]
                esp = d.textlength(" ", font=self.f_sub)
                anchos = [d.textlength(p, font=self.f_sub) for p in palabras]
                total = sum(anchos) + esp * (len(palabras) - 1)
                escala = min(1.0, (W - 60) / total)
                f = self.f_sub if escala == 1.0 else fuente(int(64 * escala))
                anchos = [d.textlength(p, font=f) for p in palabras]
                esp = d.textlength(" ", font=f)
                total = sum(anchos) + esp * (len(palabras) - 1)
                x = (W - total) / 2
                for w, p, aw in zip(b, palabras, anchos):
                    color = AMARILLO if w["ini"] <= t < w["fin"] + 0.05 else BLANCO
                    d.text((x, self.ysub), p, font=f, fill=color, stroke_width=6, stroke_fill=NEGRO)
                    x += aw + esp
                return

    def marca(self, d):
        texto_centrado(d, W / 2, H - 50, "RaulFx", self.f_marca, (200, 200, 210))

    # --- escenas
    def hook(self, img_base, t):
        plan = self.plan
        lienzo = Image.new("RGB", (W, H), FONDO)
        z = 1.0 + 0.04 * min(t / 3.0, 1)
        g = img_base.resize((int(self.ag * z), int(self.hg * z)))
        ox, oy = (g.width - self.ag) // 2, (g.height - self.hg) // 2
        g = g.crop((ox, oy, ox + self.ag, oy + self.hg))
        g = Image.blend(g, Image.new("RGB", g.size, NEGRO), 0.45)
        lienzo.paste(g, (0, self.yg))
        d = ImageDraw.Draw(lienzo)
        m = plan["hook"]["monto"]
        col = VERDE if m >= 0 else ROJO
        pop = min(1.0, t / 0.18)
        f_big = fuente(int(120 * (1.25 - 0.25 * pop)))
        cy = self.yg + self.hg / 2
        texto_centrado(d, W / 2, cy - 190, "LLEGUÉ A IR", fuente(78), BLANCO, 5)
        texto_centrado(d, W / 2, cy - 90, dinero(m), f_big, col, 6)
        if t > 0.9:
            texto_centrado(d, W / 2, cy + 70, "¿CÓMO TERMINÓ?", fuente(70), AMARILLO, 5)
        texto_centrado(d, W / 2, 70, plan.get("titulo", "NAS100"), self.f_tit, BLANCO)
        self.subtitulos(d, t)
        self.marca(d)
        return lienzo

    def trade(self, img, t):
        tm = self.tm
        lienzo = Image.new("RGB", (W, H), FONDO)
        ts = tm.a_src(t)
        pl = pl_en(self.serie, ts)
        col = VERDE if pl >= 0 else ROJO
        d = ImageDraw.Draw(lienzo)
        # borde de color de la gráfica
        d.rectangle((0, self.yg - 6, W - 1, self.yg + self.hg + 5), fill=col)
        lienzo.paste(img, (0, self.yg))
        # barra superior
        barra = None
        for b in self.barras:
            if b["_t"] <= t:
                barra = b
        if barra:
            d.text((24, 22), barra.get("titulo", ""), font=self.f_tit, fill=BLANCO)
            y = 88
            for ln in barra.get("lineas", []):
                d.text((24, y), ln, font=self.f_bar, fill=(215, 220, 230))
                y += 32
            for ln in barra.get("naranja", []):
                d.text((24, y), ln, font=self.f_bar, fill=NARANJA)
                y += 32
        vel = tm.velocidad(t)
        if vel >= 1.5:
            s = f">> x{vel:.0f}"
            w = d.textlength(s, font=self.f_vel)
            d.rounded_rectangle((W - w - 48, 24, W - 16, 78), 14, fill=AMARILLO)
            d.text((W - w - 32, 26), s, font=self.f_vel, fill=NEGRO)
        # caja P/L
        etiqueta = "P/L DEL TRADE" if t >= self.pl_desde else "P/L ABIERTO"
        caja = (110, self.ypl, W - 110, self.ypl + 104)
        d.rounded_rectangle(caja, 18, fill=(20, 24, 32), outline=col, width=4)
        texto_centrado(d, W / 2, self.ypl + 8, etiqueta, self.f_pll, GRIS)
        texto_centrado(d, W / 2, self.ypl + 30, dinero(pl), self.f_pl, col)
        # rótulos de eventos
        for e in self.eventos:
            dt = t - e["_t"]
            if e["tipo"] in ROTULOS and 0 <= dt < 1.4 and not e.get("sin_rotulo"):
                txt, c = ROTULOS[e["tipo"]]
                txt = e.get("rotulo", txt)
                esc = 1.35 - 0.35 * min(1, dt / 0.15)
                f = fuente(int(70 * esc))
                w = d.textlength(txt, font=f)
                cy = self.yg + self.hg / 2 - 50 * esc
                d.rounded_rectangle((W / 2 - w / 2 - 26, cy - 8, W / 2 + w / 2 + 26, cy + 100 * esc), 20, fill=c)
                texto_centrado(d, W / 2, cy, txt, f, BLANCO, 3)
        self.subtitulos(d, t)
        self.marca(d)
        return lienzo

    def resultado(self, img_final, t, t_ini):
        r = self.plan["resultado"]
        lienzo = Image.new("RGB", (W, H), FONDO)
        g = Image.blend(img_final, Image.new("RGB", img_final.size, NEGRO), 0.8)
        lienzo.paste(g, (0, self.yg))
        d = ImageDraw.Draw(lienzo)
        dt = t - t_ini
        m = r["monto"]
        col = VERDE if m >= 0 else ROJO
        pop = min(1.0, dt / 0.2)
        texto_centrado(d, W / 2, 170, "RESULTADO", fuente(60), GRIS)
        texto_centrado(d, W / 2, 250, dinero(m), fuente(int(130 * (1.2 - 0.2 * pop))), col, 6)
        y = 450
        for ln in r.get("lineas", []):
            texto_centrado(d, W / 2, y, ln, fuente(30, "bold"), (225, 228, 235))
            y += 46
        if "balance" in r:
            a, b = r["balance"]
            y += 20
            texto_centrado(d, W / 2, y, "BALANCE", fuente(24, "bold"), GRIS)
            texto_centrado(d, W / 2, y + 34, f"{a:,.2f}  →  {b:,.2f}", fuente(44), BLANCO)
            y += 110
        if dt > 0.6 and r.get("frase"):
            frase = r["frase"].upper()
            # partir en líneas de ≤ 18 caracteres
            lineas, act = [], ""
            for p in frase.split():
                if len(act) + len(p) + 1 > 18 and act:
                    lineas.append(act)
                    act = p
                else:
                    act = (act + " " + p).strip()
            lineas.append(act)
            yy = max(y + 30, 860)
            for ln in lineas:
                texto_centrado(d, W / 2, yy, ln, fuente(64), AMARILLO, 5)
                yy += 80
        texto_centrado(d, W / 2, H - 120, "RaulFx", fuente(52), BLANCO)
        return lienzo


# -------------------------------------------------------------------- main
def main(ruta_plan):
    plan = json.load(open(ruta_plan, encoding="utf-8"))
    HOOK = plan.get("duracion_hook", 3.0)
    TOTAL = plan.get("duracion_total", 30.0)
    plan["_total"] = TOTAL
    tm = Tiempo(plan["tramos"], HOOK)
    FIN = tm.fin
    if TOTAL - FIN < 1.5:
        print(f"AVISO: los tramos terminan en {FIN:.2f}s; queda poco para el resultado", file=sys.stderr)

    g = plan["grafica"]
    ancho = W
    alto = min(700, int(round(W * g["h"] / g["w"] / 2) * 2))
    tmp = tempfile.mkdtemp(prefix="reel_")
    try:
        print("1/4 cortando tramos de la grabación…")
        base = preparar_grafica(plan, tm, tmp, ancho, alto)
        img_hook = frame_en(plan, plan["hook"]["t_src"], ancho, alto)
        print("2/4 voz…")
        pistas, palabras = preparar_voz(plan, tm)
        bloques = bloques_subtitulos(palabras)
        serie = serie_pl(plan)
        print("3/4 audio…")
        mix = construir_audio(plan, tm, pistas, TOTAL, HOOK, FIN)
        wav = os.path.join(tmp, "mix.wav")
        sf.write(wav, mix, SR)

        print("4/4 video…")
        salida = ruta(plan["salida"])
        os.makedirs(os.path.dirname(salida), exist_ok=True)
        ff = subprocess.Popen(["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "rgb24",
                               "-s", f"{W}x{H}", "-r", str(FPS), "-i", "-", "-i", wav,
                               "-af", "loudnorm=I=-14:TP=-1.0:LRA=11",
                               "-c:v", "libx264", "-preset", "veryfast", "-crf", "19", "-pix_fmt", "yuv420p",
                               "-c:a", "aac", "-b:a", "192k", "-ar", "48000", "-shortest",
                               "-movflags", "+faststart", salida], stdin=subprocess.PIPE)
        lz = Lienzo(plan, tm, serie, bloques, ancho, alto)
        cap = cv2.VideoCapture(base)
        ultimo = img_hook
        for i in range(int(TOTAL * FPS)):
            t = i / FPS
            if t < HOOK:
                fr = lz.hook(img_hook, t)
            elif t < FIN:
                ok, f = cap.read()
                if ok:
                    ultimo = Image.fromarray(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
                fr = lz.trade(ultimo, t)
            else:
                fr = lz.resultado(ultimo, t, FIN)
            ff.stdin.write(fr.tobytes())
        ff.stdin.close()
        ff.wait()
        cap.release()
        print("listo:", salida)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == "__main__":
    main(sys.argv[1])
