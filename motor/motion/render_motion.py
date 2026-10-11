"""
render_motion.py — um MP4 por slide do carrossel, animado pelo motion.js (protótipo).

Uso: python motion/render_motion.py <carrossel.json> [out_dir] --tema <pasta_do_tema> [--dur 6] [--fps 30] [--slides 1,8]
- out_dir padrão: <pasta do json>/motion
- grava slide-NN.mp4 (H.264, yuv420p, 1080x1440) e previa.mp4 (todos em sequência)
Mesma página e mesmos dados do render.py; o tempo é dirigido quadro a quadro (Motion.seek), sem relógio real.
"""
import json
import subprocess
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

AQUI = Path(__file__).resolve().parent
MOTOR = AQUI.parent
W, H = 1080, 1440


def arg(args, nome, padrao=None):
    if nome in args:
        i = args.index(nome)
        v = args[i + 1]
        del args[i:i + 2]
        return v
    return padrao


def main():
    args = sys.argv[1:]
    tema_dir = Path(arg(args, "--tema") or sys.exit(__doc__)).resolve()
    dur, fps = float(arg(args, "--dur", 6)), int(arg(args, "--fps", 30))
    so = arg(args, "--slides")
    json_path = Path(args[0]).resolve()
    out = Path(args[1]) if len(args) > 1 else json_path.parent / "motion"
    out.mkdir(parents=True, exist_ok=True)
    tema = json.loads((tema_dir / "tema.json").read_text(encoding="utf-8"))
    data = json.loads(json_path.read_text(encoding="utf-8"))
    for s in data["slides"]:
        for k in ("imagem", "recorte"):
            if s.get(k):
                s[k] = (json_path.parent / s[k]).resolve().as_uri()
        ref = s.get("referencia")
        if ref and ref.get("print"):
            ref["print"] = (json_path.parent / ref["print"]).resolve().as_uri()
    n = len(data["slides"])
    alvo = [int(x) for x in so.split(",")] if so else list(range(1, n + 1))
    feitos = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": W, "height": H}, device_scale_factor=1)
        page.add_init_script(
            f"window.__CARROSSEL = {json.dumps(data)}; window.__TEMA = {json.dumps(tema)}; "
            f"window.__TEMA_CSS = {json.dumps((tema_dir / 'tema.css').as_uri())};")
        for i in alvo:
            page.goto(f"{(MOTOR / 'carrossel.html').as_uri()}?slide={i}", wait_until="load", timeout=20000)
            page.wait_for_function("document.title.startsWith('READY:')", timeout=15000)
            page.add_script_tag(path=str(AQUI / "motion.js"))
            page.evaluate(f"Motion.init({{duracao: {dur}}})")
            mp4 = out / f"slide-{i:02d}.mp4"
            ff = subprocess.Popen(["ffmpeg", "-y", "-loglevel", "error", "-f", "image2pipe", "-framerate", str(fps), "-i", "-",
                                   "-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "medium", str(mp4)],
                                  stdin=subprocess.PIPE)
            for f in range(int(dur * fps)):
                page.evaluate(f"Motion.seek({f / fps})")
                ff.stdin.write(page.screenshot(clip={"x": 0, "y": 0, "width": W, "height": H}, type="jpeg", quality=92))
            ff.stdin.close()
            ff.wait()
            feitos.append(mp4)
            print("ok:", mp4.name)
        browser.close()
    lista = out / "lista.txt"
    lista.write_text("".join(f"file '{f.name}'\n" for f in feitos))
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "concat", "-safe", "0", "-i", str(lista), "-c", "copy",
                    str(out / "previa.mp4")], check=True)
    lista.unlink()
    print(f"OK: {len(feitos)} MP4 {W}x{H} em {out} (+ previa.mp4)")


if __name__ == "__main__":
    main()
