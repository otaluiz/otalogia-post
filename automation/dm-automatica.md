# Automação oficial de DM: @otalogia + @idea_lab7

Esta função usa somente a Meta Instagram Messaging API e foi implantada no projeto Supabase **aidealab** no endpoint:

`https://jrfjjpxjkpvuvvycyryj.supabase.co/functions/v1/ig-dm-isca`

## Gatilhos

- Comentário em Reel/carrossel com palavra exata -> **uma única resposta privada** com link do PDF (sem exigir follow).
- DM enviada espontaneamente pelo usuário com palavra exata -> responde com link do PDF.
- Não envia mensagens em massa nem faz follow-up sem interação do usuário.
- Não responde quando não existe documento publicado, nem mistura links entre contas.
- Eventos HMAC são validados e deduplicados em `public.ig_dm_events`.

## De onde vêm as palavras e PDFs

- @otalogia: `https://raw.githubusercontent.com/otaluiz/otalogia-post/main/iscas/links.json`
- @idea_lab7: `https://raw.githubusercontent.com/otaluiz/aidealab-post/main/iscas/links.json`
- O script `automation/dm_preparar.py` (otalogia) ou `agente aidealab/automation/cloud/dm_preparar.py` (aidealab) lê as pastas do Drive e gera as iscas.
- PDFs: `Clientes/<marca>/07-Iscas-DM`. Links existentes preservados, cache de 5 minutos.

## Configurar antes de ativar as contas publicamente

Cada conta de Instagram precisa ser **profissional** e estar autorizada no app da Meta com permissões de mensagens e comentários, com Advanced Access quando aplicável.

No painel Meta, configure webhook para o endpoint acima no objeto Instagram com os campos **comments** e **messages**. Não assine eventos de terceiros desconhecidos. Teste com usuário de teste e depois com usuário externo autorizado.

Secrets da função (não armazenar no GitHub em texto puro):

| @otalogia | @idea_lab7 | Descrição |
|---|---|---|
| `IG_TOKEN` | `IG_TOKEN_AIDEALAB` | Access token de mensagens da conta |
| `IG_ID_OTALOGIA` | `IG_ID_AIDEALAB` | Instagram professional user ID |
| `IG_APP_SECRET` | `IG_APP_SECRET_AIDEALAB` | Segredo do app emissor do webhook (somente se apps distintos; mesmo app pode usar o mesmo segredo) |
| `IG_VERIFY_TOKEN` | `IG_VERIFY_TOKEN_AIDEALAB` | Verify token para validação inicial |
| `IG_GRAPH` | `IG_GRAPH_AIDEALAB` | `facebook` caso o token use Facebook Login, omitido para Instagram Login |

Também requer o Supabase padrão: `SUPABASE_URL` e `SUPABASE_SERVICE_ROLE_KEY` para a deduplicação.

**Importante:** o webhook atual já está implantado, mas isso **não significa** que os webhooks de ambas as contas, o acesso avançado e os tokens estejam ativos. Verifique e teste o fluxo ponta a ponta antes de incluir promessas de envio automático em posts publicados.

Documentação de limites: apenas uma resposta privada por comentário dentro de até 7 dias; uma conversa adicional somente após nova interação do usuário, respeitando janela de 24h. Enviar link de arquivo é mais estável que anexo direto como primeira resposta privada.

## Diagnóstico

- Supabase > Edge Functions > `ig-dm-isca` > Logs.
- GitHub Actions > `entregar.yml`: PDFs e palavras são preparados na sincronização do Drive.
- Drive > `07-Iscas-DM`: conferir o PDF com visualização pública.
- `iscas/links.json`: checar se a palavra está publicada na branch main.

Se o usuário comentar uma palavra que não está no mapa, não enviará nenhuma resposta.
