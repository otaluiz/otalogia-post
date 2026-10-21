"""Confere se algum texto passa na frente de rosto nos slides com imagem do carrossel com motion, com o parallax
em movimento. Rostos: Haar do OpenCV na foto original (como o compor.py) + cabeça pelo recorte, quando houver.
O título que fica atrás do recorte não conta (o personagem cobre). Rode depois de `SO_PREPARAR=1 render.sh`.

Uso: python checar_rostos.py carrosseis/<slug>      (sai com código 1 se achar sobreposição)
"""
import functools
import http.server
import json
import sys
import threading
from pathlib import Path

import numpy as np
from PIL import Image

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / ".vendor_cv4"))
import cv2 as cv  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

W, H, FOLGA = 1080, 1440, 12


def rostos_haar(im):
    g = cv.equalizeHist(cv.cvtColor(np.asarray(im), cv.COLOR_RGB2GRAY))
    out = []
    for nome, flip in (("haarcascade_frontalface_default.xml", False), ("haarcascade_profileface.xml", False), ("haarcascade_profileface.xml", True)):
        c = cv.CascadeClassifier(cv.data.haarcascades + nome)
        for x, y, w, h in c.detectMultiScale(cv.flip(g, 1) if flip else g, 1.1, 6, minSize=(70, 70)):
            x = W - x - w if flip else x
            out.append([x - .15 * w, y - .15 * h, x + 1.15 * w, y + 1.15 * h])
    return out


def cabeca_recorte(p):
    a = np.asarray(Image.open(p).convert("RGBA").resize((W, H)))[:, :, 3] > 128
    ys, xs = np.where(a)
    if not len(ys):
        return []
    y0, y1 = ys.min(), ys.max()
    by1 = y0 + 0.22 * (y1 - y0)
    banda = xs[ys <= by1]
    return [[banda.min(), y0, banda.max(), by1]]


JS = """([sid, caixas, t]) => {
  const tl = window.__timelines.main; tl.seek(t);
  document.querySelectorAll('section').forEach(s => { const a = +s.dataset.start; s.style.visibility = (t >= a && t < a + +s.dataset.duration) ? 'visible' : 'hidden'; });
  const sec = document.getElementById(sid), rec = sec.querySelector('.recorte'), ref = rec || sec.querySelector('.foto');
  // caixa da imagem (cover de 1080x1440) -> página, com a transformação atual do elemento (parallax, zoom)
  const b = { l: ref.offsetLeft, t: ref.offsetTop, w: ref.offsetWidth, h: ref.offsetHeight };
  const k = Math.max(b.w / 1080, b.h / 1440), dx = (b.w - 1080 * k) / 2, dy = (b.h - 1440 * k) / 2;
  const cs = getComputedStyle(ref), M = new DOMMatrix(cs.transform === 'none' ? undefined : cs.transform);
  const [ox, oy] = cs.transformOrigin.split(' ').map(parseFloat);
  const pt = (x, y) => { const p = M.transformPoint(new DOMPoint(dx + x * k - ox, dy + y * k - oy)); return [p.x + ox + b.l, p.y + oy + b.t]; };
  const rostos = caixas.map(([x0, y0, x1, y1]) => { const a = pt(x0, y0), c = pt(x1, y1); return [a[0], a[1], c[0], c[1]]; });
  // título atrás do recorte não conta; o resto do texto está na frente
  const atras = rec && +getComputedStyle(rec).zIndex >= 4;
  const sel = '.emocao, .cta .pill, .cta-txt, .arrasta, .gancho' + (atras ? '' : ', .display .linha > span');
  const achados = [];
  sec.querySelectorAll(sel).forEach(el => {
    const r = el.getBoundingClientRect(); if (!r.width || +getComputedStyle(el).opacity === 0) return;
    rostos.forEach(f => { if (r.left < f[2] + %d && r.right > f[0] - %d && r.top < f[3] + %d && r.bottom > f[1] - %d) achados.push([el.className || el.tagName, el.textContent.trim().slice(0, 30), f.map(Math.round)]); });
  });
  return achados;
}""" % (FOLGA, FOLGA, FOLGA, FOLGA)


def main():
    car = Path(sys.argv[1]).resolve()
    mot = car / "motion"
    class Quieto(http.server.SimpleHTTPRequestHandler):
        def log_message(self, *a):
            pass
    srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Quieto, directory=str(mot)))
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    problemas = 0
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": W, "height": H})
        pg.add_init_script("window.__timelines = {}")
        pg.goto(f"http://127.0.0.1:{srv.server_port}/index.html")
        pg.wait_for_load_state("networkidle")
        pg.evaluate("document.fonts.ready")
        secs = pg.evaluate("""[...document.querySelectorAll('section')].filter(s => s.querySelector('.foto')).map(s => [s.id, +s.dataset.start,
            s.querySelector('.foto').getAttribute('src'), s.querySelector('.recorte')?.getAttribute('src') || null])""")
        for sid, ini, foto, rec in secs:
            orig = car / Path(foto).name  # foto original (a de motion/img pode estar sem o sujeito)
            caixas = rostos_haar(Image.open(orig).convert("RGB").resize((W, H)))
            if rec:
                caixas += cabeca_recorte(car / Path(rec).name)
            caixas = [[float(v) for v in c] for c in caixas]
            for t in (ini + 2.5, ini + 4.0, ini + 5.9):
                for cls, txt, f in pg.evaluate(JS, [sid, caixas, t]):
                    problemas += 1
                    print(f"SOBREPOE {car.name} {sid} t={t:.1f}s: [{cls}] '{txt}' sobre rosto {f}")
            print(f"{sid}: {len(caixas)} rosto(s)/cabeça conferidos")
        b.close()
    print("ok, nenhum texto sobre rosto" if not problemas else f"{problemas} sobreposições")
    sys.exit(1 if problemas else 0)


if __name__ == "__main__":
    main()
