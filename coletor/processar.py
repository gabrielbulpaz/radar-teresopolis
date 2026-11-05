"""Transforma as notícias brutas em dados organizados para o site.

Lê dados/brutos/noticias.json e coletor/vereadores.json e extrai, de cada notícia:
  - quais vereadores foram citados (e o trecho em que aparecem);
  - quais proposições foram citadas (PL, PLC, PR, PDL, PELO, leis), com a
    situação indicada no texto (aprovado, rejeitado, em comissão...) e, quando
    o texto diz, a autoria.

Atenção: tudo vem das notícias oficiais da Câmara, não de um registro formal
de votações. O site deixa isso claro e sempre aponta a notícia de origem.

Uso:
    python coletor/processar.py
    python coletor/processar.py --entrada outro.json --vereadores outro.json --saida site/dados.js
"""

import argparse
import html
import json
import re
import unicodedata
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------- texto


class _Extrator(HTMLParser):
    BLOCOS = {"p", "br", "div", "li", "h1", "h2", "h3", "h4", "h5", "h6", "tr", "figcaption", "blockquote"}
    IGNORAR = {"script", "style", "figure", "iframe"}

    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.partes, self._ignorando = [], 0

    def handle_starttag(self, tag, attrs):
        if tag in self.IGNORAR:
            self._ignorando += 1
        elif tag in self.BLOCOS:
            self.partes.append("\n")

    def handle_endtag(self, tag):
        if tag in self.IGNORAR:
            self._ignorando = max(0, self._ignorando - 1)
        elif tag in self.BLOCOS:
            self.partes.append("\n")

    def handle_data(self, data):
        if not self._ignorando:
            self.partes.append(data)


def html_para_texto(conteudo: str) -> str:
    ext = _Extrator()
    ext.feed(conteudo or "")
    texto = "".join(ext.partes).replace("\xa0", " ")
    linhas = [re.sub(r"[ \t]+", " ", l).strip() for l in texto.split("\n")]
    return "\n".join(l for l in linhas if l)


def normalizar(texto: str) -> str:
    """minúsculas e sem acentos; 'nº' vira 'no'."""
    t = unicodedata.normalize("NFKD", texto)
    t = "".join(c for c in t if not unicodedata.combining(c))
    return t.lower()


ABREVIACOES = {"dr", "dra", "pr", "prof", "profa", "sr", "sra", "srs", "ver", "art", "arts", "no", "n", "nos", "av", "sto", "sta", "exmo", "exma", "pe"}


def frases(texto: str):
    """Divide em frases sem quebrar em 'Dr. Amorim' ou 'Pr. Sandrinho'."""
    saida = []
    for paragrafo in texto.split("\n"):
        inicio = 0
        for m in re.finditer(r"[.!?]+(?=\s+[\"“(]?[A-ZÁÉÍÓÚÂÊÔÃÕÇ0-9])", paragrafo):
            antes = paragrafo[inicio:m.start()].split()
            ultima = normalizar(antes[-1]).strip(".,;:()") if antes else ""
            if ultima in ABREVIACOES or len(ultima) == 1:
                continue
            saida.append(paragrafo[inicio:m.end()].strip())
            inicio = m.end()
        resto = paragrafo[inicio:].strip()
        if resto:
            saida.append(resto)
    return saida


def recortar(frase: str, limite: int = 280) -> str:
    return frase if len(frase) <= limite else frase[: limite - 1].rsplit(" ", 1)[0] + "…"


# ---------------------------------------------------------------- proposições

TIPOS = [
    # (regex sobre texto normalizado, sigla, nome)
    (r"projeto de lei complementar|plc", "PLC", "Projeto de Lei Complementar"),
    (r"projeto de decreto legislativo|pdl", "PDL", "Projeto de Decreto Legislativo"),
    (r"projeto de resolucao|pr", "PR", "Projeto de Resolução"),
    (r"proposta de emenda a lei organica|emenda a lei organica|pelo", "PELO", "Emenda à Lei Orgânica"),
    (r"projeto de lei|pl", "PL", "Projeto de Lei"),
    (r"lei complementar(?: municipal)?|lc", "LC", "Lei Complementar"),
    (r"lei municipal|lei", "LEI", "Lei Municipal"),
]
NOMES_TIPO = {sigla: nome for _, sigla, nome in TIPOS}
_alternativas = "|".join(f"(?P<t{i}>{rx})" for i, (rx, _, _) in enumerate(TIPOS))
RX_PROPOSICAO = re.compile(
    rf"\b(?:{_alternativas})\.?\s*(?:n\s*[o°.]*\s*|numero\s*)?(?P<num>\d{{1,4}})\s*/\s*(?P<ano>\d{{4}}|\d{{2}})\b"
)

# Ordem importa: a primeira que casar na frase vence.
SITUACOES = [
    ("rejeitado", r"\b(rejeitad|reprovad|arquivad)"),
    ("vetado", r"\b(vetad|veto\b)"),
    ("aprovado", r"\b(aprovad|aprova\b|aprovou|aprovaram|aprovacao)"),
    ("adiado", r"\b(adiad|retirad[oa]s? de pauta|pedido de vista|vistas)"),
    ("em comissão", r"\bcomiss(ao|oes)\b"),
    ("lido em plenário", r"\b(leitura|lid[oa]s?\b)"),
    ("apresentado", r"\b(apresent(ad|ou|aram)|protocol(ad|ou)|encaminhad|enviad)"),
]


def situacao_da_frase(frase_norm: str) -> str:
    for nome, rx in SITUACOES:
        if re.search(rx, frase_norm):
            return nome
    return "citado"


RX_RETOMADA = re.compile(r"^(a proposta|o projeto|o texto|a materia|a proposicao|a medida|ela|ele|o pl|o plc|a lei)\b")


def situacao_com_contexto(frase_norm: str, frases_lista, i: int) -> str:
    """Se a frase da citação não diz a situação, olha a seguinte quando ela
    retoma o projeto ('A proposta foi aprovada por unanimidade.')."""
    sit = situacao_da_frase(frase_norm)
    if sit != "citado" or i + 1 >= len(frases_lista):
        return sit
    prox = normalizar(frases_lista[i + 1])
    if RX_RETOMADA.search(prox) and not RX_PROPOSICAO.search(prox):
        return situacao_da_frase(prox)
    return sit


def chave(sigla: str, numero: int, ano: int) -> str:
    return f"{sigla} {numero:03d}/{ano}"


def achar_proposicoes(frase_norm: str):
    for m in RX_PROPOSICAO.finditer(frase_norm):
        idx = next(i for i in range(len(TIPOS)) if m.group(f"t{i}"))
        sigla = TIPOS[idx][1]
        numero, ano = int(m.group("num")), int(m.group("ano"))
        if ano < 100:
            ano += 2000
        if not 1990 <= ano <= 2100 or numero == 0:
            continue
        yield sigla, numero, ano, m.start(), m.end()


# ---------------------------------------------------------------- vereadores


def compilar_vereadores(vereadores):
    """Para cada vereador, um regex que casa qualquer apelido (sem acento)."""
    out = []
    for v in vereadores:
        apelidos = sorted({normalizar(a) for a in v["apelidos"] + [v["nome"]]}, key=len, reverse=True)
        partes = [re.escape(a).replace(r"\ ", r"\s+") for a in apelidos]
        out.append((v["slug"], re.compile(r"(?<![\w])(?:" + "|".join(partes) + r")(?![\w])")))
    return out


def _primeiro_vereador(texto, rx_vereadores, ultimo=False):
    achados = [(m.start(), slug) for slug, r in rx_vereadores for m in r.finditer(texto)]
    if not achados:
        return None
    return (max(achados) if ultimo else min(achados))[1]


def autoria(depois_norm: str, antes_norm: str, rx_vereadores):
    """Procura quem é o autor da proposição citada.

    Casos tratados:
      '... PL 12/2026, de autoria da vereadora X'    -> X
      '... PLC 3/2026, de autoria do Executivo'       -> Executivo
      'O vereador X apresentou o PL 31/2026, de sua autoria' -> X (citado antes)
    """
    m = re.search(r"\b(autoria|autor|autora)\b(.{0,90})", depois_norm)
    if not m:
        # 'O vereador X apresentou/protocolou o PL 29/2026' -> X
        if re.search(r"\b(apresentou|protocolou|propos|propoe|apresenta|protocola|e autora? d[oa]s?)\b[^.;]{0,40}$", antes_norm):
            return _primeiro_vereador(antes_norm, rx_vereadores, ultimo=True)
        return None
    if re.search(r"\bde (sua|propria) autoria", depois_norm[: m.end(1) + 1]):
        return _primeiro_vereador(antes_norm, rx_vereadores, ultimo=True)
    alvo = m.group(2)
    if re.search(r"\b(executivo|prefeit)", alvo):
        return "Executivo"
    if re.search(r"\bmesa( diretora)?\b", alvo):
        return "Mesa Diretora"
    return _primeiro_vereador(alvo, rx_vereadores)


# ---------------------------------------------------------------- temas
# Palavras-chave (sem acento, minúsculas) que indicam o assunto. Edite à vontade.
TEMAS = {
    "Saúde": r"saude|hospital|posto de saude|medic|\bupa\b|vacina|radioterapia|enfermag",
    "Educação": r"escola|educac|creche|professor|aluno|ensino",
    "Transporte e trânsito": r"transporte|onibus|transito|mobilidade|ciclomotor|bicicleta|estrada|trenzinho|guincho",
    "Obras e urbanismo": r"\bobras?\b|paviment|asfalt|calcament|manilha|drenagem|ponte|urbanis|edific|andares|construc|zoneamento",
    "Meio ambiente e saneamento": r"ambient|arvore|residuo|\blixo|recicla|catador|\baguas?\b|esgoto|saneamento|ecolog",
    "Animais": r"\banima(l|is)\b|castra|\bcaes\b|\bgatos?\b|\bpets?\b",
    "Assistência social": r"assistencia social|pobreza|alimentar|idoso|deficiencia|\bpcd\b|crianca|adolescen|mulher|violencia",
    "Finanças e impostos": r"tribut|imposto|\biss\b|iptu|orcament|\bldo\b|\bloa\b|\bppa\b|prestacao de contas|contas do executivo|fiscal|emendas? parlamentar",
    "Cultura, turismo e esporte": r"turis|cultura|festa|feira|artesan|musica|esporte|lazer|carnaval",
    "Segurança e iluminação": r"seguranca|guarda municipal|policia|iluminacao",
    "Homenagens e nomes": r"homenag|cidadao honorario|titulo de cidad|\bmocao|mocoes|denomina|medalha|utilidade publica",
}
_RX_TEMAS = {t: re.compile(rx) for t, rx in TEMAS.items()}


def temas_de(texto_norm: str):
    return [t for t, rx in _RX_TEMAS.items() if rx.search(texto_norm)]


# ---------------------------------------------------------------- principal

PALAVRAS_SESSAO = re.compile(r"\bsess(ao|oes)\s+(ordinaria|extraordinaria|solene|especial)|\breuniao extraordinaria")


def _contar_temas(listas_de_trechos):
    cont = {}
    for trechos in listas_de_trechos:
        for t in set(temas_de(normalizar(" ".join(trechos)))):
            cont[t] = cont.get(t, 0) + 1
    return dict(sorted(cont.items(), key=lambda kv: -kv[1]))


def processar(noticias, cadastro):
    vereadores = cadastro["vereadores"]
    rx_ver = compilar_vereadores(vereadores)
    por_ver = {v["slug"]: {"noticias": {}, "autoria": set()} for v in vereadores}
    props = {}
    saida_noticias = []

    for n in sorted(noticias, key=lambda x: (x["data"], x["id"])):
        titulo = html.unescape(re.sub(r"<[^>]+>", "", n.get("titulo", ""))).strip()
        texto = html_para_texto(n.get("html", ""))
        todas = [titulo] + frases(texto)
        ver_aqui, props_aqui = [], []

        for i, frase in enumerate(todas):
            fn = normalizar(frase)
            for slug, rx in rx_ver:
                if rx.search(fn):
                    trechos = por_ver[slug]["noticias"].setdefault(n["id"], [])
                    if slug not in ver_aqui:
                        ver_aqui.append(slug)
                    if len(trechos) < 3 and frase != titulo:
                        trechos.append(recortar(frase))
            for sigla, numero, ano, ini, fim in achar_proposicoes(fn):
                k = chave(sigla, numero, ano)
                p = props.setdefault(k, {"chave": k, "tipo": sigla, "tipo_nome": NOMES_TIPO[sigla],
                                         "numero": numero, "ano": ano, "autores": set(), "mencoes": []})
                autor = autoria(fn[fim:fim + 200], fn[:ini], rx_ver)
                if autor:
                    p["autores"].add(autor)
                    if autor in por_ver:
                        por_ver[autor]["autoria"].add(k)
                if not any(m["noticia"] == n["id"] for m in p["mencoes"]):
                    p["mencoes"].append({"noticia": n["id"], "data": n["data"],
                                         "situacao": situacao_com_contexto(fn, todas, i), "trecho": recortar(frase)})
                if k not in props_aqui:
                    props_aqui.append(k)

        saida_noticias.append({
            "id": n["id"], "data": n["data"], "titulo": titulo, "link": n.get("link", ""),
            "sessao": bool(PALAVRAS_SESSAO.search(normalizar(titulo + " " + texto[:600]))),
            "temas": temas_de(normalizar(titulo + " " + texto)),
            "vereadores": ver_aqui, "proposicoes": props_aqui,
        })

    lista_props = []
    for p in props.values():
        p["mencoes"].sort(key=lambda m: m["data"])
        ultima = p["mencoes"][-1]
        p["situacao"], p["data_situacao"] = ultima["situacao"], ultima["data"]
        p["autores"] = sorted(p["autores"])
        p["temas"] = temas_de(normalizar(" ".join(m["trecho"] for m in p["mencoes"])))
        lista_props.append(p)
    lista_props.sort(key=lambda p: (-p["ano"], p["tipo"], -p["numero"]))

    lista_ver = []
    for v in vereadores:
        d = por_ver[v["slug"]]
        lista_ver.append({
            **{k: v[k] for k in ("slug", "nome", "partido", "cargo", "url")},
            "mencoes": [{"noticia": nid, "trechos": t} for nid, t in d["noticias"].items()],
            "autoria": sorted(d["autoria"]),
            "temas": _contar_temas(d["noticias"].values()),
        })

    return {
        "gerado_em": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fonte": "Notícias oficiais de camarateresopolis.com.br (API WordPress)",
        "fonte_vereadores": cadastro.get("fonte", ""),
        "vereadores": lista_ver,
        "proposicoes": lista_props,
        "noticias": list(reversed(saida_noticias)),
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", default=RAIZ / "dados" / "brutos" / "noticias.json", type=Path)
    ap.add_argument("--vereadores", default=RAIZ / "coletor" / "vereadores.json", type=Path)
    ap.add_argument("--saida", default=RAIZ / "site" / "dados.js", type=Path)
    ap.add_argument("--demo", action="store_true", help="marca os dados como demonstração")
    args = ap.parse_args()

    noticias = json.loads(args.entrada.read_text(encoding="utf-8")) if args.entrada.exists() else []
    cadastro = json.loads(args.vereadores.read_text(encoding="utf-8"))
    dados = processar(noticias, cadastro)
    dados["demo"] = args.demo

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text("window.DADOS = " + json.dumps(dados, ensure_ascii=False) + ";\n", encoding="utf-8")
    (RAIZ / "dados").mkdir(exist_ok=True)
    if not args.demo:
        (RAIZ / "dados" / "radar.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(dados['noticias'])} notícias, {len(dados['proposicoes'])} proposições -> {args.saida}")


if __name__ == "__main__":
    main()
