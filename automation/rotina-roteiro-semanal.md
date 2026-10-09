# Rotina de segunda: varredura do nicho + roteiro da semana (@otalogia)

Roda toda segunda às 8h (BRT) numa sessão nova na nuvem. Às 6h, o workflow `instagram-pesquisa` já coletou dados novos no Apify e gravou em `pesquisa/instagram/dados/` na main.

## Passos

1. **Repositório atualizado.** Trabalhe no clone de `otaluiz/otalogia-post` e faça `git pull origin main`. Confira em `git log -3 -- pesquisa/instagram/dados` se a coleta é de hoje. Se não for, dispare o workflow `instagram-pesquisa.yml` na main (GitHub MCP `actions_run_trigger`, `run_workflow`), espere terminar (`actions_list`, de 60 em 60 s, no máximo 25 min) e faça o pull de novo. Se a coleta falhar, siga só com a pesquisa web e avise no roteiro.
2. **Leia o contexto** (só o necessário):
   - `pesquisa/instagram/campanha-10k.md`: meta, fase do mês, cadência, alavancas, KPIs.
   - `roteiro-carrosseis.md`: regras de produção, carrosséis já produzidos e backlog (não repetir tema).
   - O roteiro mais recente em `roteiros/`, para dar continuidade e não repetir gancho.
3. **Varredura do nicho** com as skills de https://github.com/sergebulaev/instagram-skills (clone no scratchpad): `ig-audience-insights` sobre os JSON (perfil @otalogia: seguidores e posts da semana com curtidas, comentários e views; hashtags: ranking de engajamento, formato e formato do gancho) e `ig-hook-extractor` nos 3 posts do nicho que mais engajaram. Complete com WebSearch (2 a 3 buscas): tendências e assuntos da semana em sites, automação, IA e Instagram para pequenos negócios no Brasil, mais datas sazonais dos próximos 14 dias. Não invente números: se a amostra for fraca, diga que é fraca.
4. **Escreva o roteiro da semana** com `ig-content-planner`, `ig-carousel-planner` e `ig-caption-writer`, seguindo a cadência da fase atual da campanha:
   - **Carrosséis (qua, sex, sáb):** priorize a fila pronta do `roteiro-carrosseis.md` (status aprovado ou rascunho, ainda não publicados) e encaixe tema novo quando a tendência da semana pedir. Para tema novo: série, hook de até 10 palavras, texto slide a slide, pilar, palavra do CTA e legenda (primeiros 125 caracteres com o gancho), além de 3 a 5 hashtags. Acrescente os temas novos ao backlog do `roteiro-carrosseis.md`.
   - **Reels (quantidade da fase):** gancho em texto na tela (0 a 2 s), roteiro marcado por segundo (fala + o que aparece), duração alvo, texto na tela, legenda, hashtags e se vai como Trial Reel.
   - Uma Collab sugerida (tipo de conta + ideia do post) quando a fase pedir.
   - Revise todo o texto com a skill `humanizer` (se não houver, com `ig-humanizer`).
   - Abra o roteiro com um bloco **"Placar da semana"**: seguidores (atual × semana passada × meta da fase), o post que mais rendeu e o que mudou no plano por causa disso.
5. **Salve em dois lugares:**
   - Repositório: `roteiros/AAAA-MM-DD-semana.md` (data da segunda). Faça `git add` do roteiro e do `roteiro-carrosseis.md`, commit `content: roteiro semana AAAA-MM-DD (rotina nuvem)` e push no branch da sessão (o workflow `entregar.yml` leva para a main).
   - Google Drive: não precisa de conector. Depois que o push chega à main, o `entregar.yml` (secrets `GOOGLE_DRIVE_*` do repositório) sobe todo `roteiros/*.md` novo como Google Doc para **Clientes/otalogia/03-Roteiros**, com o título `Roteiro AAAA-MM-DD-semana`.
6. **Termine** com um resumo de no máximo 8 linhas: os temas da semana, e o placar. O Doc aparece no Drive alguns minutos depois do push.

## Regras

- Não publique nada no Instagram. A rotina só planeja.
- Nada de estatística inventada em slide ou legenda (regra do roteiro).
- Sem cripto, frase motivacional ou sorteio (regra da campanha).
- Não altere `motor/`, `design-system/` nem os workflows.
