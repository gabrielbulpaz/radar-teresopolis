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

    def test_sessoes(self):
        self.assertTrue(all(n["sessao"] for n in self.d["noticias"]))
        self.assertEqual(self.d["noticias"][0]["id"], 3)  # mais recente primeiro


if __name__ == "__main__":
    unittest.main()
