"""
print_site — tira o print da viewport de um site para o template T5 (referência).

Uso: python print_site.py <url> <out.png> [--w 1280 --h 900] [--wait 1.5]
Chromium headless, device_scale_factor 2 e redução com Pillow para w x h (mais nítido).
Espera load + 1.5s e esconde banners de cookie/consentimento por CSS (melhor esforço; nunca clica em aceitar).
Só a viewport, não a página inteira.
"""
import argparse

from PIL import Image
from playwright.sync_api import sync_playwright

CSS_BANNERS = """
[id*="cookie" i],[class*="cookie" i],[id*="consent" i],[class*="consent" i],
[id*="gdpr" i],[class*="gdpr" i],[id*="banner" i],[class*="banner" i],[role="dialog"],[class*="modal" i],[class*="overlay" i]
{ display: none !important; }
"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("url")
    ap.add_argument("out")
    ap.add_argument("--w", type=int, default=1280)
    ap.add_argument("--h", type=int, default=900)
    ap.add_argument("--wait", type=float, default=1.5, help="segundos extras após o load (sites lentos: 5)")
    a = ap.parse_args()
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        pg = b.new_page(viewport={"width": a.w, "height": a.h}, device_scale_factor=2)
        pg.goto(a.url, wait_until="load", timeout=45000)
        pg.wait_for_timeout(int(a.wait * 1000))
        pg.keyboard.press("Escape")  # fecha modais simples; nunca clica em aceitar
        pg.add_style_tag(content=CSS_BANNERS)
        pg.wait_for_timeout(300)
        pg.screenshot(path=a.out, full_page=False)
        b.close()
    Image.open(a.out).convert("RGB").resize((a.w, a.h), Image.LANCZOS).save(a.out)
    print("OK:", a.out)


if __name__ == "__main__":
    main()
