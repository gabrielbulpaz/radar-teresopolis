"""Testes do Pergunte à Câmara. Rode com:  python -m unittest discover testes"""

import json
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "coletor"))
import perguntas as Q  # noqa: E402

SLUGS = {"ana", "bento", "carla"}


def rodar(lista, hoje=date(2026, 12, 15), prazo=20):
    with tempfile.TemporaryDirectory() as d:
        f = Path(d) / "p.json"
        f.write_text(json.dumps({"prazo_dias": prazo, "perguntas": lista}), encoding="utf-8")
        return Q.carregar(f, SLUGS, hoje)["perguntas"]


class TestPerguntas(unittest.TestCase):
    def test_situacoes(self):
        ps = {p["id"]: p for p in rodar([
            {"id": "a", "pergunta": "Q1", "para": ["ana"], "enviada_em": "2026-12-01"},
            {"id": "b", "pergunta": "Q2", "para": ["bento"], "enviada_em": "2026-11-01"},
            {"id": "c", "pergunta": "Q3", "para": ["carla"], "enviada_em": "2026-11-01",
             "respostas": [{"de": "carla", "data": "2026-11-10", "texto": "Resposta"}]},
        ])}
        self.assertEqual(ps["a"]["situacao"], "aguardando resposta")
        self.assertEqual(ps["b"]["situacao"], "sem resposta no prazo")
        self.assertEqual(ps["b"]["sem_resposta"], ["bento"])
        self.assertEqual(ps["c"]["situacao"], "respondida")

    def test_todos_e_quem_nao_respondeu(self):
        p = rodar([{"id": "t", "pergunta": "Q", "para": ["todos"], "enviada_em": "2026-11-01",
                    "respostas": [{"de": "ana", "data": "2026-11-05", "texto": "Sim"}]}])[0]
        self.assertEqual(p["destinatarios"], ["ana", "bento", "carla"])
        self.assertEqual(p["sem_resposta"], ["bento", "carla"])

    def test_erros_claros(self):
        with self.assertRaisesRegex(Q.PerguntaInvalida, "não existe"):
            rodar([{"id": "x", "pergunta": "Q", "para": ["zeca"], "enviada_em": "2026-11-01"}])
        with self.assertRaisesRegex(Q.PerguntaInvalida, "data inválida"):
            rodar([{"id": "x", "pergunta": "Q", "para": ["ana"], "enviada_em": "01/11/2026"}])
        with self.assertRaisesRegex(Q.PerguntaInvalida, "id repetido"):
            rodar([{"id": "x", "pergunta": "Q", "para": ["ana"], "enviada_em": "2026-11-01"}] * 2)

    def test_arquivo_inexistente(self):
        self.assertEqual(Q.carregar(Path("/nao/existe.json"), SLUGS)["perguntas"], [])


if __name__ == "__main__":
    unittest.main()
