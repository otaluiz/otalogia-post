# Roteiro de carrosséis — otalogia

Guia de temas para a rotina de carrosséis. Cada linha vira um `carrossel.json` no motor `motor/` (submódulo carrossel-engine; ver `motor/carrossel.schema.md`; tema da marca em `design-system/tema/`; render: `python ../../motor/render.py carrossel.json png --tema ../../design-system/tema`, a partir da pasta do carrossel). Atualizar a seção "Já publicados/produzidos" a cada carrossel novo, para não repetir tema nem pose do T1b.

Atualizado em 2026-10-04.

## Regras fixas de produção

- Cadência: 3 carrosséis por semana (qua, sex, sáb), dentro do plano de 3 carrosséis + 2 Reels.
- Copy escrita com a skill `marketing-skills:copywriting` e revisada com `humanizer:humanizer` (slides e legenda).
- Hook de no máximo 10 palavras. Uma ideia por slide, virada no meio, CTA de palavra-comentário.
- Arco: capa (T1 ou T1b) → slide 2 com foto inteira → miolo alternando papel (T2/T2c) e ink (T3) → CTA (T4 com foto escurecida 70%).
- 3 imagens por carrossel no Higgsfield `gpt_image_2_5`: capa, slide 2 e CTA, todas com o mesmo color grading (sombras ink, luz laranja), sempre sem texto.
- T1b: personagem @luizota, gerado no Soul 2.0 (`soul_2` + Soul "Luiz ota"), capa e CTA com estéticas diferentes do banco `design-system/esteticas-editoriais.md`. Pose e cenário sempre diferentes do carrossel anterior: olho de peixe de cima, mão vindo pra câmera, estúdio de fundo liso colorido, objeto surreal. O texto fica atrás do recorte.
- Alternar a capa: um carrossel em T1 (foto cinematográfica sem o Luiz), o seguinte em T1b (com o Luiz).
- Pilares no mês: Descoberta, Autoridade, Identificação, Opinião e Conversão (Conversão no máximo 10% do feed).

## Já produzidos

| # | Pasta | Série | Hook | Capa | Pilar | CTA | Fila | Status |
|---|---|---|---|---|---|---|---|---|
| 1 | site-invisivel | Diagnóstico | Seu site não é feio. Ele é *invisível*. | T1 (deserto, figura com notebook) | Descoberta | SITE | — | aprovado |
| 2 | mesma-pergunta | Planta | A mesma pergunta *o dia inteiro*. | T1b (olho de peixe, celulares pendurados) | Autoridade | WHATS | — | aprovado |
| 3 | antes-e-depois-post | Antes e Depois | Esse post tinha tudo. Menos um motivo pra *parar*. | T1b (E1 olho de peixe, caneca laranja) | Autoridade | REFAZ | 3 | aprovado |
| 4 | ia-sem-hype | IA sem hype | Todo mundo usa IA. Pouca gente sabe *cortar*. | T1 | Opinião | EDITAR | 4 | aprovado |
| 5 | custo-real | Custo Real | Quanto custa parar de responder *na mão*? | T1 | Autoridade | CUSTO | 5 | aprovado |
| 6 | planta-pedido | Planta | Quantas mãos seu pedido passa até *sair*? | T1b (spray desenhando setas) | Descoberta | PLANTA | 6 | aprovado |
| 7 | vitrine-esquecida | Diagnóstico | A vitrine que você esqueceu *aberta*. | T1 | Descoberta | GOOGLE | 7 | aprovado |
| 8 | ia-nao-faz-isso | IA não faz isso | A IA acertou tudo. E ficou *sem graça*. | T1b (câmera antiga) | Opinião | OLHO | 8 | aprovado |
| 9 | do-zero-ao-ar | Do Zero ao Ar | Um site no ar em um dia. Dá, com *limite*. | T1 | Autoridade | SITE | 9 | aprovado |
| 10 | preciso-de-site | Pergunta do Dono | Preciso de *site*? | T1b (E11 telefone de fio) | Identificação | DUVIDA | 10 | aprovado |
| 11 | tarde-por-semana | Custo Real | Isso pode estar te custando uma tarde por *semana*. | T1 (mesa sozinha no salar, areia escorrendo) | Identificação | TEMPO | 11 | aprovado |
| 12 | logo-sistema | Antes e Depois | O logo é a menor parte da sua *marca*. | T1b (carimbo em branco pra lente, fundo creme) | Autoridade | MARCA | 12 | aprovado |
| 18 | react-awwwards | Referência | Nenhum site de prêmio nasce do *zero*. | T1 (salão escuro com esculturas de luz) + 5 T5 (React Bits, Aceternity UI, Magic UI, Motion, GSAP) | Autoridade | REACT | 13 | aprovado |
| 15 | postar-todo-dia | Pergunta do Dono | Preciso postar todo *dia*? | T1b (E8 jornal em branco, fundo marinho com pincelada laranja) | Identificação | POSTAR | 14 | aprovado |

Poses de T1b já usadas: olho de peixe de cima com celulares (#2); mão estendida pra câmera, agachado (CTA #2); olho de peixe com caneca laranja (#3); cadeira flutuando sobre névoa (CTA #3); spray desenhando setas (#6); sentado na beira da laje, E6 (CTA #6); câmera antiga de frente (#8); sentado em laje flutuante com câmera (CTA #8); telefone de fio, E11 (#10); banqueta em estúdio marinho, E7 (CTA #10); lendo jornal em branco com mala, E8 (#15); atrás do quadro-negro em branco com giz, E12 (CTA #15); carimbo em branco pra lente, contra-plongée em creme (#12); varal com cartelas de cor contra céu azul, E9 (CTA #12). Banco de estéticas: `design-system/esteticas-editoriais.md`.

## Próximos (backlog, em ordem)

Pares de validação: cada par tem um T1 e um T1b.

| # | Série | Tema | Hook sugerido | Capa | Pilar | CTA |
|---|---|---|---|---|---|---|
| 14 | Diagnóstico | O caminho do Instagram até o WhatsApp tem atrito demais (link na bio, menu, formulário) | Seu cliente *desiste* antes de te chamar. | T1 | Descoberta | LINK |
| 16 | IA sem hype | Prompt bom não salva briefing ruim | A IA não sabe o que você *quer*. | T1 | Opinião | BRIEFING |
| 17 | Planta | Agenda no caderno e retorno que nunca acontece (lembrete automático) | O cliente voltaria. Só faltou *lembrar*. | T1b (E3 miniatura sobre agenda gigante em branco; CTA E10 cabeça-objeto) | Autoridade | AGENDA |
| 13 | Case aidealab | Antes e depois de um cliente aidealab | O que mudou quando o site *começou a vender*. | T1 | Conversão | AIDEALAB |

Notas:
- Os hooks do backlog são ponto de partida e passam pela copywriting + humanizer antes de virar slide.
- Números citados em slide (prazo, custo, tempo) precisam vir de caso real ou ser marcados como exemplo. Nada de estatística inventada.
- O #13 depende de um case com autorização do cliente.
