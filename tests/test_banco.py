import sqlite3
import tempfile
import unittest
from pathlib import Path

from estoque.banco import BancoEstoque
from estoque.validacoes import validar_produto, validar_quantidade


class BancoEstoqueTests(unittest.TestCase):
    def setUp(self):
        self.diretorio = tempfile.TemporaryDirectory()
        self.banco = BancoEstoque(Path(self.diretorio.name) / "teste.db")
        self.banco.adicionar_produto(
            {
                "codigo": "P001",
                "nome": "Caneta",
                "categoria": "Papelaria",
                "preco": 2.5,
                "estoque_minimo": 3,
            }
        )

    def tearDown(self):
        self.diretorio.cleanup()

    def test_movimentacoes_atualizam_estoque_e_resumo(self):
        self.banco.registrar_movimentacao("P001", "entrada", 8)
        self.banco.registrar_movimentacao("P001", "saida", 2)

        produto = self.banco.listar_produtos()[0]
        resumo = self.banco.obter_resumo()
        self.assertEqual(produto["quantidade"], 6)
        self.assertEqual(resumo["valor_total"], 15)
        self.assertEqual(len(self.banco.listar_movimentacoes()), 2)

    def test_saida_acima_do_saldo_e_bloqueada_pelo_banco(self):
        with self.assertRaisesRegex(sqlite3.IntegrityError, "Estoque insuficiente"):
            self.banco.registrar_movimentacao("P001", "saida", 1)

        self.assertEqual(self.banco.listar_produtos()[0]["quantidade"], 0)
        self.assertEqual(self.banco.listar_movimentacoes(), [])

    def test_codigo_unico_e_categoria(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.banco.adicionar_produto(
                {
                    "codigo": "P001",
                    "nome": "Outro",
                    "categoria": "Papelaria",
                    "preco": 1,
                    "estoque_minimo": 0,
                }
            )
        self.assertEqual(len(self.banco.listar_produtos(categoria="Papelaria")), 1)
        self.assertEqual(self.banco.listar_produtos(categoria="Eletrônicos"), [])

    def test_banco_rejeita_quantidade_negativa(self):
        with self.assertRaises(sqlite3.IntegrityError):
            self.banco.registrar_movimentacao("P001", "entrada", -1)
        self.assertEqual(self.banco.listar_produtos()[0]["quantidade"], 0)

    def test_validacoes_rejeitam_valores_invalidos(self):
        with self.assertRaisesRegex(ValueError, "maior que zero"):
            validar_quantidade("0")
        with self.assertRaisesRegex(ValueError, "não pode ser negativo"):
            validar_produto("P002", "Lápis", "Papelaria", "-1", "2")
        self.assertEqual(
            validar_produto("P002", "Lápis", "Papelaria", 1.5, "2")["preco"],
            1.5,
        )


if __name__ == "__main__":
    unittest.main()
