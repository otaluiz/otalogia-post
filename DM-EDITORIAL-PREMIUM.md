# PADRÃO EDITORIAL OBRIGATÓRIO — guias para entrega por DM
Versão 2 • 12/11/2026 • Aplica-se a @idea_lab7 e @otalogia

## Separar as entregas
O conteúdo de feed (Reels/carrossel) é a chamada de atenção e introdução. O PDF é um **produto editorial autônomo**: pesquisa independente, aprofundamento real, tutoriais, exemplos, quadros, gráficos e fontes. NÃO copiar, expandir mecanicamente ou resumir os textos dos slides/legendas. Um documento que repete slides, contém dicas genéricas ou só 1–2 páginas é reprovado.

## Pesquisa ANTES de escrever
1. Definir público, problema, objetivo e resultado concreto prometido pelo material, escolhendo um recorte forte e útil para o tema do próximo post.
2. Pesquisar preferencialmente documentação primária e pesquisas metodologicamente claras. Conferir título, autor/instituição, URL, data e escopo. Preferir atualizações recentes; manter conteúdo atemporal se dados novos não forem necessários.
3. Criar arquivo `pesquisa.md` junto do material com pelo menos 3 fontes pertinentes (quando existem), nota de evidência para cada afirmação factual relevante, conflitos, limitações e data de verificação. Sem fontes suficientes, identificar lacunas e **não inventar**.
4. Desenvolver análise independente em português brasileiro, com minúcia: definições, por que importa, passo a passo executável, exemplos contextualizados, variações, armadilhas, métricas e diagnóstico, checklist, estudo ilustrativo rotulado como tal, referências.
5. Diferenciar fatos verificados, hipóteses, boas práticas recomendadas, opinião editorial e exemplos fictícios. Nunca alegar resultados não medidos.

## Documento premium e independente
- Alvo editorial: 8–15 páginas de conteúdo útil, não páginas vazias; pode variar conforme complexidade real do tema. Ideal para leitura no celular (A4 vertical bem contrastado, fonte de corpo confortável), clicável, sem clipping.
- Abertura editorial impactante; sumário ou mapa; conceitos; procedimento; casos e diagramas; templates preenchíveis; métricas; plano de ação; fontes ao final.
- Identidade **otalogia**: ink #0B0B12, papel #ECE6DA, laranja #FF5A1F (escuro) / #D2410F (papel), Inter Tight, Instrument Serif e JetBrains Mono; direção editorial de engenharia, sem gradiente.
- Identidade **aidealab**: consultar tokens e guias do próprio repositório (navy/ciano da marca, layout editorial), nunca reaproveitar indiscriminadamente a paleta da otalogia.
- Referências e exemplos devem estar dentro do documento; hyperlinks funcionais, numeração e cabeçalho/rodapé consistentes.
- Exportar PDF, renderizar **todas as páginas** em imagens, verificar visualmente cortes, sobreposições, acentos, fontes, contraste e excesso de áreas em branco. Corrigir até passar. Fazer checagem de links e conteúdo.

## Gatilhos e publicação
- Não gerar PDF automaticamente a partir do metadata, slides ou legenda. O script antigo `dm_preparar.py` foi removido.
- Para cada candidato, produzir `guia/brief.md`, `guia/pesquisa.md`, `guia/conteudo.md` e `guia/<slug>.pdf` revisado. O PDF novo só entra em `07-Iscas-DM` após aprovação editorial explícita.
- Publicar `iscas/links.json` com palavra-chave **somente depois** do PDF final estar acessível no Drive e visualmente aprovado, e o webhook Meta validado. Não prometer envio automático antes disso.
- O post aprovado não deve ser publicado com CTA prometendo PDF ainda ausente; alterar a CTA ou reter o post.
- O conteúdo da fila e os posts já publicados NÃO devem sofrer alteração automática de legenda; aprovação humana é preservada.
- Para testar um novo formato, criar **apenas um piloto** e revisá-lo antes de gerar em lote.
- Não apagar PDFs válidos preexistentes sem identificar se são parte de campanha ativa.
