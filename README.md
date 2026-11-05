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

## Configuração rápida

Edite `site/config.js`:
- `erroUrl`: link de um Google Forms para o botão "Encontrou um erro?". Sem ele, o botão abre uma issue no GitHub (exige conta).
- `contatoEmail`: e-mail exibido na página "Como funciona".
- `goatcounter`: código de uma conta grátis do GoatCounter, para contar acessos sem cookies.

Fotos dos vereadores (opcional): veja `site/fotos/LEIAME.md`.

Imagem de prévia de link (WhatsApp, redes): `site/og.png`. Se o endereço do site mudar, atualize as tags `og:` em `site/index.html` e `siteUrl` em `site/config.js`.

## Licenças

Código: MIT. Dados: CC BY 4.0 (cite "Radar da Câmara de Teresópolis"). Detalhes em `LICENSE`.
