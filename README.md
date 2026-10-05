# otalogia-brand

Marca otalogia: design system (`design-system/`), carrosséis (`carrosseis/`) e roteiro (`roteiro-carrosseis.md`).

## Motor de carrossel

O motor genérico (`carrossel-engine`) vem copiado em `motor/` (sem submódulo, para a rotina na nuvem clonar um repositório só); a marca entra como tema em `design-system/tema/`.

```
bash automation/setup-cloud.sh            # nuvem/Linux: Playwright, rembg, OpenCV 4
cd carrosseis/<id> && python ../../motor/compor.py carrossel.json
python ../../motor/render.py carrossel.json png --tema ../../design-system/tema
python ../../motor/metadata.py carrossel.json <ordem_fila> --tema ../../design-system/tema #tags
```

Rotinas: `automation/daily-carousel-prompt.txt` (local, Windows) e `automation/cloud-carousel-prompt.md` (nuvem).
O motor é mantido em `D:/claude/carrossel-engine`; ao mudar lá, copie os arquivos para `motor/` aqui.
