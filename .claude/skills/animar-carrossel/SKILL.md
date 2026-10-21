---
name: animar-carrossel
description: |
  Anima um carrossel da otalogia (carrossel.json do motor/) e exporta um MP4 por slide, com motion por tipo de
  slide e partículas ASCII 3D. Use quando pedirem "animar carrossel", "carrossel com motion", "versão em vídeo do
  carrossel" ou ao montar um carrossel do roteiro-carrosseis.md que vai sair animado. Não gera copy nem imagem:
  parte de um carrossel já pronto (estático aprovado).
metadata:
  version: "0.1.0 (protótipo)"
---

# animar-carrossel

Transforma um carrossel pronto do motor (`carrosseis/<slug>/carrossel.json`) em vídeos: um MP4 1080x1440 por slide
(o Instagram aceita vídeo dentro do carrossel) e uma `previa.mp4` com todos em sequência. O layout é o mesmo do PNG
estático: a animação só mexe em quando e como cada peça entra.

## Como rodar

A partir da pasta do carrossel:

```
python ../../motor/motion/render_motion.py carrossel.json motion --tema ../../design-system/tema [--dur 10] [--fps 30] [--slides 1,8]
```

- Requer o mesmo ambiente do `render.py` (Playwright/Chromium, fontes do tema) e `ffmpeg` no PATH.
- Cada slide tem 10 s (padrão). Leva cerca de 1,5 min por slide. Para testar, use `--slides 1` primeiro.
- Saída: `motion/slide-NN.mp4` + `motion/previa.mp4`. Não versionar os MP4 no git (são pesados): sobem para o Drive
  junto com os PNG.

## O que o motion faz (motor/motion/motion.js)

Tudo é pausado e dirigido quadro a quadro (`Motion.seek(t)`), sem relógio real e sem aleatório: a mesma entrada
gera sempre o mesmo vídeo.

| Peça | Movimento | Quando |
|---|---|---|
| Foto (capa, slide 2, CTA) | entra do escuro e faz zoom lento 1.08 → 1.00 | o slide inteiro |
| Recorte (sujeito) | paralaxe leve, sobe 18px e reduz 6% | o slide inteiro |
| Topo e rodapé | fade | 0,1 s |
| Título (`display`) | cada linha sobe de trás de uma máscara, em cascata | 0,3 s + 0,13 s por linha |
| Frase manuscrita (`emocao`) | se escreve da esquerda pra direita | depois do título |
| Marca-texto `{palavra}` | a caixa laranja varre por trás da palavra | junto do título |
| Lista | itens em cascata da esquerda | depois do título |
| Pílula do CTA | entra com overshoot e pulsa até o fim do vídeo | depois da frase |
| Partículas ASCII 3D | slides com foto: campo de brasas em caracteres subindo em perspectiva (laranja da marca, `screen`). Slides de texto escuro (T3): esfera de caracteres girando no espaço vazio do canto. Papel (T2/T2c): sem partículas | o slide inteiro |

Os caracteres das partículas vêm de uma rampa (` .,:;-=+*#%@`) pela profundidade: o que está perto fica maior, mais
denso e mais opaco. A fonte é a mono do tema (`--f-mono`).

## Arco do roteiro (roteiro-carrosseis.md) e o motion

- **Capa (T1/T1b):** brasas + zoom da foto; o título entra primeiro, a frase manuscrita fecha o hook.
- **Slide 2 (foto inteira):** mesma linguagem da capa, para não quebrar a virada de slide.
- **Miolo:** papel sem partículas (respiro); ink (T3) com a esfera de caracteres e a lista em cascata.
- **CTA (T4):** brasas + a pílula entra por último e pulsa, para o olho terminar na palavra-comentário.

## Ajustes rápidos

- Duração: `--dur` (padrão 10 s por slide; o Instagram toca cada vídeo do carrossel até o fim).
- Sem partículas num slide: `Motion.init({particulas: false})` (no render, editar a chamada).
- Tempos e curvas ficam no topo de cada bloco em `motor/motion/motion.js`; o tecido do T4 e as texturas do tema
  continuam como no PNG.

## Formato novo: HyperFrames (motor/hyperframes/)

Mesmo formato do carrossel animado da aidealab (W43): uma composição HTML/GSAP por carrossel, 6 s por slide, motion
suave (tudo assenta até ~3,5 s e só o ambiente respira até o fim, para o loop do Instagram ficar limpo). Cada slide
ganha um gesto próprio além da entrada do texto: busca digitando, ponto percorrendo a lista, toque no marca-texto,
navegador com o print aproximando, pílula do CTA pulsando.

```
cd carrosseis/<slug> && python ../../motor/hyperframes/gerar.py carrossel.json   # cria motion/index.html
bash motor/hyperframes/render.sh carrosseis/<slug>    # gera carrosseis/<slug>/motion/out/slide-NN.mp4 + completo.mp4
```

- `gerar.py` monta o HTML a partir do `carrossel.json` com o motion padrão de cada template e ajusta o tamanho do
  título para caber no bloco. Gestos próprios de um carrossel entram editando o `index.html` gerado (ele não
  sobrescreve um existente sem `--force`).

- `carrosseis/<slug>/motion/index.html`: só o conteúdo dos slides e a timeline. Tema (`otalogia.css`), helpers
  (`otalogia.js`: linhas, escreve, marca, lista, foto, referencia, pill) e fontes ficam em `motor/hyperframes/` e o
  `render.sh` copia para a pasta na hora, junto com os PNG do carrossel (`img/`). Nada disso é versionado.
- Dois modelos, um por tipo de capa:
  - **Personagem (T1b):** `2026-10-instagram-buscador`. Recorte por cima do título na capa (texto atrás da cabeça),
    zoom menor (1.06) para a cabeça não engolir o título; no CTA o texto fica na frente do corpo.
  - **Imagem gerada (T1):** `2026-10-desiste-antes`. Push-in maior (1.16) com a luz da cena tremulando e brasas;
    slides T5 com o navegador subindo e o print aproximando.
- Conferir antes de renderizar: `npx hyperframes@0.8.181 snapshot --at 5.5,11.5,... --no-end` dentro de `motion/`.
