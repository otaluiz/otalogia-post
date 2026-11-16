# Atualizar os PDFs do Drive pelo GitHub Actions

Este fluxo usa os secrets GOOGLE_DRIVE_CLIENT_ID, GOOGLE_DRIVE_CLIENT_SECRET e GOOGLE_DRIVE_REFRESH_TOKEN do repositório. Não extrai credenciais para o agente. A auditoria também roda no push do workflow/script; a atualização de PDFs é somente manual. Não publica conteúdo do Instagram.

1. Suba o workflow `.github/workflows/dm-pdfs-drive.yml` e `motor/dm_drive.py` ao repositório. No GitHub Actions selecione **DM PDFs - auditar ou atualizar Drive**, **Run workflow**, modo `auditar`.
2. Baixe o artifact da execução. Ele contém `auditoria.json`, as filas pendentes dos dois perfis e os PDFs originais de 07-Iscas-DM. Contém dados editoriais privados: compartilhe somente com a equipe autorizada. Retenção: 14 dias. O audit não altera arquivos nem permissões.
3. Compare as promessas dos posts com os materiais existentes. Redesenhe os guias completos com o template em `motor/PDF.md` e revise todas as páginas. Não crie material a partir de resumo de slides.
4. Inclua os PDFs finais e um manifesto revisado em `iscas/entrega-pdfs/`. Preencha IDs, nomes e MD5 originais a partir da auditoria real. Não invente IDs ou hashes.
5. Execute o mesmo workflow em modo `atualizar`, indicando o manifesto. O script verifica todo o lote, baixa backups, compara checksums e atualiza os arquivos existentes preservando IDs, nomes, pastas e permissões. Não cria novos PDFs no Drive e não altera legendas, posts ou catálogo Supabase.
6. Confira o artifact com `atualizados.json`, backups e o resultado. Em uma falha no meio da atualização, consulte o relatório parcial: o lote não é uma transação e os arquivos já atualizados não são revertidos automaticamente. Faça nova auditoria antes de repetir.

Formato do manifesto (substitua os campos pelo resultado real):

```json
{"arquivos":[{"perfil":"aidealab","arquivo":"AIDEALAB_SITE.pdf","drive_id":"ID_REAL_DO_PDF","nome_drive":"NOME_EXATO_NO_DRIVE.pdf","md5_original":"MD5_DA_AUDITORIA","revisado":true}]}
```

Cada PDF deve existir dentro da pasta do manifesto e usar assinatura apenas aidealab. `revisado: true` registra revisão editorial feita antes do envio. Fontes/diagramação são verificadas na engine; o envio verifica estrutura básica, marca, destino e integridade, sem substituir a revisão visual. PDFs novos sem ID existente precisam de entrega editorial própria; este fluxo não os cadastra automaticamente.

Como os dois repositórios têm o mesmo fluxo e acessam as duas bibliotecas, execute por um só repositório de cada vez. A concorrência do Actions vale apenas dentro do próprio repositório; o checksum é revalidado antes de cada atualização. Mudanças simultâneas por outro editor ainda podem ocorrer entre a leitura e a gravação: use uma janela de manutenção sem outros editores.
