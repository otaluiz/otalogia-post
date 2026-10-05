# Contrato de conteúdo do carrossel (carrossel-engine)

Fonte única de dados do renderizador (`carrossel.js`). Exemplo completo: `exemplo/exemplo.json`.
Cores, fontes e strings de marca vêm do **tema** (pasta com `tema.css` + `tema.json`; ver README).
Fluxo: `python render.py <carrossel.json> [out_dir] --tema <pasta_do_tema>` gera `slide-01.png … slide-NN.png` (1080×1440).
Debug visual: abrir `carrossel.html?tema=<url da pasta do tema>&data=<url do json>` (todos os slides empilhados) ou `?slide=N` (1080×1440 exatos).

## Raiz

| Campo | Tipo | Regra |
|---|---|---|
| `id` | string | nome da pasta de saída (ex.: `2026-10-ia-sem-hype-01`) |
| `meta.serie` | string | aparece em caixa alta na linha de metadados |
| `meta.data` | string `AAAA/MM` | idem |
| `slides` | lista | 1 ou mais; ver regras de sequência |

Linha de metadados (automática): `<nome_meta do tema>` · `<SERIE>` · `<AAAA/MM>`. Rodapé: `<handle>`, `<rodape_centro>` e bolinhas-guia (strings do `tema.json`).

## Slide

| Campo | Tipo | Onde | Regra |
|---|---|---|---|
| `template` | `T1` `T1b` `T2` `T2c` `T3` `T4` `T5` | todos | obrigatório |
| `display` | lista de strings | todos | linhas em caixa alta (Inter Tight 900); o texto é escrito já em maiúsculas |
| `emocao` | objeto, opcional | todos | bloco serifado itálico (máx. 1 por slide) |
| `emocao.texto` | string | | minúsculas como escrito; `" / "` = quebra de linha dentro do MESMO bloco serifado (estrutura em paralelo) |
| `emocao.posicao` | `antes` `depois` `sobreposta` `entre` | | `sobreposta` sobe e encosta/cobre a última linha do display |
| `emocao.apos_linha` | inteiro ≥ 1 | só com `entre` | insere o bloco depois da linha N do display (1 ≤ N < nº de linhas) |
| `corpo` | string, opcional | todos (em T1b vira o texto da pill) | até 2 linhas, Inter Tight 400 30u |
| `lista` | até 4 strings | só T3 | numeradas `01`–`04` em mono na cor de apoio (`--apoio`) |
| `diagrama` | `{tipo:"barra", partes:[{valor, rotulo, nota, destaque?}]}` | só T3 | barra única dividida por `valor` (%); a parte com `destaque:true` fica preenchida na cor quente (`--quente`) |
| `cta` | `{acao, texto}` | só T4 | `acao` = texto da pill; `texto` = linha de apoio abaixo |
| `imagem` | caminho relativo ao JSON, ou `null` | T1/T1b/T2/T4 (nunca T2c/T3) | **a chave é obrigatória no slide 1, no slide 2 e no último** (regra: todo carrossel tem imagem na capa, no slide 2 e no CTA). `null` usa placeholder SVG de crepúsculo (céu `--ink`, brilho `--quente` no horizonte, figura pequena; busto no T1b) e gera aviso |
| `referencia` | `{site, nome, descricao, print}` | só T5 | obrigatório no T5; `print` = PNG do site (relativo ao JSON, gerar com `print_site.py`) ou `null` (placeholder + aviso). T5 aceita `display` opcional (até 2 linhas curtas, alinhadas à direita na linha do chip) e não aceita `emocao`/`corpo`/`lista`/`diagrama`/`cta` |
| `gancho` | string, opcional | só T1/T1b | linha serifada pequena; exceção documentada à regra de 1 bloco serifado (o lockup da capa conta como uma unidade) |
| `fundo` | `ink` (padrão) ou `papel` | só T1b | extensão: T1b existe nos dois fundos e a cor quente depende dele |

### Layouts com imagem

- **T2 com foto (papel + foto colada):** fundo papel como sempre; texto (display + emocao) de y 200u a 640u; foto de 936×500u em x 72u, y 700u a 1200u, `cover`, filete de 1u grafite a 15%; grão por cima de tudo. Se o bloco de texto passar de 640u, o display e a serifada encolhem 7% por passo (≤ 20 iterações) até caber. Cor quente do papel (`--quente-papel`).
- **T4 com foto:** foto sangrada no fundo, véu `--ink` chapado a 70% (sem gradiente), grão por cima, depois o layout normal do T4 (texto branco, palavra quente, pill na cor quente, sem seta).

### Marcador `[palavra]`

Colchetes marcam a palavra de cor quente, no `display` OU no `emocao.texto`. No máximo um marcador por slide.
**A cor quente é decidida pelo template, nunca pelos dados**: `--quente` sobre ink/foto (T1, T1b-ink, T3, T4) e
`--quente-papel` sobre papel/caderno (T2, T2c, T1b-papel). Os dados não escolhem cor; assim a
cor quente forte sobre papel (baixo contraste) é impossível por construção.

### Regras tipográficas implementadas

- Máx. 1 bloco serifado (`emocao`) por slide; o paralelo `" / "` conta como um bloco. T1/T1b podem ter também `gancho`.
- Display: 180-230u no T1, 96-140u nos demais; o tamanho encolhe de forma determinística (≤ 20 iterações) até a linha mais larga caber em 936u (776u no T2c, que começa à direita da margem). A serifada acompanha ~1.1× o display e também encolhe se não couber.
- Sem gradiente em T1/T4 nem como fundo principal em lugar nenhum. Únicas exceções: o céu do placeholder de foto (substituto de fotografia) e a vinheta sutil do papel (overlay, não fundo).
- Grão em 100% dos slides (0.10 papel / 0.14 ink / 0.18 foto). Seta do rodapé some no último slide.

## Validação (`Carrossel.validate(data)` → `{errors, warnings}`)

Erros (bloqueiam o `render.py`, que sai com código ≠ 0 sem escrever PNGs):
template desconhecido; mais de 1 marcador `[ ]` num slide; hook (slide 1: palavras de display + emocao, ignorando colchetes e `" / "`) com mais de 10 palavras; `lista` com mais de 4 itens; `lista`/`diagrama` fora do T3; `cta` fora do T4; `imagem` em T2c/T3; chave `imagem` ausente no slide 2 ou no último (`null` vale); `gancho` fora de T1/T1b; primeiro slide que não é T1/T1b; último que não é T4; mais de 3 slides seguidos com o mesmo fundo (família papel = T2/T2c; família ink = T3/T4; T1/T1b zeram a contagem); `emocao.posicao` inválida; `entre` sem `apos_linha` válido; `apos_linha` com posição diferente de `entre`; `diagrama.tipo` ≠ `barra`.

Avisos: T1, T2 ou T4 com `imagem: null` (usa placeholder).

## Saída de erro do renderizador

No navegador, `document.title = 'READY:{"slides":N,"errors":[],"warnings":[],"fit":[…]}'` sinaliza fim do render
(fontes carregadas + ajuste do display). Com erros, o modo empilhado mostra um banner vermelho.


## T1b modo camadas (`recorte`)

`recorte` (só T1b): PNG com fundo transparente do sujeito, mesmo tamanho/enquadramento de `imagem` (gerar com rembg, local ou na nuvem com `pip install rembg`, a partir da própria `imagem`). Com `recorte`, o T1b vira: foto sangrada → display atrás → recorte → emoção na frente (no peito). Caminho relativo ao JSON, como `imagem`.


## Marca-texto `{palavra}`

`{palavra}` (em display, emocao ou item de lista) vira caixa na cor quente com texto ink. Conta como marcador junto com `[palavra]`: no máximo 1 por slide. Usar nos slides só de texto; `[palavra]` fica para slides com foto.

## metadata.json (postagem automática)

`python metadata.py <carrossel.json> <ordem_fila> --tema <pasta_do_tema> #tag1 #tag2 ...` escreve `png/metadata.json` no schema da skill post-instagram (cliente, handle e familia_cor do `tema.json`, `postado:false`).


## T4 em camadas (`recorte`)

`recorte` também vale no T4: PNG transparente do sujeito no mesmo enquadramento de `imagem`. O sujeito fica acima do véu e do texto; o bloco de texto começa em y 640, então o sujeito precisa estar no terço de cima da foto.

## Texturas

T2 recebe `assets/papel-dobra.png` + `assets/halftone.png`; T2c só `papel-dobra.png`; T1b recebe `assets/pano.png`. Recriar com `python assets/texturas.py`.


## T5 referência

Fundo ink com grão: chip `REFERÊNCIA` (cor `--quente`, texto `--ink`) em y 190u e, de y 250u a 1150u, um card de navegador (3 bolinhas + pill com a URL na barra de 80u, print do site com `object-fit: cover` e `object-position: top`, e no rodapé do card o `nome` em display 64u + `descricao` em corpo 34u). Tudo vem de variáveis do tema.
Regras: não pode ser o primeiro nem o último slide; não conta na regra de "mais de 3 slides seguidos com o mesmo fundo" (nem zera a contagem); `print: null` usa placeholder e gera aviso.

Gerar o print: `python print_site.py <url> <out.png> [--w 1280 --h 900]` (Chromium headless, escala 2x reduzida com Pillow, só a viewport, esconde banners de cookie por CSS, sem clicar em "aceitar").


## Composição em camadas (`recorte` + `bloco` + `sujeito`) e textura LED

Vale para T1, T1b, T2 (com foto) e T4: `recorte` = PNG do sujeito (mesmo quadro de `imagem`). Ordem de empilhamento (z): foto 1, véu/scrim 2, display (negrito) 4, recorte 6, emocao/corpo/gancho/CTA 8, topo e rodapé 20, grão 50. No T4 o véu fica sob o sujeito (sujeito em brilho total). T1/T2 com `recorte` usam a classe `cam2`; T1b/T4 só com `recorte` (sem `bloco`/`sujeito`) mantêm o CSS antigo, idêntico ao anterior.

| Campo | Tipo | Regra |
|---|---|---|
| `bloco` | `{y, alinhar, largura?}` | topo do bloco de texto em u (1080x1440); `alinhar` = `esquerda` `direita` `centro`; `largura` padrão 936 (o display encolhe para caber). Sobrescreve a posição padrão do template. `manual: true` faz o `compor.py` manter o bloco. |
| `sujeito` | `{cabeca, caixa, rostos, rostos_sujeito, rostos_manual}` | caixas `[x0,y0,x1,y1]` em u (escrito pelo `compor.py`). `cabeca` e `rostos_sujeito` (rostos do próprio recorte): texto à frente não pode cobri-los; o display passa por trás. `rostos` (outras figuras: estátuas, segunda cabeça etc.): nenhum texto, nem o display. Sem `recorte`, cabeça e todos os rostos valem para todo o texto. |
| `textura` | `"led"` ou `"grain"` | `grain`: só grão forte (`--grao-grain`, padrão .32) sobre o fundo liso, sem gradiente de cor; padrão do slide 3 (o `compor.py` marca sozinho). `led`, só T2/T2c/T3: camada de pontos LED (`assets/led-grade.png` como máscara, cor `--led-cor`/`--quente`; no papel `--led-cor-papel`/`--apoio-papel`) entre o fundo e o texto. Intensidade = `--tex-led` do tema (padrão 0 = desligada). |

Colisão (JS, depois do ajuste do display): se emocao/CTA/corpo/gancho tocam cabeça ou rosto (+24u), o item é deslocado, no máximo 20 tentativas determinísticas: abaixo do display, abaixo da cabeça/rostos, acima, acima do display, cada uma no x atual e no lado com mais espaço; por último a emoção encolhe até 0.7x. Faixa útil de y: 190 a 1280. O relatório sai em `window.__fitReport.camadas` (`cabeca`, `rostos`, `display`, `emocao`, `cta`, `colisao`, `movidos`). `render.py` aborta (código ≠ 0, nenhum PNG) se `colisao` for verdadeiro em qualquer slide.

`python compor.py <carrossel.json ...> [--led capa,cta,slide2] [--sem-recorte]` escreve `recorte`, `bloco`, `sujeito` e `textura` (ver docstring do script). Requer rembg e OpenCV 4.x (Haar): com OpenCV 5 use `pip install --target .vendor_cv4 opencv-python-headless==4.10.0.84` dentro do motor.


## Rodapé claro (`rodape`)

`rodape: "claro"` (qualquer slide com `recorte`/`bloco`) força o rodapé em branco com halo ink. Usar quando, num T1b de fundo papel, o rodapé cai sobre roupa ou área escura da foto e o texto grafite com halo creme fica borrado.


## Tecido (`tecido`)

Trama de pano (`assets/pano.png`, soft-light, opacidade `--tex-pano`) por cima de tudo. T1b camadas: padrão ligado (`"tecido": false` desliga). T1: padrão desligado (`"tecido": true` liga).
