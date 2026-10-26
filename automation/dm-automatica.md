# DM automática das iscas (só para quem segue)

Função `supabase/functions/ig-dm-isca` (projeto Supabase **aidealab**), já publicada em:
`https://jrfjjpxjkpvuvvycyryj.supabase.co/functions/v1/ig-dm-isca`

## Fluxo
1. Alguém comenta a palavra (ex.: BRIEFING) → responde no comentário "Te mandei no direct 📩" e manda DM perguntando **"Você já me segue?"** com os botões **Sim, já sigo ✅** e **Ainda não**.
2. "Ainda não" → manda o botão **Seguir @otalogia** (abre o perfil) e **Pronto, segui ✅**. "Sim" ou "Pronto" (ou a palavra no direct) → confere `is_user_follow_business`; o link só sai se seguir de verdade.
   - Segue: manda o título e o link do PDF no Drive.
   - Não segue: pede o follow e manda o botão de novo.
3. Palavras e links vêm de `iscas/links.json` na main (o `entregar.yml` gera). Isca nova entra sozinha, sem novo deploy (cache de 5 min).

## Configurar uma vez
1. Conta @otalogia como **Profissional** (criador ou empresa). Em Configurações > Mensagens e respostas > Ferramentas conectadas, ligue **Permitir acesso às mensagens**.
2. Em developers.facebook.com: crie um app tipo **Business**, adicione o produto **Instagram** > "API setup with Instagram login". Gere o token da @otalogia com `instagram_business_basic`, `instagram_business_manage_messages` e `instagram_business_manage_comments`.
3. Secrets no Supabase (Project Settings > Edge Functions > Secrets):
   - `IG_TOKEN`: token de longa duração da @otalogia
   - `IG_APP_SECRET`: Instagram app secret
   - `IG_VERIFY_TOKEN`: uma senha qualquer que você inventa
4. No app, em Webhooks: Callback URL = a URL acima, Verify token = o `IG_VERIFY_TOKEN`. Assine os campos **comments**, **messages** e **messaging_postbacks**.
5. Teste com uma conta adicionada como **Instagram Tester** do app (modo desenvolvimento). Para funcionar com qualquer seguidor: troque o app para **Live** e peça Advanced Access das permissões acima na App Review da Meta.

## Token permanente (recomendado)
O token do login do Instagram vence em 60 dias. O que não vence é o token de **Usuário do Sistema** do Business Manager:
1. A @otalogia precisa estar ligada a uma **Página do Facebook** (Configurações do Instagram > Central de Contas).
2. No app da Meta, adicione o produto **Messenger > Configurações do Instagram** (API com login do Facebook) e assine o webhook do objeto **Instagram** com `comments`, `messages` e `messaging_postbacks` na mesma URL.
3. business.facebook.com > Configurações > **Usuários do sistema** > Adicionar (função Admin). Em "Atribuir ativos", dê a Página e a conta do Instagram com controle total, e o app.
4. "Gerar novo token" > escolha o app > validade **Nunca** > permissões `instagram_basic`, `instagram_manage_messages`, `instagram_manage_comments`, `pages_manage_metadata`, `pages_show_list`, `pages_read_engagement`, `business_management`.
5. Troque o token do Usuário do Sistema pelo token da Página (também não vence): `GET https://graph.facebook.com/v23.0/me/accounts?access_token=<token do sistema>` e copie o `access_token` da Página.
6. Secrets no Supabase: `IG_TOKEN` = token da Página, `IG_GRAPH` = `facebook`, `IG_APP_SECRET` = chave secreta do app (Configurações > Básico), `IG_VERIFY_TOKEN` = a senha do webhook.

## Manutenção
- Só no modo login do Instagram (sem `IG_GRAPH`): o token dura 60 dias. Renove antes de vencer: `GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=<IG_TOKEN>` e troque o secret.
- Logs de erro: Supabase > Edge Functions > ig-dm-isca > Logs.
- Para desligar: remova o webhook no app da Meta.
