# Rotina na nuvem: 1 carrossel do otalogia por rodada

Você roda sozinho, sem humano para responder. Este repositório já está clonado no workspace.

## 0. Preparar o ambiente
`bash automation/setup-cloud.sh` (instala Playwright/Chromium, rembg e OpenCV 4 em `motor/.vendor_cv4`).
Se falhar, pare e relate o erro.

## 1. Fazer o carrossel
Siga `automation/daily-carousel-prompt.txt` do início ao fim, com estas diferenças da versão local:
- Caminhos do Windows (`C:\Users\...`) não existem aqui. O backlog de rascunhos é contado pelas pastas em
  `carrosseis/` cujo `png/metadata.json` tem `"status": "rascunho"`.
- Imagens: conectores Higgsfield (`generate_image`/`generate_image_batch` + `jobs_wait`), baixe o `result_url` com curl.
  Se der 429 (rate limit), espere ~30 s e reenvie só o item que falhou.
- `compor.py` pode levar 10 min na primeira vez (modelo do rembg): rode em primeiro plano com timeout alto.
- Skills `marketing-skills:copywriting` e `humanizer:humanizer`: use se estiverem disponíveis; senão aplique as regras
  do roteiro (hook ≤ 10 palavras, sem número inventado, sem contraste "não é X, é Y", sem travessão).

## 2. Entregar
- `status: "rascunho"` no `png/metadata.json` (aprovação é humana).
- Atualize `roteiro-carrosseis.md` (linha em "Já produzidos" com a capa usada; tire o tema de "Próximos").
- `git add` da pasta do carrossel e do roteiro, commit `content: <slug> (rotina nuvem)` e `git push`.
  Não envie PNG para o Drive por MCP (base64 estoura o contexto): o PC do Luiz roda `automation/sync-drive.ps1`
  de hora em hora, puxa este commit e copia a pasta para `Clientes/otalogia/04-Carrosseis` no Drive.

## 3. Resumo final
Tema, variante, imagens geradas e créditos gastos, checagens feitas, bloqueios.
