# contrib-svg-service (GitHub-only)

Serviço **100% GitHub** para gerar e publicar um SVG moderno, sofisticado e futurista das suas contributions, usando a paleta:

- Background `#1e1e1e`
- Cor principal `#E65729`
- Branco `#ffffff`

Aqui não existe servidor externo. O próprio **GitHub Actions** gera o SVG em cron e o **GitHub Pages** (ou `raw.githubusercontent.com`) serve o arquivo estático.

## Como funciona

1. O workflow roda diariamente.
2. Ele chama a GitHub GraphQL API e gera um SVG **linha apenas (sem preenchimento)**.
3. O SVG é commitado em `assets/contributions.svg`.

## Setup rápido

1. Crie o repositório e coloque esses arquivos.
2. Crie um secret:
   - `GH_PAT` com um token pessoal.
   - Escopos mínimos:
     - Público: `read:user`
     - Privado (se quiser contributions privadas): `repo` + `read:user`
3. Ative o GitHub Pages:
   - Settings → Pages → Deploy from a branch → `main` / `/`
4. Aguarde o cron rodar ou execute manualmente o workflow.

## URLs para usar o SVG

Via GitHub Pages:
```
https://SEU_USUARIO.github.io/SEU_REPO/assets/contributions.svg
```

Via raw:
```
https://raw.githubusercontent.com/SEU_USUARIO/SEU_REPO/main/assets/contributions.svg
```

## Embutir no README

```markdown
![Contributions](https://SEU_USUARIO.github.io/SEU_REPO/assets/contributions.svg)
```

## Customização

Edite os valores em `scripts/generate_svg.py`:
- `BG`, `STROKE`, `TEXT`
- `width`, `height`, `padding`
- fontes e detalhes visuais

## Executar localmente

```bash
export GITHUB_TOKEN="ghp_..."
python scripts/generate_svg.py --user DonatoReis --out assets/contributions.svg
```

