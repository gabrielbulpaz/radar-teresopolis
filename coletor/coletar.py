"""Baixa as notícias publicadas no site da Câmara Municipal de Teresópolis.

O site oficial (camarateresopolis.com.br) roda em WordPress, que expõe uma API
pública de leitura em /wp-json/wp/v2/posts. É de lá que vêm os relatos das
sessões, com projetos citados, votações e vereadores que discursaram.

Uso:
    python coletor/coletar.py                 # desde 01/01/2025 (início da legislatura)
    python coletor/coletar.py --desde 2026-01-01

Resultado: dados/brutos/noticias.json (lista de notícias, mesclada por id).
Só usa a biblioteca padrão do Python.
"""

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://camarateresopolis.com.br/wp-json/wp/v2/posts"
CAMPOS = "id,date,modified,link,title,content"
POR_PAGINA = 100
PAUSA_SEGUNDOS = 1.0  # gentileza com o servidor da Câmara
USER_AGENT = "RadarTere/1.0 (acompanhamento cidadao da Camara de Teresopolis)"

RAIZ = Path(__file__).resolve().parent.parent
SAIDA = RAIZ / "dados" / "brutos" / "noticias.json"


def baixar_pagina(pagina: int, desde: str):
    """Retorna (lista_de_posts, total_de_paginas). Lista vazia = acabou."""
    params = {
        "per_page": POR_PAGINA,
        "page": pagina,
        "after": f"{desde}T00:00:00",
        "orderby": "date",
        "order": "asc",
        "_fields": CAMPOS,
    }
    url = f"{API}?{urllib.parse.urlencode(params)}"
    req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "application/json"})
    for tentativa in range(3):
        try:
            with urllib.request.urlopen(req, timeout=60) as resp:
                total = int(resp.headers.get("X-WP-TotalPages", "1") or 1)
                return json.loads(resp.read().decode("utf-8")), total
        except urllib.error.HTTPError as erro:
            # O WordPress responde 400 quando a página pedida passa do fim.
            if erro.code == 400:
                return [], pagina - 1
            if tentativa == 2:
                raise
        except urllib.error.URLError:
            if tentativa == 2:
                raise
        time.sleep(5 * (tentativa + 1))
    return [], 0


def simplificar(post: dict) -> dict:
    return {
        "id": post["id"],
        "data": post.get("date", "")[:10],
        "modificado": post.get("modified", ""),
        "link": post.get("link", ""),
        "titulo": (post.get("title") or {}).get("rendered", ""),
        "html": (post.get("content") or {}).get("rendered", ""),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--desde", default="2025-01-01", help="data inicial AAAA-MM-DD (padrão: 2025-01-01)")
    args = parser.parse_args()

    existentes = {}
    if SAIDA.exists():
        for n in json.loads(SAIDA.read_text(encoding="utf-8")):
            existentes[n["id"]] = n

    pagina, total, novas = 1, 1, 0
    while pagina <= total:
        posts, total = baixar_pagina(pagina, args.desde)
        if not posts:
            break
        for p in posts:
            n = simplificar(p)
            antigo = existentes.get(n["id"])
            if antigo is None or antigo.get("modificado") != n["modificado"]:
                novas += 1
            existentes[n["id"]] = n
        print(f"página {pagina}/{total}: {len(posts)} notícias", file=sys.stderr)
        pagina += 1
        time.sleep(PAUSA_SEGUNDOS)

    SAIDA.parent.mkdir(parents=True, exist_ok=True)
    lista = sorted(existentes.values(), key=lambda n: (n["data"], n["id"]))
    SAIDA.write_text(json.dumps(lista, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(lista)} notícias salvas ({novas} novas ou alteradas) em {SAIDA}", file=sys.stderr)


if __name__ == "__main__":
    main()
