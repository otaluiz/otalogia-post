# DM automática das iscas (só para quem segue)

Função `supabase/functions/ig-dm-isca` (projeto Supabase **aidealab**), já publicada em:
`https://jrfjjpxjkpvuvvycyryj.supabase.co/functions/v1/ig-dm-isca`

## Fluxo
1. Alguém comenta a palavra (ex.: BRIEFING) num post/Reel → responde no comentário "Te mandei no direct 📩" e manda DM com botão **Já te sigo ✅**.
2. Tocou no botão (ou mandou a palavra no direct) → confere `is_user_follow_business`.
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

## Manutenção
- O token dura 60 dias. Renove antes de vencer: `GET https://graph.instagram.com/refresh_access_token?grant_type=ig_refresh_token&access_token=<IG_TOKEN>` e troque o secret.
- Logs de erro: Supabase > Edge Functions > ig-dm-isca > Logs.
- Para desligar: remova o webhook no app da Meta.
