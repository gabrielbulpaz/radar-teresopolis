"""Gera notícias e vereadores FICTÍCIOS para a prévia do site.

Uso:
    python testes/gerar_demo.py
    python coletor/processar.py --entrada testes/demo_noticias.json --vereadores testes/demo_vereadores.json --demo --saida demo/dados.js
"""

import json
import random
from datetime import date, timedelta
from pathlib import Path

AQUI = Path(__file__).resolve().parent
random.seed(7)

VEREADORES = [
    ("ana-exemplo", "Ana Exemplo", "Partido A", "Presidente", ["Ana Exemplo"]),
    ("dr-bento", "Dr. Bento Teste", "Partido B", "Vice-Presidente", ["Dr. Bento", "Bento Teste"]),
    ("carla-modelo", "Carla Modelo", "Partido C", "", ["Carla Modelo"]),
    ("pr-davi", "Pr. Davi Amostra", "Partido A", "", ["Pr. Davi", "Davi Amostra"]),
    ("elisa-ficticia", "Elisa Fictícia", "Partido D", "1ª Secretária", ["Elisa Fictícia"]),
    ("fabio-simulado", "Fábio Simulado", "Partido B", "", ["Fábio Simulado"]),
    ("gui-do-bairro", "Gui do Bairro", "Partido C", "", ["Gui do Bairro"]),
    ("helena-prova", "Professora Helena", "Partido D", "", ["Professora Helena", "Helena Prova"]),
]

ASSUNTOS = [
    "cria o programa de hortas comunitárias nas escolas",
    "institui a semana de vacinação nos postos de saúde",
    "regulamenta o uso de bicicletas elétricas nas vias urbanas",
    "cria o castramóvel municipal para cães e gatos",
    "determina a pavimentação e drenagem de ruas em áreas de risco",
    "cria o programa de coleta seletiva com catadores",
    "concede título de cidadão honorário a voluntário da Defesa Civil",
    "amplia o horário das creches municipais",
    "institui a feira de artesanato no centro",
    "reforça a iluminação pública nos pontos de ônibus",
    "cria o cadastro de pessoas com deficiência para transporte adaptado",
    "dá nome de rua a antiga moradora do bairro",
]
COBRANCAS = [
    "cobrou a reforma do posto de saúde do bairro",
    "pediu providências sobre buracos na estrada principal",
    "denunciou falta de professores em uma escola municipal",
    "pediu mais ônibus no horário de pico",
    "cobrou a limpeza de um rio após as chuvas",
    "pediu reforço da guarda municipal nas praças",
    "elogiou a festa cultural do fim de semana",
]


def main():
    noticias, props, nid, n_pl = [], [], 100, {2026: 0}
    d = date(2026, 2, 19)
    sessao = 0
    while d < date(2026, 10, 30):
        if d.month == 7:
            d += timedelta(days=7)
            continue
        sessao += 1
        frases = [f"A Câmara Municipal realizou, nesta terça-feira, a {sessao}ª Sessão Ordinária do ano."]
        novos = []
        for _ in range(random.choice([1, 1, 2])):
            n_pl[2026] += 1
            autor = random.choice(VEREADORES)
            assunto = random.choice(ASSUNTOS)
            num = n_pl[2026]
            props.append((num, autor, assunto))
            novos.append(num)
            frases.append(f"Foi lido o Projeto de Lei nº {num:03d}/2026, de autoria do vereador {autor[4][0]}, que {assunto}. A proposta segue para as comissões.")
        pendentes = [p for p in props if p[0] not in novos]
        for num, autor, assunto in random.sample(pendentes, min(len(pendentes), random.choice([0, 1, 2]))):
            props.remove((num, autor, assunto))
            if random.random() < 0.8:
                frases.append(f"Os vereadores aprovaram o PL {num}/2026, que {assunto}.")
            else:
                frases.append(f"O Projeto de Lei nº {num:03d}/2026 foi rejeitado em votação nominal.")
        for v in random.sample(VEREADORES, random.choice([1, 2, 3])):
            frases.append(f"{random.choice(['O vereador', 'Na tribuna,', 'Em seguida,'])} {v[4][0]} {random.choice(COBRANCAS)}.")
        if sessao % 6 == 0:
            frases.append(f"Também foi aprovado o Projeto de Lei Complementar nº {sessao // 6:03d}/2026, de autoria do Poder Executivo, que altera o Código Tributário e o ISS.")
        titulo = f"Câmara realiza {sessao}ª Sessão Ordinária de 2026"
        noticias.append({"id": nid, "data": d.isoformat(), "modificado": d.isoformat() + "T12:00:00",
                         "link": f"#exemplo-{nid}", "titulo": titulo,
                         "html": "".join(f"<p>{f}</p>" for f in frases)})
        nid += 1
        d += timedelta(days=random.choice([7, 7, 14]))

    (AQUI / "demo_noticias.json").write_text(json.dumps(noticias, ensure_ascii=False, indent=1), encoding="utf-8")
    cad = {"fonte": "exemplo", "vereadores": [
        {"slug": s, "nome": n, "partido": p, "cargo": c, "url": "#", "apelidos": a} for s, n, p, c, a in VEREADORES]}
    (AQUI / "demo_vereadores.json").write_text(json.dumps(cad, ensure_ascii=False, indent=1), encoding="utf-8")
    print(f"{len(noticias)} notícias fictícias geradas")


if __name__ == "__main__":
    main()
