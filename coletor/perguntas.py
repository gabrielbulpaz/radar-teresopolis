"""Perguntas do público à Câmara ("Pergunte à Câmara").

As perguntas são escolhidas e publicadas à mão pelo responsável do Radar, no
arquivo coletor/perguntas.json. Este módulo valida o arquivo e calcula a
situação de cada pergunta para o site:

  - "aguardando resposta": enviada aos gabinetes, ainda dentro do prazo;
  - "respondida": tem resposta registrada;
  - "sem resposta no prazo": passou o prazo e não houve resposta.

Formato de cada pergunta (veja coletor/perguntas.json):
  {
    "id": "2026-12-01",                      # único, curto, sem espaços
    "pergunta": "Texto da pergunta",
    "tema": "Saúde",                         # opcional
    "projeto": "PL 074/2026",                # opcional
    "para": ["luciano-santos"] ou ["todos"], # slugs de coletor/vereadores.json
    "enviada_em": "2026-12-01",              # data do e-mail aos gabinetes
    "respostas": [                           # opcional; uma por gabinete que respondeu
      {"de": "luciano-santos", "data": "2026-12-10", "texto": "..."}
    ]
  }
"""

import json
from datetime import date, timedelta
from pathlib import Path


class PerguntaInvalida(ValueError):
    pass


def _data(valor, onde):
    try:
        return date.fromisoformat(valor)
    except (TypeError, ValueError):
        raise PerguntaInvalida(f"{onde}: data inválida {valor!r}. Use AAAA-MM-DD, por exemplo 2026-12-01.")


def carregar(caminho: Path, slugs_validos, hoje: date | None = None):
    if not caminho.exists():
        return {"prazo_dias": 20, "perguntas": []}
    try:
        bruto = json.loads(caminho.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        raise PerguntaInvalida(f"{caminho.name}, linha {e.lineno}: o arquivo não é um JSON válido ({e.msg}). "
                               "Confira vírgulas e aspas perto dessa linha.")
    hoje = hoje or date.today()
    prazo = int(bruto.get("prazo_dias", 20))
    vistos, saida = set(), []
    for i, p in enumerate(bruto.get("perguntas", []), 1):
        onde = f"pergunta {i} ({p.get('id', 'sem id')})"
        for campo in ("id", "pergunta", "para", "enviada_em"):
            if not p.get(campo):
                raise PerguntaInvalida(f"{onde}: falta o campo {campo!r}.")
        if p["id"] in vistos:
            raise PerguntaInvalida(f"{onde}: id repetido.")
        vistos.add(p["id"])
        para = p["para"]
        if para != ["todos"]:
            for s in para:
                if s not in slugs_validos:
                    raise PerguntaInvalida(f"{onde}: vereador {s!r} não existe em vereadores.json.")
        enviada = _data(p["enviada_em"], onde)
        limite = enviada + timedelta(days=prazo)
        respostas = []
        for r in p.get("respostas", []):
            if r.get("de") not in slugs_validos and r.get("de") not in ("Presidência", "Mesa Diretora"):
                raise PerguntaInvalida(f"{onde}: resposta de {r.get('de')!r}, que não está em vereadores.json.")
            _data(r.get("data"), onde)
            if not r.get("texto"):
                raise PerguntaInvalida(f"{onde}: resposta sem texto.")
            respostas.append({"de": r["de"], "data": r["data"], "texto": r["texto"].strip()})
        respostas.sort(key=lambda r: r["data"])
        destinatarios = sorted(slugs_validos) if para == ["todos"] else list(para)
        responderam = {r["de"] for r in respostas}
        if respostas:
            situacao = "respondida"
        elif hoje > limite:
            situacao = "sem resposta no prazo"
        else:
            situacao = "aguardando resposta"
        saida.append({
            "id": p["id"], "pergunta": p["pergunta"].strip(), "tema": p.get("tema", ""), "projeto": p.get("projeto", ""),
            "para": para, "destinatarios": destinatarios, "enviada_em": p["enviada_em"], "prazo": limite.isoformat(),
            "situacao": situacao, "respostas": respostas,
            "sem_resposta": [s for s in destinatarios if s not in responderam] if hoje > limite else [],
        })
    saida.sort(key=lambda p: (p["enviada_em"], p["id"]), reverse=True)
    return {"prazo_dias": prazo, "perguntas": saida}
