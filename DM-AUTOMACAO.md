# Material por DM — rotina automática

Ao produzir qualquer post novo, inclua no `png/metadata.json` (carrossel) ou `metadata.json` (Reels) a configuração:

```json
"dm": {
  "palavra": "PALAVRA_UNICA",
  "titulo": "Nome útil e específico do material",
  "secoes": [ {"titulo": "Aplicação", "itens": ["Passo concreto 1", "Passo concreto 2"]} ]
}
```

A palavra deve ser única dentro deste Instagram (3–24 caracteres, sem acentos e preferencialmente uma só palavra), específica do post, e a legenda deve ter **Comente PALAVRA para receber o material gratuito em PDF por DM.** O PDF deve ensinar a executar algo útil, com passos verificáveis; nunca inventar dados. Não prometer envio se o material estiver vazio. O conteúdo também serve ao futuro gerador; a automação usa legenda/slides como fallback para posts já em fila.

O workflow `entregar.yml` chama `dm_preparar.py` depois do upload. O script lê a fila de aprovação do Drive, cria/atualiza o PDF em `Clientes/<marca>/07-Iscas-DM`, torna o material acessível por link, preserva histórico de palavras em `iscas/links.json` e atualiza **apenas** o metadata/legenda dos posts em aprovação (nunca POSTADOS). A aprovação humana continua necessária; não publica conteúdo sozinho.

Comentários e DMs são processados pelo webhook `ig-dm-isca` no Supabase, que consulta cada registro por conta. **Antes de anunciar automação pública:** configurar webhook Meta, permissões avançadas e credenciais para as duas contas; testar comentário e DM de uma conta externa. Resposta privada ao comentário limitada a uma mensagem por comentário em até 7 dias; conversas posteriores exigem nova mensagem do usuário e respeitam a janela de 24h. Falha no PDF deve bloquear publicação.

Secrets no GitHub Actions: `GOOGLE_DRIVE_CLIENT_ID`, `GOOGLE_DRIVE_CLIENT_SECRET`, `GOOGLE_DRIVE_REFRESH_TOKEN`. `DM_BRAND` é definido pelo workflow. Não commitar tokens.
