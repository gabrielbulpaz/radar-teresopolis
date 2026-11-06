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
import csv
import html
import json
import re
import sys
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


RX_RETOMADA = re.compile(r"^(e |ja |depois,? |em seguida,? |entao,? )?(a proposta|o projeto|o texto|a materia|a proposicao|a medida|ela|ele)\b")
RX_GRUPO = re.compile(r"\b(em bloco|os seguintes|os projetos|projetos de lei|as propostas|as materias)\b")


def situacao_com_contexto(frase_norm: str, frases_lista, i: int, sigla: str = "PL") -> str:
    """Situação da proposição, olhando o entorno quando a frase não diz.

    - Leis citadas: 'revogada' ou 'lei citada' (não são projetos em tramitação).
    - Frases seguintes que retomam o projeto ('A proposta foi aprovada...'),
      até 4 frases, parando se outra proposição for citada (listas numeradas).
    - Frase anterior que aprova/rejeita um grupo ('aprovou em bloco projetos...
      Entre os projetos estão: o PL 74/2026...').
    """
    if sigla in ("LEI", "LC"):
        return "revogada" if re.search(r"\brevog(ou|ad|ar|a\b)", frase_norm) else "lei citada"
    sit = situacao_da_frase(frase_norm)
    if sit != "citado":
        return sit
    # Item de lista ('2. Projeto de Lei nº 001/2025:') olha até 4 frases à frente;
    # nos demais casos, só a frase imediatamente seguinte.
    alcance = 4 if frase_norm.rstrip().endswith(":") else 1
    for prox in frases_lista[i + 1:i + 1 + alcance]:
        pn = normalizar(prox)
        if RX_PROPOSICAO.search(pn):
            break
        if RX_RETOMADA.search(pn):
            s2 = situacao_da_frase(pn)
            if s2 != "citado":
                return s2
    cab = _cabecalho_de_grupo(frases_lista, i)
    if cab:
        s2 = situacao_da_frase(cab)
        if s2 in ("aprovado", "rejeitado", "apresentado"):
            return s2
    return sit


def _cabecalho_de_grupo(frases_lista, i: int):
    """Frase anterior (até 3 atrás) que anuncia um grupo de projetos, sem número:
    'aprovou em bloco projetos de lei...', 'apresentou dois projetos de sua autoria'."""
    for j in range(i - 1, max(-1, i - 4), -1):
        ant = normalizar(frases_lista[j])
        if RX_PROPOSICAO.search(ant):
            continue
        if RX_GRUPO.search(ant) or re.search(r"\b(dois|duas|tres|dos|das) (projetos|propostas)", ant):
            return ant
        return None
    return None


def autor_do_contexto(frases_lista, i: int, rx_vereadores):
    """'X apresentou dois projetos de sua autoria. O PL 17/2026 propõe...' -> X"""
    if frases_lista[i].rstrip().endswith(":") and i + 1 < len(frases_lista):
        prox = normalizar(frases_lista[i + 1])
        m = re.match(r"(tambem )?de autoria d[oa] (.{0,60})", prox)
        if m:
            if re.search(r"executivo|prefeit", m.group(2)):
                return "Executivo"
            if "mesa" in m.group(2):
                return "Mesa Diretora"
            achado = _primeiro_vereador(m.group(2), rx_vereadores)
            if achado:
                return achado
    cab = _cabecalho_de_grupo(frases_lista, i)
    if not cab or not re.search(r"\b(de sua autoria|apresentou|protocolou)\b", cab):
        return None
    return _primeiro_vereador(cab, rx_vereadores, ultimo=True)


VERBOS_EMENTA = (r"(propoe|institui|cria|altera|dispoe|concede|garante|autoriza|regulamenta|revoga|denomina|declara|"
                 r"reconhece|modifica|estabelece|inclui|obriga|proibe|determina|corrige|atualiza|amplia|reforca|"
                 r"fixa|torna|preve|disciplina|assegura|confere|homenageia|regula|implanta|implementa|permite|"
                 r"destina|reajusta|aumenta|reduz|suspende|transforma|unifica|oficializa|"
                 r"alterou|criou|instituiu|autorizou|revogou|estabeleceu|concedeu|regulamentou)")
RX_VERBO = re.compile(r"\b" + VERBOS_EMENTA + r"\b")


def _limpar_ementa(texto: str, limite: int = 220) -> str:
    t = re.split(r"[;\n]|\.\s|\.$", texto, maxsplit=1)[0].strip(" ,:-–—")
    if len(t) > limite:
        t = t[: limite - 1].rsplit(" ", 1)[0] + "…"
    return t[:1].upper() + t[1:] if t else ""


def ementa_da_frase(frase: str, frase_norm: str, fim: int):
    """'..., PL 74/2026, de autoria de X, que garante prioridade...' -> 'Garante prioridade...'"""
    if len(frase) != len(frase_norm):  # normalização mudou o tamanho; não dá para mapear
        return None
    resto_n, resto = frase_norm[fim:fim + 400], frase[fim:fim + 400]
    # Corta na próxima proposição só quando é uma lista ('...; o PL 75/2026'),
    # não quando a descrição cita uma lei ('que revoga a Lei Complementar 351/2025').
    for prox in RX_PROPOSICAO.finditer(resto_n):
        if re.search(r"(;|,|\be)\s*(o|a|os|as)?\s*$", resto_n[:prox.start()]):
            resto_n, resto = resto_n[:prox.start()], resto[:prox.start()]
            break
    m = RX_VERBO.search(resto_n[:220])
    if not m or ";" in resto_n[:m.start()]:
        return None
    return _limpar_ementa(resto[m.start():]) or None


def ementa_do_contexto(frases_lista, i: int):
    """Item de lista ('Projeto de Lei nº 1/2025:') com a descrição nas frases seguintes."""
    if not frases_lista[i].rstrip().endswith(":"):
        return None
    for prox in frases_lista[i + 1:i + 4]:
        pn = normalizar(prox)
        if RX_PROPOSICAO.search(pn):
            return None
        m = re.search(r"\b(busca|visa|pretende|tem como objetivo)\s+(.+)", prox, flags=re.I)
        if m and len(prox) == len(pn):
            return _limpar_ementa(m.group(2))
        if RX_VERBO.match(pn):
            return _limpar_ementa(prox)
    return None


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
        # '... PL 75/2026, do vereador X, que institui...' -> X
        m2 = re.match(r"\s*,?\s*(do|da) (vereador|vereadora|presidente|presidenta|executivo|poder executivo|prefeit\w*|mesa diretora)\b(.{0,50})", depois_norm)
        if m2:
            if re.search(r"executivo|prefeit", m2.group(2)):
                return "Executivo"
            if m2.group(2) == "mesa diretora":
                return "Mesa Diretora"
            achado = _primeiro_vereador(m2.group(3), rx_vereadores)
            if achado:
                return achado
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
    "Saúde": r"saude|hospital|posto de saude|medic|\bupa\b|vacina|radioterapia|enfermag|doenca|psicolog|endemias",
    "Educação": r"escola|educac|creche|professor|aluno|ensino",
    "Transporte e trânsito": r"transporte|onibus|transito|mobilidade|ciclomotor|bicicleta|estrada|trenzinho|guincho",
    "Obras e urbanismo": r"\bobras?\b|paviment|asfalt|calcament|manilha|drenagem|ponte|urbanis|edific|andares|construc|zoneamento|\brua\b|logradouro",
    "Meio ambiente e saneamento": r"ambient|arvore|residuo|\blixo|recicla|catador|\baguas?\b|esgoto|saneamento|ecolog",
    "Animais": r"\banima(l|is)\b|castra|\bcaes\b|\bgatos?\b|\bpets?\b",
    "Assistência social": r"assistencia social|pobreza|alimentar|idoso|deficiencia|\bpcd\b|crianca|adolescen|mulher|violencia",
    "Finanças e impostos": r"tribut|imposto|\biss\b|iptu|orcament|\bldo\b|\bloa\b|\bppa\b|prestacao de contas|contas do executivo|fiscal|emendas? parlamentar|emprestimo|credito|calamidade financeira",
    "Servidores e administração": r"servidor|cargos? publico|estrutura administrativa|secretaria municipal|regimento interno|remunera|salari|revisao geral|transparencia|recursos publicos",
    "Agricultura": r"agric|organico|agroecolog|produtor(es)? rura|lavoura|hortifruti",
    "Cultura, turismo e esporte": r"turis|cultura|festa|feira|artesan|musica|esporte|lazer|carnaval|gastronom|patrimonio historico",
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
                autor = autoria(fn[fim:fim + 200], fn[:ini], rx_ver) or autor_do_contexto(todas, i, rx_ver)
                if autor:
                    p["autores"].add(autor)
                    if autor in por_ver:
                        por_ver[autor]["autoria"].add(k)
                ja = next((m for m in p["mencoes"] if m["noticia"] == n["id"]), None)
                if ja and not ja.get("ementa"):
                    ja["ementa"] = ementa_da_frase(frase, fn, fim) or ementa_do_contexto(todas, i)
                if not ja:
                    p["mencoes"].append({"noticia": n["id"], "data": n["data"],
                                         "situacao": situacao_com_contexto(fn, todas, i, sigla), "trecho": recortar(frase),
                                         "ementa": ementa_da_frase(frase, fn, fim) or ementa_do_contexto(todas, i)})
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
        # A situação vem da notícia mais recente que diz algo além de "citado".
        informativas = [m for m in p["mencoes"] if m["situacao"] != "citado"] or p["mencoes"]
        ultima = informativas[-1]
        p["situacao"], p["data_situacao"] = ultima["situacao"], ultima["data"]
        p["autores"] = sorted(p["autores"])
        ementas = [m["ementa"] for m in p["mencoes"] if m.get("ementa")]
        p["ementa"] = max(ementas, key=len) if ementas else ""
        # Temas pela descrição quando existe; senão, pelos trechos (que podem falar de outros projetos).
        p["temas"] = temas_de(normalizar(p["ementa"] or " ".join(m["trecho"] for m in p["mencoes"])))
        lista_props.append(p)
    lista_props.sort(key=lambda p: (-p["ano"], p["tipo"], -p["numero"]))

    lista_ver = []
    for v in vereadores:
        d = por_ver[v["slug"]]
        lista_ver.append({
            **{k: v[k] for k in ("slug", "nome", "partido", "cargo", "url")},
            "foto": v.get("foto", ""),
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


def exportar_abertos(dados, pasta: Path):
    """Arquivos para download no site: CSV (abre no Excel) e JSON."""
    pasta.mkdir(parents=True, exist_ok=True)
    nomes = {v["slug"]: v["nome"] for v in dados["vereadores"]}
    links = {n["id"]: n["link"] for n in dados["noticias"]}
    autor = lambda a: nomes.get(a, a)

    def gravar(nome, cab, linhas):
        with open(pasta / nome, "w", newline="", encoding="utf-8-sig") as f:
            w = csv.writer(f, delimiter=";")
            w.writerow(cab)
            w.writerows(linhas)

    gravar("projetos.csv", ["projeto", "tipo", "numero", "ano", "descricao", "situacao", "data_situacao", "autores", "temas", "noticias"],
           [[p["chave"], p["tipo_nome"], p["numero"], p["ano"], p["ementa"], p["situacao"], p["data_situacao"],
             ", ".join(map(autor, p["autores"])), ", ".join(p["temas"]), " ".join(links.get(m["noticia"], "") for m in p["mencoes"])]
            for p in dados["proposicoes"]])
    aprov = lambda v: sum(1 for k in v["autoria"] if any(p["chave"] == k and p["situacao"] == "aprovado" for p in dados["proposicoes"]))
    gravar("vereadores.csv", ["vereador", "partido", "cargo", "noticias_que_citam", "projetos_de_autoria", "aprovados", "pagina_oficial"],
           [[v["nome"], v["partido"], v["cargo"], len(v["mencoes"]), len(v["autoria"]), aprov(v), v["url"]] for v in dados["vereadores"]])
    gravar("noticias.csv", ["data", "titulo", "link", "vereadores", "projetos", "temas"],
           [[n["data"], n["titulo"], n["link"], ", ".join(map(autor, n["vereadores"])), ", ".join(n["proposicoes"]), ", ".join(n["temas"])]
            for n in dados["noticias"]])
    (pasta / "radar.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")


sys.path.insert(0, str(Path(__file__).resolve().parent))


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--entrada", default=RAIZ / "dados" / "brutos" / "noticias.json", type=Path)
    ap.add_argument("--vereadores", default=RAIZ / "coletor" / "vereadores.json", type=Path)
    ap.add_argument("--perguntas", default=RAIZ / "coletor" / "perguntas.json", type=Path)
    ap.add_argument("--saida", default=RAIZ / "site" / "dados.js", type=Path)
    ap.add_argument("--demo", action="store_true", help="marca os dados como demonstração")
    args = ap.parse_args()

    noticias = json.loads(args.entrada.read_text(encoding="utf-8")) if args.entrada.exists() else []
    cadastro = json.loads(args.vereadores.read_text(encoding="utf-8"))
    dados = processar(noticias, cadastro)
    dados["demo"] = args.demo
    import perguntas as _perguntas  # noqa: E402 (mesmo diretório)
    try:
        dados["perguntas"] = _perguntas.carregar(args.perguntas, {v["slug"] for v in cadastro["vereadores"]})
    except _perguntas.PerguntaInvalida as erro:
        raise SystemExit(f"Erro em perguntas.json: {erro}")

    args.saida.parent.mkdir(parents=True, exist_ok=True)
    args.saida.write_text("window.DADOS = " + json.dumps(dados, ensure_ascii=False) + ";\n", encoding="utf-8")
    (RAIZ / "dados").mkdir(exist_ok=True)
    exportar_abertos(dados, args.saida.parent / "dados")
    if not args.demo:
        (RAIZ / "dados" / "radar.json").write_text(json.dumps(dados, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(dados['noticias'])} notícias, {len(dados['proposicoes'])} proposições -> {args.saida}")


if __name__ == "__main__":
    main()
