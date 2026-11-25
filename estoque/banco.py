"""Acesso ao banco de dados SQLite e operações de estoque."""

import sqlite3
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parent.parent
SCHEMA_PATH = ROOT_DIR / "banco.sql"
DEFAULT_DB_PATH = ROOT_DIR / "estoque.db"


class BancoEstoque:
    def __init__(self, caminho=DEFAULT_DB_PATH):
        self.caminho = str(caminho)
        self.inicializar()

    def conectar(self):
        conexao = sqlite3.connect(self.caminho)
        conexao.row_factory = sqlite3.Row
        conexao.execute("PRAGMA foreign_keys = ON")
        return conexao

    def inicializar(self):
        with self.conectar() as conexao:
            conexao.executescript(SCHEMA_PATH.read_text(encoding="utf-8"))

    def listar_produtos(self, categoria=None, busca=None):
        consulta = """
            SELECT codigo, nome, categoria, preco, quantidade, estoque_minimo
            FROM produtos
            WHERE 1 = 1
        """
        parametros = []
        if categoria:
            consulta += " AND categoria = ?"
            parametros.append(categoria)
        if busca:
            consulta += " AND (codigo LIKE ? OR nome LIKE ?)"
            termo = f"%{busca.strip()}%"
            parametros.extend((termo, termo))
        consulta += " ORDER BY nome COLLATE NOCASE"
        with self.conectar() as conexao:
            return [dict(linha) for linha in conexao.execute(consulta, parametros)]

    def adicionar_produto(self, produto):
        with self.conectar() as conexao:
            conexao.execute(
                """
                INSERT INTO produtos (codigo, nome, categoria, preco, estoque_minimo)
                VALUES (:codigo, :nome, :categoria, :preco, :estoque_minimo)
                """,
                produto,
            )

    def atualizar_produto(self, codigo, produto):
        with self.conectar() as conexao:
            cursor = conexao.execute(
                """
                UPDATE produtos
                SET nome = :nome, categoria = :categoria, preco = :preco,
                    estoque_minimo = :estoque_minimo
                WHERE codigo = :codigo
                """,
                {**produto, "codigo": codigo},
            )
            if cursor.rowcount == 0:
                raise ValueError("O produto selecionado não foi encontrado.")

    def excluir_produto(self, codigo):
        with self.conectar() as conexao:
            cursor = conexao.execute("DELETE FROM produtos WHERE codigo = ?", (codigo,))
            if cursor.rowcount == 0:
                raise ValueError("O produto selecionado não foi encontrado.")

    def registrar_movimentacao(self, codigo, tipo, quantidade):
        with self.conectar() as conexao:
            conexao.execute(
                """
                INSERT INTO movimentacoes (produto_codigo, tipo, quantidade)
                VALUES (?, ?, ?)
                """,
                (codigo, tipo, quantidade),
            )

    def listar_movimentacoes(self, categoria=None):
        consulta = """
            SELECT m.id, m.tipo, m.quantidade, m.data, p.codigo, p.nome, p.categoria
            FROM movimentacoes AS m
            JOIN produtos AS p ON p.codigo = m.produto_codigo
        """
        parametros = []
        if categoria:
            consulta += " WHERE p.categoria = ?"
            parametros.append(categoria)
        consulta += " ORDER BY m.data DESC, m.id DESC"
        with self.conectar() as conexao:
            return [dict(linha) for linha in conexao.execute(consulta, parametros)]

    def listar_categorias(self):
        with self.conectar() as conexao:
            linhas = conexao.execute(
                """
                SELECT DISTINCT categoria FROM produtos
                WHERE TRIM(categoria) <> ''
                ORDER BY categoria COLLATE NOCASE
                """
            )
            return [linha["categoria"] for linha in linhas]

    def obter_resumo(self, categoria=None):
        filtro = " WHERE categoria = ?" if categoria else ""
        parametros = (categoria,) if categoria else ()
        with self.conectar() as conexao:
            resumo = conexao.execute(
                f"""
                SELECT COUNT(*) AS produtos,
                       COALESCE(SUM(quantidade), 0) AS unidades,
                       COALESCE(SUM(preco * quantidade), 0) AS valor_total,
                       COALESCE(SUM(CASE WHEN quantidade <= estoque_minimo
                                         THEN 1 ELSE 0 END), 0) AS estoque_baixo
                FROM produtos{filtro}
                """,
                parametros,
            ).fetchone()
            por_categoria = conexao.execute(
                f"""
                SELECT categoria, COALESCE(SUM(preco * quantidade), 0) AS valor
                FROM produtos{filtro}
                GROUP BY categoria
                ORDER BY valor DESC, categoria COLLATE NOCASE
                """,
                parametros,
            ).fetchall()
            return {
                **dict(resumo),
                "por_categoria": [dict(linha) for linha in por_categoria],
            }
