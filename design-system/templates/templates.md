# Templates — otalogia post design system

Direção "Editorial de engenheiro". Render real em `../index.html`; tokens em `../tokens.json`.
Formato 1080×1440 (3:4), com zona segura 4:5 (os 45px de cima e de baixo podem ser cortados no grid do perfil).

O ritmo vem das referências: **capa cinematográfica → miolo só tipográfico → CTA**. Uma ideia por slide, frases curtas e uma virada no meio.

## Elementos fixos (todos os templates)

- **Linha de metadados** (topo, y=96): JetBrains Mono 20px, caixa alta, tracking 0.06em, em 3 blocos: `OTALOGIA` · `<SÉRIE>` · `<AAAA/MM>` (sem FIG). Branco sobre ink/foto, grafite 70% sobre papel.
- **Rodapé** (base, y=96 da borda): `@otalogia` em Instrument Serif itálico (esquerda) · marcador + "salva pra depois" (centro) · bolinhas-guia do carrossel à direita, uma por slide, a atual preenchida (aparecem em todos os slides, inclusive o último).
- **Guia do carrossel:** bolinhas de 14px preenchidas a 40%, a do slide atual vira pílula de 38px em 100%. Nos slides com textura LED, as bolinhas ganham uma placa na cor do fundo (ink 88%) para não sumirem na grade.
- **Grão** em 100% dos slides (opacidade 0.10 papel / 0.14 ink / 0.18 foto).
- **Margem lateral 72px**, nunca varia dentro do carrossel.

## Marca-texto

Nos slides só de texto (sem foto), a palavra-chave vai em **marca-texto**: `{palavra}` no JSON vira caixa laranja `#FF5A1F` com texto ink, levemente torta. Um destaque por slide: ou `[palavra]` (cor quente) ou `{palavra}` (marca-texto), nunca os dois. Em slide com foto (capa, slide 2, CTA) continua `[palavra]`.

## Regra da dupla tipográfica

- **Inter Tight 900, caixa alta, tracking -0.035em, entrelinha 0.86** carrega o **fato**.
- **Instrument Serif Italic** carrega a **emoção**: no máximo 1 palavra ou expressão por slide, que pode encostar ou se sobrepor ao display (é intencional, como nas referências).
- A cor quente vai na palavra mais forte do slide e só nela: `#FF5A1F` sobre ink/foto, `#D2410F` sobre papel.

## T1 — Capa foto (hook)

Slide 1. Funciona como thumbnail.
- Fundo: foto cinematográfica sangrada (figura humana pequena em paisagem grande, luz de holofote ou pôr do sol, um toque surreal). Imagem gerada **sem texto** (Higgsfield `gpt_image_2_5`, padrão do otalogia; ver `geracao_imagem` em tokens.json), com color grading no prompt: sombras para o ink e altas para o laranja.
- Lockup do hook centralizado em y 300-900: serifada itálica pequena acima ("Todo mundo"), display gigante (180-230px) com a palavra-chave em laranja, linha serifada abaixo com a promessa/tensão.
- Gancho final opcional em serifada itálica ("aqui está o porquê…") perto da figura.
- Hook com 5-10 palavras no total.
- Trama de tecido por cima de tudo (foto e título), igual ao T1b: `"tecido": true` no slide (no motor o padrão do T1 é sem tecido).

## T1b — Capa retrato (Luiz)

Variante de T1 para Reels-capa e opinião.
- Retrato do Luiz recortado (rembg local), com tratamento de **linhas concêntricas/meio-tom**, **sobreposto ao título**: a cabeça cobre no máximo 1 letra da palavra-chave (mesma regra de oclusão do aidealab).
- Fundo papel ou ink; um script ou traço azul atrás do retrato pode servir como camada de profundidade.
- Caixa de pergunta (pill escura com borda tracejada) na base: a pergunta que gera identificação.

### T1b no modo camadas (padrão com o Luiz)

Referência aprovada: `templates/t1b-referencia-luiz.png`.
- Retrato gerado com o personagem **@luizota** no **Soul 2.0** (`soul_2` + Soul "Luiz ota"), prompt montado a partir do banco `../esteticas-editoriais.md`, cintura pra cima, cabeça no meio do quadro, céu limpo acima.
- Recorte local com rembg no mesmo enquadramento (`recorte`). Camadas: foto sangrada → display (Inter Tight 220u) → recorte do Luiz → serifada na frente, no peito.
- A cabeça cobre no máximo parte de 1 letra do display; ajustar a altura do título se cobrir mais.
- **Pose e cenário sempre diferentes a cada carrossel** (prender atenção): grande-angular/olho de peixe de cima, contra-plongée com a mão vindo pra câmera, estúdio de fundo liso colorido, objeto surreal (celulares pendurados, câmera, spray). Nunca repetir o retrato parado do carrossel anterior. Refs: pins de editorial de moda enviados em 2026-10-04.

## T2 — Papel (miolo tipográfico)

Slides de tensão e desenvolvimento.
- Fundo papel `#ECE6DA` com vinheta leve e dobra vertical opcional.
- Até 2 blocos de frase (display 96-120px + serifada laranja-tinta), alinhados à esquerda, no terço central.
- Ideal para a **estrutura em paralelo** ("Qualquer um gera *uma imagem*. / Qualquer um gera *um texto*.").

**Variante com foto (obrigatória no slide 2):** papel + foto colada. Texto (display + serifada) no alto, de y 200 a 640, logo abaixo da linha de metadados; foto abaixo, na largura do texto (936u, x 72), de y 700 a 1200 (≥ 40u livres até o rodapé), `object-fit: cover`, com filete de 1u em tinta a 15% (sensação de foto impressa). O display encolhe se o bloco de texto passar de 640, para nunca encostar na foto. Cor quente segue `#D2410F`. Os demais T2 do miolo continuam sem foto. Sem imagem pronta, `imagem: null` usa placeholder SVG (crepúsculo) e gera aviso.

## T2c — Caderno (variação de T2)

A virada/insight.
- Papel quadriculado (36px, azul 8%) com margem vertical laranja-tinta em x=200 e o `#` técnico no canto.
- Display + serifada grande sobreposta (a palavra-emoção "pendurada" na margem), com a conclusão em serifada itálica abaixo.

## T3 — Ink (miolo técnico/diagrama)

Prova, números, processo, listas.
- Fundo ink `#0B0B12` com grão.
- Display branco + número ou dado em laranja; diagramas em linhas ciano 2px com rótulos em JetBrains Mono.
- Listas: até 4 itens, numeração mono `01-04` (só quando é sequência ou checklist de verdade).

## T4 — CTA

Último slide.
- Fundo: **foto escurecida 70% (obrigatória)**: sangrada, com véu ink `#0B0B12` chapado a 70% (sem gradiente) e grão por cima; o resto do layout é o mesmo. `imagem: null` usa o placeholder de crepúsculo sob o mesmo véu, com aviso.
- Headline de convite com a dupla display + serifada laranja.
- Pill CTA: fundo laranja, texto ink, Inter Tight 900 30px, cantos de 14px. Ação de palavra-comentário ("Comenta EDITAR que eu te mando…") ou salvar/compartilhar.

## Arco do carrossel (padrão 7-9 slides)

| Slide | Função | Template |
|---|---|---|
| 1 | Hook | T1 ou T1b |
| 2 | Tensão / problema | T2 |
| 3-5 | Desenvolvimento | T2 / T3 alternando |
| 6 | Virada / insight | T2c |
| 7 | Conclusão | T2 ou T3 |
| 8 | CTA | T4 |

Alternar papel ↔ ink cria o ritmo de leitura. Nunca usar o mesmo fundo em mais de 3 slides seguidos.

## Proibido

- Gradiente na capa ou no CTA; gradiente roxo→azul em qualquer lugar como fundo principal.
- Laranja `#FF5A1F` sobre papel (2.51:1).
- Mais de uma palavra serifada por slide; serifada em frase inteira de corpo.
- Texto gerado dentro da imagem de IA.
- "Arraste para o lado", "Confira", "5 dicas para…" (a seta do rodapé já faz esse papel).

## Geração de imagem

Rotina própria do otalogia, separada da do aidealab. Detalhes em `tokens.json` → `geracao_imagem`.
- Modelo: Higgsfield `gpt_image_2_5` (3 créditos) para imagens sem o Luiz (capa T1, slide 2). Com o Luiz (T1b e CTA da variante 2): `soul_2` com o Soul "Luiz ota", prompt do banco `../esteticas-editoriais.md`.
- Teto: **3 imagens por carrossel** (capa T1/T1b, slide 2 em T2 com foto e CTA T4 com foto escurecida 70%) e no máximo 9 por rodada da rotina. Acima disso, pedir aprovação.
- As 3 imagens saem da mesma família de prompt e do mesmo color grading, para o carrossel manter uma paleta só.
- Imagem sempre sem texto; color grading descrito no prompt (sombras para o ink, altas para o laranja).
- Upscale local (Lanczos + unsharp); nunca o upscaler pago. Recorte do retrato (T1b) com rembg local.


## Slide 2 com foto

A foto do slide 2 entra **inteira e sangrada** (tela toda, véu ink 35%), nunca recortada numa caixa. Texto claro por cima, cor quente #FF5A1F.


## Texturas

- **T2 (papel):** papel dobrado (dobra vertical, dobra horizontal de carta, vinco diagonal leve, amassado) em soft-light + halftone ink a 45° que cresce para o canto inferior direito (multiply). **T2c (caderno):** só o papel dobrado, sem halftone. Arquivos `motor/assets/papel-dobra.png` e `halftone.png`. No T2 com foto (slide 2) não entra.
- **T1 e T1b (capas):** trama de tecido (`motor/assets/pano.png`, soft-light 55%) por cima de tudo, foto e título, como impresso em pano.
- As texturas são procedurais: `python motor/assets/texturas.py` recria os três arquivos.

## CTA em camadas (variante 2)

- Com `recorte` no T4, o sujeito fica na frente do véu e do texto e aparece inteiro.
- Sujeito no terço de cima da foto; o texto começa abaixo dele (y 640). Texto e sujeito nunca se cobrem.
- Recorte com rembg (open-source, roda local ou em nuvem com `pip install rembg`), nunca o remover fundo do Higgsfield.


## Textura LED

**Slide 2 (tensão):** a foto passa pelo filtro LED (`motor/filtro_led.py`) na paleta da marca: mapa `#1E1410, #7A3218, #D2410F, #FF7A3D, #F5EEE4`, força 0.6 e gama 0.65 (sombras clareadas para o desenho aparecer), com retícula de pontos. Capa e CTA ficam com a foto natural.

### Lista e conclusão

Nos slides de lista (T3 com `lista`) e no slide de conclusão (o último antes do CTA), uma grade de pontos tipo painel de LED em laranja da marca (`#FF5A1F` no ink, `#D2410F` no papel), forte nas bordas e suave atrás do texto. No JSON: `"textura": "led"`. Intensidade no tema: `--tex-led: .75`.

**Slide 3 sempre com textura grain** (2026-10-05): gradiente granulado da paleta (brilho laranja num canto, apoio no oposto, grão forte) em vez da grade LED. No JSON: `"textura": "grain"` (o `compor.py` marca sozinho). Força no tema: `--tex-grain` (padrão .55).
