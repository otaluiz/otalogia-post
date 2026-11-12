# Entrega de PDFs no Instagram — apenas seguidores (12/11/2026)

## Produção / links
- Catálogo de categoria: \`iscas/categorias.json\`. Só distribuir guias com \`status: aprovado\`.
- Links de produção: \`iscas/links.json\`; palavras por categoria.
- PDFs aprovados em \`Clientes/<marca>/07-Iscas-DM\` com permissão pública por link; **a permissão do Drive não substitui a verificação de seguidor**. Como qualquer link compartilhável, quem recebeu pode reenviá-lo — não prometer DRM.
- @idea_lab7: ATENDIMENTO e RETOMA -> guia "Do lead ao cliente" (16 páginas).
- @otalogia: PERFIL e BIO -> guia "Bio que converte" (12 páginas).
- Materiais antigos da otalogia preservados: BRIEFING, CORTE, SUSTO.
- A mesma categoria pode conter até cinco PDFs aprovados; links não autorizados não devem existir.

## Interação de comentário
1. Pessoa comenta a palavra da categoria em um post/Reel.
2. Meta envia webhook \`comments\`.
3. **A primeira resposta privada NÃO contém link.** Ela pede que o usuário responda com a palavra na DM; exige opt-in para consultar User Profile API.
4. Quando o usuário responde espontaneamente, o webhook de \`messages\` fornece o Instagram-Scoped-ID (IGSID).
5. A função consulta a API oficial do perfil: \`is_user_follow_business\` para a conta que recebeu a DM.
6. **Só libera URL se o campo for literalmente \`true\`.** \`false\`, campo omitido, erro, timeout ou token inválido bloqueiam a entrega.
7. Se não segue, pede que siga o perfil correto e reenvie a palavra; o status é consultado novamente em cada tentativa, sem confiar em botão ou autodeclaração.
8. Deduplica por conta e evento em \`public.ig_dm_events\`; valida HMAC do webhook.
9. Respeita 1 private reply/comentário em até 7 dias, e janela padrão de 24 horas para novas DMs após interação.

## Interação de DM direta
Quem enviar espontaneamente **ATENDIMENTO** para @idea_lab7 ou **PERFIL** para @otalogia recebe documento diretamente se já seguir a conta e se a Meta autorizar a consulta de seguidor; caso contrário recebe apenas uma instrução ou mensagem de indisponibilidade.

## Pré-requisitos Meta — não confundir deploy com integração ativa
- App Meta com caso de uso Instagram Business (em 12/11/2026 **ainda não configurado**, requer confirmação).
- Permissões de comentários, mensagens, user profile API e app review/acesso adequados.
- Contas profissionais conectadas; Instagram IDs e tokens da conta em secrets Supabase; HMAC App Secret e verify token, IDs distintos para cada marca.
- Assinatura webhook Instagram \`comments\` e \`messages\` com callback \`https://jrfjjpxjkpvuvvycyryj.supabase.co/functions/v1/ig-dm-isca\`.
- Apenas depois do cadastro e verificação Meta, realizar dois testes reais por conta: uma conta que segue e outra que não segue.
- Se a integração estiver em modo desenvolvimento, somente usuários com funções de app/testadores autorizados poderão testar.

## Validar alterações
- Código em \`otaluiz/otalogia-post/supabase/functions/ig-dm-isca/\`.
- CI \`dm-follower-gate-tests.yml\` exercita true, false, erro, ausência de campo, sem token e falhas de rede.
- Deploy Supabase \`ig-dm-isca\` com \`verify_jwt=false\` **mas assinatura HMAC obrigatória**.
- Nenhum link de documento deve sair de resposta privada baseada apenas no comentário.
- Aprovados são compartilhados no Drive somente pelo workflow \`dm-share-guides.yml\`.
- Nunca colocar token Meta, Drive OAuth ou service_role em Git, legenda, logs ou documentação.

## Biblioteca privada e teste de seguidores (atualizado em 12/11/2026)

**Fonte de links de produção:** tabela Supabase `public.ig_dm_catalog`, protegida com RLS e sem grants a `anon` ou `authenticated`; a Edge Function consulta via `service_role` **somente após autenticar o webhook**. O GitHub público (`iscas/links.json`) guarda apenas nomes de categorias e palavras, **sem URLs**. Não volte a publicar Drive IDs ou links em arquivos públicos, commits, readmes ou legendas. A geração de novo documento exige pesquisa, revisão, aprovação, upload ao Drive e cadastro privado na tabela.

**Gate de seguidores (sem exceções):** a API oficial `is_user_follow_business` deve retornar exatamente `true` no contexto da conta Instagram que recebeu a mensagem. Comentários de pessoas que já autorizaram a User Profile API podem receber link direto depois dessa verificação; comentários sem consentimento recebem apenas resposta privada pedindo que respondam com a palavra-chave. Na DM subsequente, verificar novamente antes de entregar. Perfil false, ausente, 403, timeout ou token inválido => nunca enviar link. Usuário pode seguir e tentar de novo com a palavra. Não confiar em botões ou afirmações "já sigo".

**Testes:** `otaluiz/otalogia-post/.github/workflows/dm-follower-gate-tests.yml` faz checagem de tipos e 7 testes de falha fechada. `dm-share-guides.yml` confirma permissões públicas dos guias aprovados. Essas checagens NÃO substituem a ativação da Meta: ainda são necessários caso de uso Instagram Business, tokens e IDs da conta, assinatura dos webhooks `comments`/`messages` e teste real com conta seguidora e não seguidora. Links do Google Drive são compartilháveis depois da entrega; o bloqueio vale para a distribuição pelo bot, não DRM do PDF.
