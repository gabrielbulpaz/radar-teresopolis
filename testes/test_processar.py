"""Testes do processador. Rode com:  python -m unittest discover testes"""

import json
import sys
import unittest
from pathlib import Path

AQUI = Path(__file__).resolve().parent
sys.path.insert(0, str(AQUI.parent / "coletor"))

import processar as P  # noqa: E402


def carregar():
    noticias = json.loads((AQUI / "exemplo_noticias.json").read_text(encoding="utf-8"))
    cadastro = json.loads((AQUI / "exemplo_vereadores.json").read_text(encoding="utf-8"))
    return P.processar(noticias, cadastro)


class TestTexto(unittest.TestCase):
    def test_nao_quebra_frase_em_abreviacao(self):
        f = P.frases("O Dr. Bento falou. Depois o Pr. Davi respondeu.")
        self.assertEqual(f, ["O Dr. Bento falou.", "Depois o Pr. Davi respondeu."])

    def test_html_para_texto(self):
        t = P.html_para_texto("<p>Olá&nbsp;mundo</p><script>x()</script><p>Fim</p>")
        self.assertEqual(t, "Olá mundo\nFim")


class TestProposicoes(unittest.TestCase):
    def casos(self, texto):
        return [(s, n, a) for s, n, a, _, _ in P.achar_proposicoes(P.normalizar(texto))]

    def test_formatos(self):
        self.assertEqual(self.casos("Projeto de Lei nº 012/2026"), [("PL", 12, 2026)])
        self.assertEqual(self.casos("PLC 003/2026"), [("PLC", 3, 2026)])
        self.assertEqual(self.casos("Projeto de Lei Complementar 9/24"), [("PLC", 9, 2024)])
        self.assertEqual(self.casos("Projeto de Resolução nº 001/2025"), [("PR", 1, 2025)])
        self.assertEqual(self.casos("Lei Complementar nº 351/2025"), [("LC", 351, 2025)])

    def test_nao_confunde_partido_ou_data(self):
        self.assertEqual(self.casos("Paulinho Nogueira (PL) falou em 15/03/2026"), [])
        self.assertEqual(self.casos("o PPA 2026/2029"), [])


class TestFluxoCompleto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.d = carregar()
        cls.props = {p["chave"]: p for p in cls.d["proposicoes"]}
        cls.ver = {v["slug"]: v for v in cls.d["vereadores"]}

    def test_mesmo_projeto_com_grafias_diferentes_vira_um_so(self):
        self.assertIn("PL 012/2026", self.props)
        self.assertEqual(len(self.props["PL 012/2026"]["mencoes"]), 2)

    def test_situacao_mais_recente(self):
        self.assertEqual(self.props["PL 012/2026"]["situacao"], "aprovado")
        self.assertEqual(self.props["PR 002/2026"]["situacao"], "rejeitado")
        self.assertEqual(self.props["PLC 003/2026"]["situacao"], "aprovado")
        self.assertEqual(self.props["PL 031/2026"]["situacao"], "apresentado")

    def test_autoria(self):
        self.assertEqual(self.props["PL 012/2026"]["autores"], ["carla-modelo"])
        self.assertEqual(self.props["PLC 003/2026"]["autores"], ["Executivo"])
        self.assertEqual(self.props["PR 002/2026"]["autores"], ["Mesa Diretora"])
        self.assertEqual(self.props["PL 031/2026"]["autores"], ["pr-davi"])
        self.assertEqual(self.ver["carla-modelo"]["autoria"], ["PL 012/2026"])

    def test_mencoes_de_vereadores(self):
        self.assertEqual(len(self.ver["pr-davi"]["mencoes"]), 2)
        self.assertEqual(len(self.ver["dr-bento"]["mencoes"]), 1)
        self.assertEqual(len(self.ver["ana-exemplo"]["mencoes"]), 1)

    def test_temas(self):
        self.assertIn("Animais", self.props["PL 031/2026"]["temas"])
        self.assertIn("Finanças e impostos", self.props["PLC 003/2026"]["temas"])
        self.assertIn("Saúde", self.ver["dr-bento"]["temas"])

    def test_situacao_na_frase_seguinte_e_autor_antes(self):
        noticias = [{"id": 9, "data": "2026-04-28", "link": "#", "titulo": "Sessão ordinária",
                     "html": "<p>Em sessão ordinária, o plenário votou o PLC 007/2026. A proposta foi aprovada por unanimidade.</p>"
                             "<p>A vereadora Carla Modelo apresentou o PL nº 029/2026, que institui o Programa de Cultivo Orgânico.</p>"
                             "<p>Foi citado o PL 040/2026. Ana Exemplo comentou o tema.</p>"}]
        cadastro = json.loads((AQUI / "exemplo_vereadores.json").read_text(encoding="utf-8"))
        props = {p["chave"]: p for p in P.processar(noticias, cadastro)["proposicoes"]}
        self.assertEqual(props["PLC 007/2026"]["situacao"], "aprovado")
        self.assertEqual(props["PL 029/2026"]["autores"], ["carla-modelo"])
        self.assertEqual(props["PL 029/2026"]["situacao"], "apresentado")
        self.assertEqual(props["PL 040/2026"]["situacao"], "citado")

    def test_padroes_reais_da_camara(self):
        html = ("<p>Os vereadores votaram os seguintes projetos:</p>"
                "<p>1. Projeto de Lei Complementar nº 001/2025:</p><p>De autoria do Poder Executivo, altera a estrutura administrativa.</p>"
                "<p>O projeto foi aprovado com 19 votos favoráveis.</p>"
                "<p>2. Projeto de Lei nº 001/2025:</p><p>Modifica a lei da Feirarte.</p>"
                "<p>Na pauta, o plenário aprovou em bloco projetos de lei e moções. Entre os projetos com votação destacada estão: o PL nº 074/2026, que garante prioridade em consultas.</p>"
                "<p>A vereadora Carla Modelo apresentou dois projetos de lei de sua autoria. O PL nº 017/2026 propõe placas informativas. Já o PL nº 018/2026 institui um diagnóstico.</p>"
                "<p>Foi citado também o PL nº 080/2026, do vereador Dr. Bento, que cria a semana do idoso.</p>"
                "<p>O plenário revogou a Lei Complementar nº 351/2025. A norma citada na Lei Complementar nº 182/2014 foi mantida.</p>")
        cadastro = json.loads((AQUI / "exemplo_vereadores.json").read_text(encoding="utf-8"))
        d = P.processar([{"id": 1, "data": "2026-04-28", "link": "#", "titulo": "Sessão", "html": html}], cadastro)
        props = {p["chave"]: p for p in d["proposicoes"]}
        self.assertEqual(props["PLC 001/2025"]["situacao"], "aprovado")
        self.assertEqual(props["PL 001/2025"]["situacao"], "citado")  # nada diz que foi votado
        self.assertEqual(props["PL 074/2026"]["situacao"], "aprovado")
        self.assertEqual(props["PL 017/2026"]["autores"], ["carla-modelo"])
        self.assertEqual(props["PL 018/2026"]["autores"], ["carla-modelo"])
        self.assertEqual(props["PL 018/2026"]["situacao"], "apresentado")
        self.assertEqual(props["PL 080/2026"]["autores"], ["dr-bento"])
        self.assertEqual(props["LC 351/2025"]["situacao"], "revogada")
        self.assertEqual(props["LC 182/2014"]["situacao"], "lei citada")

    def test_citacao_posterior_nao_apaga_aprovacao(self):
        cadastro = json.loads((AQUI / "exemplo_vereadores.json").read_text(encoding="utf-8"))
        ns = [{"id": 1, "data": "2025-01-21", "link": "#", "titulo": "Sessão", "html": "<p>O Projeto de Resolução nº 001/2025 foi aprovado.</p>"},
              {"id": 2, "data": "2025-02-18", "link": "#", "titulo": "Sessão", "html": "<p>O horário segue o Projeto de Resolução nº 001/2025. Ele mudou as sessões. O Executivo encaminhou o Projeto de Lei da LDO às comissões.</p>"}]
        p = P.processar(ns, cadastro)["proposicoes"][0]
        self.assertEqual((p["situacao"], p["data_situacao"]), ("aprovado", "2025-01-21"))

    def test_sessoes(self):
        self.assertTrue(all(n["sessao"] for n in self.d["noticias"]))
        self.assertEqual(self.d["noticias"][0]["id"], 3)  # mais recente primeiro


if __name__ == "__main__":
    unittest.main()
