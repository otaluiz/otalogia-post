# Automação oficial do Instagram: aplicativo API_AUTO

App Meta **API_AUTO** (ID `2124703308119813`). Esta integração não utiliza o aplicativo api-CRM e não modifica seu WhatsApp.

## Infraestrutura criada

- Supabase Edge Function `ig-dm-api-auto` (endpoint `https://jrfjjpxjkpvuvvycyryj.supabase.co/functions/v1/ig-dm-api-auto`)
- Inscrição Meta: objeto `instagram` com campos `comments` e `messages`
- Catálogo privado: `public.ig_dm_catalog`, separado por perfil e palavra-chave
- Entradas de teste: @idea_lab7 **ATENDIMENTO** ou **RETOMA**; @otalogia **PERFIL** ou **BIO**
- Filtro de seguidores: apenas resposta `is_user_follow_business === true` permite enviar link; falhas bloqueiam
- Meta App Secret sempre validado por HMAC `X-Hub-Signature-256`
- Token de verificação de webhook: segredo mantido fora do código; apenas SHA-256 no código-fonte

## Configurações necessárias (Supabase Edge Secrets)

`API_AUTO_APP_SECRET`: App Secret do API_AUTO, encontrado no painel Meta App > Configurações > Básico. **Não colocar no GitHub ou nesta conversa.**

`API_AUTO_IG_ID_AIDEALAB`, `API_AUTO_IG_TOKEN_AIDEALAB`: Instagram Professional ID + token autorizado de @idea_lab7.

`API_AUTO_IG_ID_OTALOGIA`, `API_AUTO_IG_TOKEN_OTALOGIA`: Instagram Professional ID + token autorizado de @otalogia.

`API_AUTO_IG_GRAPH_AIDEALAB` e `API_AUTO_IG_GRAPH_OTALOGIA`: definir `facebook` somente quando utilizar token emitido pelo fluxo Facebook Login; omitir para token Instagram Login.

É necessário também `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` para catálogo e deduplicação.

## Limitações que permanecem

- Produto Instagram está instalado no API_AUTO, mas o app está em modo desenvolvimento; acesso padrão vale para usuários vinculados ao app. Para público geral, verificar revisão/Advanced Access e publicação do app.
- Comentário sem conversa prévia pode não permitir consulta de perfil. A primeira resposta privada pede palavra-chave na DM. Quando a pessoa responde, a API consulta o follow. Se não segue ou a confirmação é indisponível, **nenhum link** é enviado.
- A assinatura do app e IDs distintos das duas contas são obrigatórios; sem secrets de produção o endpoint bloqueia tudo por segurança.
- O Google Drive usa links compartilháveis. O gate protege a distribuição pelo bot, não cópias do arquivo depois de enviado.

## Teste real

1. Conectar as duas contas no produto Instagram do API_AUTO e autorizar mensagens/comentários.
2. Configurar secrets do API_AUTO no Supabase.
3. Confirmar assinatura de webhook `instagram` no API_AUTO com campos `comments` e `messages`.
4. Validar webhook Meta e assinatura com evento de teste.
5. Testar com conta de usuário autorizada que segue @idea_lab7 enviando ATENDIMENTO e @otalogia enviando PERFIL, primeiro via DM direta, depois comentário.
6. Repetir com conta que não segue: não pode receber PDF.
7. Avaliar logs no Supabase e registrar o sucesso sem divulgar IDs ou mensagens privadas.

Enquanto não estiver concluído, **não alegar que as DMs já estão operacionais**.
