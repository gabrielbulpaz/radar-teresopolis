# Radar da Câmara de Teresópolis

Site gratuito que mostra o que cada vereador de Teresópolis apresenta, vota e discute, montado automaticamente a partir das notícias oficiais da Câmara Municipal.

- **Vereadores**: os 21 da legislatura 2025–2028, com quantas notícias citam cada um, os projetos de autoria e os trechos em que aparecem.
- **Projetos**: cada PL, PLC, Projeto de Resolução, Emenda à Lei Orgânica e lei citada, com a situação (aprovado, rejeitado, em comissão…) e o histórico.
- **Sessões e notícias**: linha do tempo com os vereadores e projetos de cada notícia.
- **Início**: painel com notícias por mês, assuntos e situação dos projetos; tudo clicável.
- **Interação**: busca geral, filtros por partido e tema, seguir vereadores (com aviso de novidades desde a última visita, salvo no navegador do leitor), comparar dois vereadores lado a lado e copiar link de qualquer página.

Custo: zero. Roda no GitHub Actions e é publicado no GitHub Pages.

## De onde vêm os dados

A Câmara de Teresópolis não usa o SAPL (o sistema do Interlegis com dados abertos que muitas câmaras usam) e não publica uma base de proposições. O que existe de mais estruturado é o próprio site, feito em WordPress, que expõe uma API pública de leitura:

```
https://camarateresopolis.com.br/wp-json/wp/v2/posts
```

As notícias relatam cada sessão: projetos lidos, aprovados, rejeitados, quem é autor e quem discursou. O `processar.py` lê esse texto e organiza.

**Limitações, que o site também avisa:**
- A situação de um projeto é a da notícia mais recente que o cita. Se a Câmara não noticiou a votação, o site não sabe.
- A autoria só aparece quando a notícia diz ("de autoria do vereador X", "do Executivo").
- Votos individuais (quem votou sim ou não) quase nunca saem nas notícias. Ver "Próximos passos".

## Colocar no ar (uns 10 minutos)

1. Crie uma conta no GitHub (gratuita) e um repositório novo, público, por exemplo `radar-teresopolis`.
2. Envie os arquivos desta pasta para o repositório (pelo botão "Add file > Upload files" ou com `git push`). Inclua a pasta oculta `.github`.
3. No repositório, vá em **Settings > Pages** e, em "Source", escolha **GitHub Actions**.
4. Vá em **Actions**, abra "Atualizar dados e publicar site" e clique em **Run workflow**.
5. Em poucos minutos o site estará em `https://SEU-USUARIO.github.io/radar-teresopolis/`. Depois disso ele se atualiza sozinho todo dia de manhã.

## Rodar no seu computador

Precisa só do Python 3.9 ou mais novo, sem instalar nada.

```bash
python coletor/coletar.py      # baixa as notícias desde 01/01/2025
python coletor/processar.py    # gera site/dados.js e dados/radar.json
# abra site/index.html no navegador
```

Testes: `python -m unittest discover testes`

Prévia com dados fictícios: `python testes/gerar_demo.py` e depois `python coletor/processar.py --entrada testes/demo_noticias.json --vereadores testes/demo_vereadores.json --demo --saida demo/dados.js` (copie `site/index.html` para `demo/` e abra).

Temas: a lista de palavras-chave está em `TEMAS`, no começo de `coletor/processar.py`.

## Manutenção

- **Lista de vereadores**: `coletor/vereadores.json`. Os partidos foram copiados do site da Câmara; confira se alguém trocou de partido na janela partidária de 2026. Se um suplente assumir, acrescente-o.
- **Apelidos**: se um vereador aparece nas notícias com outro nome ("Dr. Amorim", "Pastor Sandrinho"), adicione em `apelidos`. A busca ignora acentos e maiúsculas.
- **Dados abertos**: `dados/radar.json` traz tudo processado, para quem quiser reutilizar.

## Próximos passos

1. **Leis sancionadas**: o portal de atos da Prefeitura (atos.teresopolis.rj.gov.br) publica as leis; dá para cruzar com os projetos para saber quais viraram lei.
2. **Diário Oficial do Legislativo**: os PDFs em camarateresopolis.com.br/diario-oficial trazem resoluções, atos da Mesa e despesas.
3. **Votos nominais e presença**: pedir à Câmara, pela Lei de Acesso à Informação (Ouvidoria no site), as atas das sessões e a lista de proposições em formato aberto. Isso daria um registro oficial no lugar das notícias.
4. **Outras cidades**: muitas câmaras usam SAPL, que tem API própria (`/api/materia/materialegislativa/`). Lá o trabalho é bem mais fácil.
5. **Alertas**: um bot de Telegram que avisa quando surge projeto novo de um vereador.

## Neutralidade

O site mostra o que as notícias oficiais registram, sem notas, rankings de "melhor" ou "pior" vereador, nem opinião. Mantenha assim: é o que dá credibilidade a uma ferramenta como esta.
