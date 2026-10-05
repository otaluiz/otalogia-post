# Estéticas editoriais — banco de composição de prompts

Use este banco quando não houver imagem de referência para o tema do carrossel. Escolha uma estética que converse com o tema, combine com a paleta e monte o prompt com o esqueleto abaixo.

Origem: referências em `Drive/Clientes/otalogia/01-Referencias/Instagram/soul-ref` (12 imagens, analisadas em 2026-10-04) e as capas já aprovadas.

## Regras de geração

- **Com o Luiz (capa T1b e CTA da variante 2):** Higgsfield `soul_2`, `soul_id` `f752ac25-65a0-4930-a628-722af0508c5b` (Soul "Luiz ota"), `aspect_ratio` 3:4, `quality` 2k. Só prompt descritivo, nunca a imagem de referência como input (ela tem o rosto de outra pessoa).
- **Sem o Luiz (capa T1, slide 2):** `gpt_image_2_5`, quality high, 2k.
- **Preservar o personagem:** sempre escrever "keep his own short dark textured hair fully visible, no hat, no glasses" (o boné e o óculos das referências escondem o cabelo e mudam a fisionomia).
- **Sem texto:** objetos que costumam vir com letra (caneca, teclado, post-it, placa, tela) precisam de "completely blank". Teclado sempre sai com letra: evitar como cenário. Se sobrar marca pequena, limpar localmente (inpaint) antes do recorte.
- **Moldura:** pedir "no black circular border, image fills the frame" quando for olho de peixe; o Soul tende a pôr vinheta preta.
- **Enquadramento do T1b camadas:** "the top of his head sits at about 40 percent of the frame height, upper part is clean empty backdrop". Mesmo assim o Soul sobe a cabeça; se precisar, completar o fundo localmente usando o recorte como máscara.
- **CTA em camadas:** pedir o Luiz no terço de cima do quadro ("he sits in the upper third, lower half is empty ground/backdrop"), porque o texto do CTA vai embaixo dele. Se vier baixo, subir a foto e estender o fundo localmente.
- **Recorte:** rembg local/nuvem, nunca o remover fundo pago do Higgsfield.
- **Pose e cenário nunca repetem** o carrossel anterior (ver "Poses já usadas" no `roteiro-carrosseis.md`).

## Paleta dentro da foto

A foto tem de soar da mesma paleta dos slides:
- Fundo de estúdio: creme papel `#ECE6DA` ou ink `#0B0B12`/azul-marinho. Azul `#2563EB` só como fundo liso forte, raro.
- Acento: laranja queimado `#FF5A1F` em um objeto ou na luz de recorte (caneca, luz no horizonte, card).
- Figurino neutro: preto, marrom, creme, cinza. Evitar amarelo, verde, rosa e estampas.
- Color grading no prompt: "deep shadows pushed to blue-black ink, warm burnt-orange highlights, natural film grain".

## Esqueleto do prompt

```
<estética>, vertical 3:4. <ação e pose do Luiz> <expressão>. Keep his own short dark textured hair fully visible, no hat, no glasses. <figurino neutro>. <cenário/fundo na paleta>. <luz>. <enquadramento para o texto>. Natural film grain. <objetos> completely blank. No text, no letters, no logos, no watermark anywhere.
```

## Estéticas

| # | Estética | Composição | Bom para | Já usada |
|---|---|---|---|---|
| E1 | Olho de peixe próximo | Lente grande-angular colada no rosto, objeto em primeiro plano (caneca, celular) | Hook provocativo, ironia | carrossel 3 (caneca laranja) |
| E2 | Olho de peixe de cima | Câmera alta, corpo encolhido, rosto olhando pra lente | Sobrecarga, rotina, "na mão" | carrossel 2 (celulares pendurados) |
| E3 | Miniatura tilt-shift | Luiz do tamanho de um boneco sobre objeto gigante (mesa, mouse, caneca) | Escala, "ferramenta" | CTA testado no teclado (saiu letra; usar objeto sem texto) |
| E4 | Mão pra lente | Contra-plongée, mão aberta enorme e desfocada em primeiro plano | CTA, convite | CTA do carrossel 2 |
| E5 | Flutuando | Sentado numa cadeira de plástico branca no ar, paisagem baixa e enevoada | CTA calmo, "sem esforço" | CTA do carrossel 3 |
| E6 | No limite | Sentado na beira de uma laje de concreto contra céu limpo, de baixo pra cima | Risco, decisão | CTA do #6 |
| E7 | Estúdio liso + banqueta | Corpo inteiro em banqueta alta, fundo liso marinho, pose relaxada | Autoridade, opinião | CTA do #10 |
| E8 | Leitor de jornal | Sentado lendo jornal em branco, mala ao lado, fundo creme, pincelada azul atrás | Bastidor, "notícia" | #15 (fundo marinho) |
| E9 | Pendurado no varal | Recorte surreal preso por prendedores num varal contra céu azul | Humor, "deixado de lado" | CTA do #12 (cartelas de cor) |
| E10 | Cabeça-objeto | Cabeça trocada por objeto do tema (cubo, tela, ícone) | Metáfora forte, opinião | — |
| E11 | Retrato de mesa | Ao telefone de fio, sentado em cadeira de escritório, flash direto | Pergunta do dono, atendimento | #10 |
| E12 | Quadro-negro | Escrevendo num quadro em branco com giz, corpo inteiro | Explicação, "simplificando" | CTA do #15 |

Quando um tema não encaixar em nenhuma, combine duas (ex.: E1 + objeto do tema) e registre a nova linha aqui.
