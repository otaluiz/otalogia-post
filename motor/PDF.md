# PDF editorial junto do conteúdo

Os dois motores usam o mesmo template `aidealab-azul-laranja-v1`: assinatura somente **aidealab**, navy #0A0E16, azul #6EC9F7 e laranja #FF5A1F. Fontes locais incorporadas no HTML/PDF, com licenças em `pdf/fonts/`; não depende de Google Fonts ou do Drive para diagramar.

## Fluxo padrão

1. Consulte `iscas/categorias.json` e o verificador de categorias antes de escrever. Reutilize o guia canônico quando a categoria já estiver coberta.
2. Para um novo guia, pesquise e escreva `guia/brief.md`, `guia/pesquisa.md` e `guia/conteudo.md` junto do conteúdo. O guia é editorialmente independente do feed. Não gere a redação a partir dos slides ou da legenda.
3. Escreva `guia/guia.json` seguindo `pdf/exemplo-guia.json`. Campos obrigatórios: `titulo`, `subtitulo`, `categoria`, `paginas` e `fontes`. Cada página tem `titulo` e pelo menos um de `texto` (parágrafos separados por duas quebras), `itens`, `recursos` (nome/url/descricao) ou `codigo`; `dica` é opcional. Referências têm `titulo` e `url` HTTP(S). Use fontes verificadas; o motor valida a estrutura, não a veracidade ou disponibilidade dos destinos.
4. Rode o comando de metadata habitual: ele cria **png/guia.pdf**, **png/guia.html** e **guia/previews/pagina-NN.png**, além de registrar `material_pdf` no metadata. Para conteúdo novo sem fonte de guia ou referência de reuso, falha com mensagem de correção. Carrosséis legados que já têm metadata continuam funcionando sem fonte de guia; posts publicados não são alterados.
5. Confira **todas** as páginas em `guia/previews/`. O motor bloqueia exportação que ultrapassa rodapé/largura e mantém o PDF anterior quando o render falha. Se não couber, divida o conteúdo em páginas menores. Evite sumários com títulos muito longos ou capítulos demais; o mapa também é validado.
6. Inclua guia, previews e PDF no commit do conteúdo. `upload_drive.py` / `upload_carrosseis.py` já enviam os arquivos de `png/` com o rascunho, junto dos slides. Nenhum upload ou publicação acontece durante a geração local. O arquivo fica no rascunho em 04-Carrosseis; não é automaticamente cadastrado em 07-Iscas-DM ou no Supabase.
7. Revise e aprove o conteúdo antes de distribuir. A criação do arquivo não configura `dm`, não cria palavra-chave e não promete entrega. Mantenha as regras de aprovação e catálogo privado de `DM-EDITORIAL-PREMIUM.md`.

## Fonte externa ou reuso

No `meta` do `carrossel.json`, use uma destas configurações (caminhos relativos ao carrossel):

```json
{"guia": {"fonte": "guia/guia.json"}}
```

```json
{"guia": {"reutilizar": "../../../../../iscas/sites/guia.pdf"}}
```

Ajuste o caminho real no seu projeto. O PDF reutilizado precisa já existir e ter sido aprovado no template atual. Ele é copiado para a entrega; sua categoria e URL de distribuição continuam sendo as canônicas, sem novo cadastro. O motor não consegue atestar a aprovação editorial de um arquivo reutilizado.

## Reels e geração avulsa

O render também funciona para Reels e outros conteúdos, sem exigir imagens de carrossel:

```sh
python motor/guia_pdf.py caminho/do/conteudo/guia/guia.json --saida caminho/do/conteudo/guia.pdf --previews caminho/do/conteudo/guia/previews
```

Na produção de Reels, inclua o PDF e a fonte na mesma entrega e registre o material no metadata do Reel, preservando cliente/handle do post. A assinatura do PDF é aidealab em ambos os perfis. O exemplo de duas páginas de conteúdo demonstra o schema; guias finais devem ter profundidade compatível com o problema, conforme o padrão editorial.

## Ambiente e validação

Instale `playwright` e `pypdf`. Use Chromium instalado no sistema ou `PDF_CHROMIUM_EXECUTABLE=/caminho/do/chromium`; se não houver, instale o navegador com `python -m playwright install chromium`. Não desative TLS nem validações de download. A instalação padrão dos motores já inclui pypdf. PDF requer navegador em execução apenas durante o render.

```sh
python -m unittest discover -s motor/tests -p 'test_guia_pdf.py'
```

Os testes exercitam os dois caminhos: PDF novo e reutilização, falhas de conteúdo/layout, preservação de publicação e integração com metadata.
