# carrossel-engine

Motor de carrosséis sem marca: um `carrossel.json` vira PNGs 1080x1440 (um por slide), com templates T1, T1b, T2, T2c, T3, T4 e T5 (referência: card de navegador com print de site). Cores, fontes e textos de marca vêm de um **tema**. Contrato dos dados: `carrossel.schema.md`.

## Tema

Pasta com dois arquivos:

- `tema.css`: só custom properties em `:root` (`--ink --papel --branco --grafite --quente --quente-papel --apoio --apoio-papel --detalhe --papel-sombra --f-display --f-serif --f-body --f-mono` e opacidades `--tex-*`). Lista de defaults em `carrossel.css`.
- `tema.json`:

```json
{"marca":"minhamarca","nome_meta":"MINHAMARCA","handle":"@minhamarca","rodape_centro":"salva pra depois",
 "google_fonts":"<url css2 do Google Fonts>",
 "fontes":["900 100px \"Inter Tight\"", "italic 400 100px \"Instrument Serif\""],
 "familia_cor":"ink-laranja"}
```

`fontes` é a lista que o render espera e confere (fallback silencioso de fonte = falha).

## Uso

```
pip install playwright pillow && playwright install chromium
python render.py <carrossel.json> [out_dir] --tema <pasta_do_tema>     # ou env CARROSSEL_TEMA
python metadata.py <carrossel.json> <ordem_fila> --tema <pasta_do_tema> #tag1 #tag2
python assets/texturas.py                                               # recria as texturas
python compor.py <carrossel.json> [--led capa,cta,slide2] [--sem-recorte]   # camadas: recorte + bloco + rostos (ver schema)
python print_site.py <url> <out.png> [--w 1280 --h 900]                 # print de site para o T5
```

Imagens (`imagem`, `recorte`) são resolvidas relativas ao JSON. Preview no navegador (via servidor http): `carrossel.html?tema=<url da pasta do tema>&data=<url do json>`.

Recorte de sujeito (`recorte`, modo camadas) usa rembg, que roda local ou na nuvem com `pip install rembg`. `python recorte.py foto.png saida.png` só grava o recorte se ele for limpo (tamanho do sujeito, uma peça só, borda nítida); senão sai com código 2. No T1b, `"tecido": false` desliga a textura de tecido (capas de banco).

## Uso como submódulo

`git submodule add <url> motor` e apontar o render para o tema da marca, por exemplo `python ../../motor/render.py carrossel.json png --tema ../../design-system/tema`.
