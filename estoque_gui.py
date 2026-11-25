#a primeira vez tava com uns erros
#deixei duas vezes para
#nao esquecer qual que era o erro
#uma das funcoes que definia
#staticmethod tava errada e eu tive que trocar

"""Interface gráfica do Sistema de Controle de Estoque."""

import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from estoque.banco import BancoEstoque
from estoque.exportacao import exportar_csv
from estoque.validacoes import validar_produto, validar_quantidade


def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class AplicacaoEstoque:
    def __init__(self, janela, banco=None):
        self.janela = janela
        self.banco = banco or BancoEstoque()
        self.editando_codigo = None
        self.produto_por_opcao = {}

        self.janela.title("Sistema de Controle de Estoque")
        self.janela.geometry("1120x720")
        self.janela.minsize(900, 600)

        self._configurar_estilos()
        self._criar_menu()
        self._criar_interface()
        self.atualizar_tudo()

    def _configurar_estilos(self):
        estilo = ttk.Style()

        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")

        estilo.configure("Treeview", rowheight=27)
        estilo.configure(
            "Treeview.Heading",
            font=("TkDefaultFont", 10, "bold")
        )
        estilo.configure(
            "Titulo.TLabel",
            font=("TkDefaultFont", 18, "bold")
        )
        estilo.configure(
            "KPI.TLabel",
            font=("TkDefaultFont", 12, "bold")
        )

    def _criar_menu(self):
        menu = tk.Menu(self.janela)
        navegacao = tk.Menu(menu, tearoff=False)

        navegacao.add_command(
            label="Produtos",
            command=lambda: self.abas.select(self.aba_produtos)
        )
        navegacao.add_command(
            label="Movimentações",
            command=lambda: self.abas.select(self.aba_movimentacoes)
        )
        navegacao.add_command(
            label="Estoque atual",
            command=lambda: self.abas.select(self.aba_estoque)
        )
        navegacao.add_command(
            label="Relatórios",
            command=lambda: self.abas.select(self.aba_relatorios)
        )

        menu.add_cascade(label="Navegar", menu=navegacao)
        menu.add_command(label="Atualizar", command=self.atualizar_tudo)

        self.janela.configure(menu=menu)

    def _criar_interface(self):
        topo = ttk.Frame(self.janela, padding=(18, 14, 18, 8))
        topo.pack(fill="x")

        ttk.Label(
            topo,
            text="Controle de Estoque",
            style="Titulo.TLabel"
        ).pack(side="left")

        self.alerta_label = ttk.Label(
            topo,
            text="",
            foreground="#a33a00"
        )
        self.alerta_label.pack(side="right")

        self.abas = ttk.Notebook(self.janela)
        self.abas.pack(
            fill="both",
            expand=True,
            padx=14,
            pady=(0, 10)
        )

        self.aba_produtos = ttk.Frame(self.abas, padding=12)
        self.aba_movimentacoes = ttk.Frame(self.abas, padding=12)
        self.aba_estoque = ttk.Frame(self.abas, padding=12)
        self.aba_relatorios = ttk.Frame(self.abas, padding=12)

        self.abas.add(self.aba_produtos, text="Produtos")
        self.abas.add(self.aba_movimentacoes, text="Entradas e saídas")
        self.abas.add(self.aba_estoque, text="Estoque atual")
        self.abas.add(self.aba_relatorios, text="Relatórios")

        self._criar_aba_produtos()
        self._criar_aba_movimentacoes()
        self._criar_aba_estoque()
        self._criar_aba_relatorios()

        self.status_label = ttk.Label(
            self.janela,
            text="Pronto",
            relief="sunken",
            anchor="w",
            padding=5
        )
        self.status_label.pack(fill="x", side="bottom")

    def _criar_aba_produtos(self):
        formulario = ttk.LabelFrame(
            self.aba_produtos,
            text="Cadastro de produto",
            padding=10
        )
        formulario.pack(fill="x")

        self.codigo_var = tk.StringVar()
        self.nome_var = tk.StringVar()
        self.categoria_var = tk.StringVar()
        self.preco_var = tk.StringVar()
        self.minimo_var = tk.StringVar(value="5")

        campos = [
            ("Código", self.codigo_var, 16),
            ("Nome", self.nome_var, 26),
            ("Categoria", self.categoria_var, 20),
            ("Preço (R$)", self.preco_var, 14),
            ("Estoque mínimo", self.minimo_var, 14),
        ]

        for coluna, (rotulo, variavel, largura) in enumerate(campos):
            ttk.Label(
                formulario,
                text=rotulo
            ).grid(row=0, column=coluna, sticky="w", padx=4)

            entrada = ttk.Entry(
                formulario,
                textvariable=variavel,
                width=largura
            )
            entrada.grid(
                row=1,
                column=coluna,
                sticky="ew",
                padx=4,
                pady=(3, 8)
            )

            if coluna == 0:
                self.codigo_entry = entrada

        botoes = ttk.Frame(formulario)
        botoes.grid(
            row=2,
            column=0,
            columnspan=5,
            sticky="w",
            padx=4
        )

        ttk.Button(
            botoes,
            text="Salvar produto",
            command=self.salvar_produto
        ).pack(side="left", padx=(0, 6))

        ttk.Button(
            botoes,
            text="Limpar",
            command=self.limpar_formulario
        ).pack(side="left", padx=6)

        ttk.Button(
            botoes,
            text="Excluir selecionado",
            command=self.excluir_produto
        ).pack(side="left", padx=6)

        quadro = ttk.LabelFrame(
            self.aba_produtos,
            text="Produtos cadastrados",
            padding=8
        )
        quadro.pack(fill="both", expand=True, pady=(12, 0))

        colunas = (
            "codigo", "nome", "categoria",
            "preco", "quantidade", "estoque_minimo"
        )

        titulos = (
            "Código", "Nome", "Categoria",
            "Preço", "Quantidade", "Estoque mínimo"
        )

        self.produtos_tree = self._criar_tabela(
            quadro, colunas, titulos
        )

        self.produtos_tree.bind(
            "<<TreeviewSelect>>",
            self.selecionar_produto
        )

    def _criar_aba_movimentacoes(self):
        formulario = ttk.LabelFrame(
            self.aba_movimentacoes,
            text="Registrar movimentação",
            padding=12
        )
        formulario.pack(fill="x")

        self.produto_mov_var = tk.StringVar()
        self.tipo_var = tk.StringVar(value="entrada")
        self.quantidade_var = tk.StringVar()

        ttk.Label(
            formulario,
            text="Produto"
        ).grid(row=0, column=0, sticky="w", padx=5)

        self.produto_combo = ttk.Combobox(
            formulario,
            textvariable=self.produto_mov_var,
            width=48,
            state="readonly"
        )
        self.produto_combo.grid(
            row=1, column=0, padx=5, pady=(3, 8)
        )

        ttk.Label(
            formulario,
            text="Tipo"
        ).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Combobox(
            formulario,
            textvariable=self.tipo_var,
            values=("entrada", "saida"),
            state="readonly",
            width=16
        ).grid(row=1, column=1, padx=5, pady=(3, 8))

        ttk.Label(
            formulario,
            text="Quantidade"
        ).grid(row=0, column=2, sticky="w", padx=5)

        ttk.Entry(
            formulario,
            textvariable=self.quantidade_var,
            width=16
        ).grid(row=1, column=2, padx=5, pady=(3, 8))

        ttk.Button(
            formulario,
            text="Registrar",
            command=self.registrar_movimentacao
        ).grid(row=1, column=3, padx=8, pady=(3, 8))

        quadro = ttk.LabelFrame(
            self.aba_movimentacoes,
            text="Histórico de movimentações",
            padding=8
        )
        quadro.pack(fill="both", expand=True, pady=(12, 0))

        colunas = (
            "data", "tipo", "codigo",
            "nome", "categoria", "quantidade"
        )

        titulos = (
            "Data", "Tipo", "Código",
            "Produto", "Categoria", "Quantidade"
        )

        self.movimentacoes_tree = self._criar_tabela(
            quadro, colunas, titulos
        )

    def _criar_aba_estoque(self):
        filtros = ttk.Frame(self.aba_estoque)
        filtros.pack(fill="x", pady=(0, 8))

        ttk.Label(
            filtros,
            text="Categoria:"
        ).pack(side="left", padx=(0, 5))

        self.filtro_categoria_var = tk.StringVar(value="Todas")

        self.categoria_filtro = ttk.Combobox(
            filtros,
            textvariable=self.filtro_categoria_var,
            state="readonly",
            width=22
        )
        self.categoria_filtro.pack(side="left", padx=(0, 12))

        self.categoria_filtro.bind(
            "<<ComboboxSelected>>",
            lambda _evento: self.atualizar_estoque()
        )

        ttk.Label(
            filtros,
            text="Buscar:"
        ).pack(side="left", padx=(0, 5))

        self.busca_var = tk.StringVar()

        busca = ttk.Entry(
            filtros,
            textvariable=self.busca_var,
            width=26
        )
        busca.pack(side="left", padx=(0, 8))

        busca.bind(
            "<Return>",
            lambda _evento: self.atualizar_estoque()
        )

        ttk.Button(
            filtros,
            text="Filtrar",
            command=self.atualizar_estoque
        ).pack(side="left")

        ttk.Button(
            filtros,
            text="Exportar CSV",
            command=self.exportar_estoque
        ).pack(side="right")

        quadro = ttk.LabelFrame(
            self.aba_estoque,
            text="Posição atual do estoque",
            padding=8
        )
        quadro.pack(fill="both", expand=True)

        colunas = (
            "codigo", "nome", "categoria", "preco",
            "quantidade", "estoque_minimo", "valor"
        )

        titulos = (
            "Código", "Nome", "Categoria", "Preço",
            "Quantidade", "Mínimo", "Valor em estoque"
        )

        self.estoque_tree = self._criar_tabela(
            quadro, colunas, titulos
        )

        self.estoque_tree.tag_configure(
            "baixo",
            background="#fff0e6"
        )

    def _criar_aba_relatorios(self):
        kpis = ttk.Frame(self.aba_relatorios)
        kpis.pack(fill="x", pady=(0, 12))

        self.kpi_produtos = ttk.Label(
            kpis,
            text="Produtos: 0",
            style="KPI.TLabel"
        )

        self.kpi_unidades = ttk.Label(
            kpis,
            text="Unidades: 0",
            style="KPI.TLabel"
        )

        self.kpi_valor = ttk.Label(
            kpis,
            text="Valor total: R$ 0,00",
            style="KPI.TLabel"
        )

        self.kpi_baixo = ttk.Label(
            kpis,
            text="Estoque baixo: 0",
            style="KPI.TLabel"
        )

        for label in (
            self.kpi_produtos,
            self.kpi_unidades,
            self.kpi_valor,
            self.kpi_baixo
        ):
            label.pack(side="left", expand=True, padx=5, pady=8)

        ttk.Label(
            self.aba_relatorios,
            text="Valor do estoque por categoria",
            font=("TkDefaultFont", 12, "bold")
        ).pack(anchor="w", pady=(0, 5))

        self.grafico = tk.Canvas(
            self.aba_relatorios,
            height=360,
            background="white",
            highlightthickness=1,
            highlightbackground="#d0d0d0"
        )
        self.grafico.pack(fill="both", expand=True)

        self.grafico.bind(
            "<Configure>",
            lambda _evento: self.atualizar_relatorio()
        )

        ttk.Button(
            self.aba_relatorios,
            text="Exportar relatório de estoque (CSV)",
            command=self.exportar_estoque
        ).pack(anchor="e", pady=(10, 0))

    @staticmethod
    def _criar_tabela(pai, colunas, titulos):
        recipiente = ttk.Frame(pai)
        recipiente.pack(fill="both", expand=True)

        tabela = ttk.Treeview(
            recipiente,
            columns=colunas,
            show="headings",
            selectmode="browse"
        )

        barra_y = ttk.Scrollbar(
            recipiente,
            orient="vertical",
            command=tabela.yview
        )

        barra_x = ttk.Scrollbar(
            recipiente,
            orient="horizontal",
            command=tabela.xview
        )

        tabela.configure(
            yscrollcommand=barra_y.set,
            xscrollcommand=barra_x.set
        )

        tabela.grid(row=0, column=0, sticky="nsew")
        barra_y.grid(row=0, column=1, sticky="ns")
        barra_x.grid(row=1, column=0, sticky="ew")

        recipiente.rowconfigure(0, weight=1)
        recipiente.columnconfigure(0, weight=1)

        for coluna, titulo in zip(colunas, titulos):
            tabela.heading(coluna, text=titulo)
            tabela.column(
                coluna,
                width=125,
                minwidth=80,
                anchor="w"
            )

        if "preco" in colunas:
            tabela.column("preco", anchor="e", width=110)

        if "valor" in colunas:
            tabela.column("valor", anchor="e", width=145)

        if "quantidade" in colunas:
            tabela.column(
                "quantidade",
                anchor="center",
                width=100
            )

        if "estoque_minimo" in colunas:
            tabela.column(
                "estoque_minimo",
                anchor="center",
                width=120
            )

        return tabela

    def _preencher_tabela(self, tabela, linhas, valores, tags=None):
        tabela.delete(*tabela.get_children())

        for linha in linhas:
            iid_tags = tags(linha) if tags else ()

            tabela.insert(
                "",
                "end",
                values=valores(linha),
                tags=iid_tags
            )

    def atualizar_tudo(self):
        self.atualizar_categorias()
        self.atualizar_produtos()
        self.atualizar_opcoes_produto()
        self.atualizar_movimentacoes()
        self.atualizar_estoque()
        self.atualizar_relatorio()

        resumo = self.banco.obter_resumo()
        baixo = resumo["estoque_baixo"]

        self.alerta_label.configure(
            text=(
                f"ALERTA: {baixo} produto(s) com estoque baixo"
                if baixo else "Estoque dentro do mínimo"
            ),
            foreground="#a33a00" if baixo else "#267346"
        )

    def atualizar_categorias(self):
        categorias = self.banco.listar_categorias()

        atual = (
            self.filtro_categoria_var.get()
            if hasattr(self, "filtro_categoria_var")
            else "Todas"
        )

        self.categoria_filtro.configure(
            values=["Todas", *categorias]
        )

        self.filtro_categoria_var.set(
            atual if atual == "Todas" or atual in categorias
            else "Todas"
        )

    def atualizar_produtos(self):
        produtos = self.banco.listar_produtos()

        self._preencher_tabela(
            self.produtos_tree,
            produtos,
            lambda p: (
                p["codigo"],
                p["nome"],
                p["categoria"],
                moeda(p["preco"]),
                p["quantidade"],
                p["estoque_minimo"]
            )
        )

    def atualizar_opcoes_produto(self):
        produtos = self.banco.listar_produtos()

        self.produto_por_opcao = {
            f'{p["codigo"]} — {p["nome"]} (estoque: {p["quantidade"]})':
            p["codigo"]
            for p in produtos
        }

        valores = list(self.produto_por_opcao)

        self.produto_combo.configure(values=valores)

        if self.produto_mov_var.get() not in self.produto_por_opcao:
            self.produto_mov_var.set(
                valores[0] if valores else ""
            )

    def atualizar_movimentacoes(self):
        historico = self.banco.listar_movimentacoes()

        self._preencher_tabela(
            self.movimentacoes_tree,
            historico,
            lambda m: (
                m["data"],
                m["tipo"],
                m["codigo"],
                m["nome"],
                m["categoria"],
                m["quantidade"]
            )
        )

    def atualizar_estoque(self):
        categoria = self.filtro_categoria_var.get()

        categoria = (
            None if not categoria or categoria == "Todas"
            else categoria
        )

        produtos = self.banco.listar_produtos(
            categoria,
            self.busca_var.get()
        )

        self._preencher_tabela(
            self.estoque_tree,
            produtos,
            lambda p: (
                p["codigo"],
                p["nome"],
                p["categoria"],
                moeda(p["preco"]),
                p["quantidade"],
                p["estoque_minimo"],
                moeda(p["preco"] * p["quantidade"])
            ),
            lambda p: (
                ("baixo",)
                if p["quantidade"] <= p["estoque_minimo"]
                else ()
            )
        )

        self.atualizar_relatorio(categoria)

    def atualizar_relatorio(self, categoria=None):
        resumo = self.banco.obter_resumo(categoria)

        self.kpi_produtos.configure(
            text=f'Produtos: {resumo["produtos"]}'
        )

        self.kpi_unidades.configure(
            text=f'Unidades: {resumo["unidades"]}'
        )

        self.kpi_valor.configure(
            text=f'Valor total: {moeda(resumo["valor_total"])}'
        )

        self.kpi_baixo.configure(
            text=f'Estoque baixo: {resumo["estoque_baixo"]}'
        )

        self.grafico.delete("all")

        largura = max(self.grafico.winfo_width(), 500)
        altura = max(self.grafico.winfo_height(), 280)

        categorias = resumo["por_categoria"]

        if not categorias:
            self.grafico.create_text(
                largura / 2,
                altura / 2,
                text="Cadastre produtos para visualizar o relatório.",
                fill="#666"
            )
            return

        margem_esquerda = min(210, largura * 0.32)
        margem_direita = 115
        topo = 18

        altura_linha = max(
            34,
            min(52, (altura - 30) / len(categorias))
        )

        max_valor = max(
            float(item["valor"]) for item in categorias
        ) or 1

        largura_barra = max(
            50,
            largura - margem_esquerda - margem_direita
        )

        for indice, item in enumerate(categorias):
            centro_y = (
                topo + indice * altura_linha + altura_linha / 2
            )

            valor = float(item["valor"])
            barra = largura_barra * valor / max_valor

            self.grafico.create_text(
                margem_esquerda - 10,
                centro_y,
                text=item["categoria"],
                anchor="e",
                fill="#333"
            )

            self.grafico.create_rectangle(
                margem_esquerda,
                centro_y - 10,
                margem_esquerda + barra,
                centro_y + 10,
                fill="#3478b8",
                outline=""
            )

            self.grafico.create_text(
                margem_esquerda + barra + 8,
                centro_y,
                text=moeda(valor),
                anchor="w",
                fill="#333"
            )

    def salvar_produto(self):
        try:
            produto = validar_produto(
                self.codigo_var.get(),
                self.nome_var.get(),
                self.categoria_var.get(),
                self.preco_var.get(),
                self.minimo_var.get()
            )

            if self.editando_codigo:
                self.banco.atualizar_produto(
                    self.editando_codigo,
                    produto
                )
                acao = "atualizado"
            else:
                self.banco.adicionar_produto(produto)
                acao = "cadastrado"

        except (ValueError, sqlite3.IntegrityError) as error:
            mensagem = (
                "Já existe um produto com esse código."
                if isinstance(error, sqlite3.IntegrityError)
                else str(error)
            )

            messagebox.showerror(
                "Não foi possível salvar",
                mensagem,
                parent=self.janela
            )
            return

        self.limpar_formulario()
        self.atualizar_tudo()

        self.status_label.configure(
            text=f"Produto {acao} com sucesso."
        )

    def selecionar_produto(self, _evento=None):
        selecionados = self.produtos_tree.selection()

        if not selecionados:
            return

        codigo, nome, categoria, preco, _qtd, minimo = (
            self.produtos_tree.item(
                selecionados[0],
                "values"
            )
        )

        self.editando_codigo = codigo
        self.codigo_var.set(codigo)
        self.nome_var.set(nome)
        self.categoria_var.set(categoria)

        self.preco_var.set(
            preco.replace("R$ ", "")
            .replace(".", "")
            .replace(",", ".")
        )

        self.minimo_var.set(str(minimo))
        self.codigo_entry.configure(state="disabled")

    def limpar_formulario(self):
        self.editando_codigo = None

        self.codigo_entry.configure(state="normal")

        self.codigo_var.set("")
        self.nome_var.set("")
        self.categoria_var.set("")
        self.preco_var.set("")
        self.minimo_var.set("5")

        for item in self.produtos_tree.selection():
            self.produtos_tree.selection_remove(item)

    def excluir_produto(self):
        selecionados = self.produtos_tree.selection()

        if not selecionados:
            messagebox.showinfo(
                "Excluir produto",
                "Selecione um produto na tabela.",
                parent=self.janela
            )
            return

        codigo = self.produtos_tree.item(
            selecionados[0],
            "values"
        )[0]

        if not messagebox.askyesno(
            "Confirmar exclusão",
            f"Deseja excluir o produto {codigo}?",
            parent=self.janela
        ):
            return

        try:
            self.banco.excluir_produto(codigo)

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Produto utilizado",
                "Não é possível excluir um produto que possui movimentações registradas.",
                parent=self.janela
            )
            return

        self.limpar_formulario()
        self.atualizar_tudo()

        self.status_label.configure(
            text="Produto excluído."
        )

    def registrar_movimentacao(self):
        codigo = self.produto_por_opcao.get(
            self.produto_mov_var.get()
        )

        if not codigo:
            messagebox.showerror(
                "Movimentação",
                "Cadastre e selecione um produto.",
                parent=self.janela
            )
            return

        tipo = self.tipo_var.get()

        if tipo not in ("entrada", "saida"):
            messagebox.showerror(
                "Movimentação",
                "Selecione entrada ou saída.",
                parent=self.janela
            )
            return

        try:
            quantidade = validar_quantidade(
                self.quantidade_var.get()
            )

            self.banco.registrar_movimentacao(
                codigo,
                tipo,
                quantidade
            )

        except ValueError as error:
            messagebox.showerror(
                "Quantidade inválida",
                str(error),
                parent=self.janela
            )
            return

        except sqlite3.IntegrityError as error:
            message = str(error)

            if "Estoque insuficiente" in message:
                message = (
                    "A quantidade solicitada é maior "
                    "que o estoque disponível."
                )

            elif "FOREIGN KEY" in message:
                message = (
                    "O produto selecionado não foi encontrado."
                )

            messagebox.showerror(
                "Movimentação não registrada",
                message,
                parent=self.janela
            )
            return

        self.quantidade_var.set("")
        self.atualizar_tudo()

        self.status_label.configure(
            text=f"{tipo.capitalize()} registrada com sucesso."
        )

    def exportar_estoque(self):
        categoria = self.filtro_categoria_var.get()

        categoria = (
            None if not categoria or categoria == "Todas"
            else categoria
        )

        produtos = self.banco.listar_produtos(
            categoria,
            self.busca_var.get()
        )

        if not produtos:
            messagebox.showinfo(
                "Exportar relatório",
                "Não há produtos para exportar.",
                parent=self.janela
            )
            return

        caminho = filedialog.asksaveasfilename(
            parent=self.janela,
            title="Salvar relatório de estoque",
            defaultextension=".csv",
            filetypes=(("Arquivo CSV", "*.csv"),),
            initialfile="relatorio_estoque.csv"
        )

        if not caminho:
            return

        exportar_csv(
            caminho,
            (
                "Código",
                "Nome",
                "Categoria",
                "Preço unitário",
                "Quantidade",
                "Estoque mínimo",
                "Valor em estoque"
            ),
            (
                (
                    p["codigo"],
                    p["nome"],
                    p["categoria"],
                    f'{p["preco"]:.2f}'.replace(".", ","),
                    p["quantidade"],
                    p["estoque_minimo"],
                    f'{p["preco"] * p["quantidade"]:.2f}'.replace(".", ",")
                )
                for p in produtos
            )
        )

        self.status_label.configure(
            text=f"Relatório exportado: {caminho}"
        )

        messagebox.showinfo(
            "Exportação concluída",
            "O relatório CSV foi salvo.",
            parent=self.janela
        )


def main():
    janela = tk.Tk()

    try:
        AplicacaoEstoque(janela)

    except (OSError, sqlite3.Error) as error:
        messagebox.showerror(
            "Falha ao iniciar",
            f"Não foi possível inicializar o banco de dados:\n{error}",
            parent=janela
        )

        janela.destroy()
        return

    janela.mainloop()


if __name__ == "__main__":
    main()


"""Interface gráfica do Sistema de Controle de Estoque."""
'''
import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from estoque.banco import BancoEstoque
from estoque.exportacao import exportar_csv
from estoque.validacoes import validar_produto, validar_quantidade


def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class AplicacaoEstoque:
    def __init__(self, janela, banco=None):
        self.janela = janela
        self.banco = banco or BancoEstoque()
        self.editando_codigo = None
        self.produto_por_opcao = {}
        self.janela.title("Sistema de Controle de Estoque")
        self.janela.geometry("1120x720")
        self.janela.minsize(900, 600)
        self._configurar_estilos()
        self._criar_menu()
        self._criar_interface()
        self.atualizar_tudo()

    def _configurar_estilos(self):
        estilo = ttk.Style()
        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")
        estilo.configure("Treeview", rowheight=27)
        estilo.configure("Treeview.Heading", font=("TkDefaultFont", 10, "bold"))
        estilo.configure("Titulo.TLabel", font=("TkDefaultFont", 18, "bold"))
        estilo.configure("KPI.TLabel", font=("TkDefaultFont", 12, "bold"))

    def _criar_menu(self):
        menu = tk.Menu(self.janela)
        navegacao = tk.Menu(menu, tearoff=False)
        navegacao.add_command(label="Produtos", command=lambda: self.abas.select(self.aba_produtos))
        navegacao.add_command(label="Movimentações", command=lambda: self.abas.select(self.aba_movimentacoes))
        navegacao.add_command(label="Estoque atual", command=lambda: self.abas.select(self.aba_estoque))
        navegacao.add_command(label="Relatórios", command=lambda: self.abas.select(self.aba_relatorios))
        menu.add_cascade(label="Navegar", menu=navegacao)
        menu.add_command(label="Atualizar", command=self.atualizar_tudo)
        self.janela.configure(menu=menu)

    def _criar_interface(self):
        topo = ttk.Frame(self.janela, padding=(18, 14, 18, 8))
        topo.pack(fill="x")
        ttk.Label(topo, text="Controle de Estoque", style="Titulo.TLabel").pack(side="left")
        self.alerta_label = ttk.Label(topo, text="", foreground="#a33a00")
        self.alerta_label.pack(side="right")

        self.abas = ttk.Notebook(self.janela)
        self.abas.pack(fill="both", expand=True, padx=14, pady=(0, 10))
        self.aba_produtos = ttk.Frame(self.abas, padding=12)
        self.aba_movimentacoes = ttk.Frame(self.abas, padding=12)
        self.aba_estoque = ttk.Frame(self.abas, padding=12)
        self.aba_relatorios = ttk.Frame(self.abas, padding=12)
        self.abas.add(self.aba_produtos, text="Produtos")
        self.abas.add(self.aba_movimentacoes, text="Entradas e saídas")
        self.abas.add(self.aba_estoque, text="Estoque atual")
        self.abas.add(self.aba_relatorios, text="Relatórios")
        self._criar_aba_produtos()
        self._criar_aba_movimentacoes()
        self._criar_aba_estoque()
        self._criar_aba_relatorios()

        self.status_label = ttk.Label(self.janela, text="Pronto", relief="sunken", anchor="w", padding=5)
        self.status_label.pack(fill="x", side="bottom")

    def _criar_aba_produtos(self):
        formulario = ttk.LabelFrame(self.aba_produtos, text="Cadastro de produto", padding=10)
        formulario.pack(fill="x")
        self.codigo_var = tk.StringVar()
        self.nome_var = tk.StringVar()
        self.categoria_var = tk.StringVar()
        self.preco_var = tk.StringVar()
        self.minimo_var = tk.StringVar(value="5")

        campos = [
            ("Código", self.codigo_var, 16),
            ("Nome", self.nome_var, 26),
            ("Categoria", self.categoria_var, 20),
            ("Preço (R$)", self.preco_var, 14),
            ("Estoque mínimo", self.minimo_var, 14),
        ]
        for coluna, (rotulo, variavel, largura) in enumerate(campos):
            ttk.Label(formulario, text=rotulo).grid(row=0, column=coluna, sticky="w", padx=4)
            entrada = ttk.Entry(formulario, textvariable=variavel, width=largura)
            entrada.grid(row=1, column=coluna, sticky="ew", padx=4, pady=(3, 8))
            if coluna == 0:
                self.codigo_entry = entrada
        botoes = ttk.Frame(formulario)
        botoes.grid(row=2, column=0, columnspan=5, sticky="w", padx=4)
        ttk.Button(botoes, text="Salvar produto", command=self.salvar_produto).pack(side="left", padx=(0, 6))
        ttk.Button(botoes, text="Limpar", command=self.limpar_formulario).pack(side="left", padx=6)
        ttk.Button(botoes, text="Excluir selecionado", command=self.excluir_produto).pack(side="left", padx=6)

        quadro = ttk.LabelFrame(self.aba_produtos, text="Produtos cadastrados", padding=8)
        quadro.pack(fill="both", expand=True, pady=(12, 0))
        colunas = ("codigo", "nome", "categoria", "preco", "quantidade", "estoque_minimo")
        titulos = ("Código", "Nome", "Categoria", "Preço", "Quantidade", "Estoque mínimo")
        self.produtos_tree = self._criar_tabela(quadro, colunas, titulos)
        self.produtos_tree.bind("<<TreeviewSelect>>", self.selecionar_produto)

    def _criar_aba_movimentacoes(self):
        formulario = ttk.LabelFrame(self.aba_movimentacoes, text="Registrar movimentação", padding=12)
        formulario.pack(fill="x")
        self.produto_mov_var = tk.StringVar()
        self.tipo_var = tk.StringVar(value="entrada")
        self.quantidade_var = tk.StringVar()

        ttk.Label(formulario, text="Produto").grid(row=0, column=0, sticky="w", padx=5)
        self.produto_combo = ttk.Combobox(formulario, textvariable=self.produto_mov_var, width=48, state="readonly")
        self.produto_combo.grid(row=1, column=0, padx=5, pady=(3, 8))
        ttk.Label(formulario, text="Tipo").grid(row=0, column=1, sticky="w", padx=5)
        ttk.Combobox(
            formulario, textvariable=self.tipo_var, values=("entrada", "saida"),
            state="readonly", width=16,
        ).grid(row=1, column=1, padx=5, pady=(3, 8))
        ttk.Label(formulario, text="Quantidade").grid(row=0, column=2, sticky="w", padx=5)
        ttk.Entry(formulario, textvariable=self.quantidade_var, width=16).grid(
            row=1, column=2, padx=5, pady=(3, 8)
        )
        ttk.Button(formulario, text="Registrar", command=self.registrar_movimentacao).grid(
            row=1, column=3, padx=8, pady=(3, 8)
        )

        quadro = ttk.LabelFrame(self.aba_movimentacoes, text="Histórico de movimentações", padding=8)
        quadro.pack(fill="both", expand=True, pady=(12, 0))
        colunas = ("data", "tipo", "codigo", "nome", "categoria", "quantidade")
        titulos = ("Data", "Tipo", "Código", "Produto", "Categoria", "Quantidade")
        self.movimentacoes_tree = self._criar_tabela(quadro, colunas, titulos)

    def _criar_aba_estoque(self):
        filtros = ttk.Frame(self.aba_estoque)
        filtros.pack(fill="x", pady=(0, 8))
        ttk.Label(filtros, text="Categoria:").pack(side="left", padx=(0, 5))
        self.filtro_categoria_var = tk.StringVar(value="Todas")
        self.categoria_filtro = ttk.Combobox(
            filtros, textvariable=self.filtro_categoria_var, state="readonly", width=22
        )
        self.categoria_filtro.pack(side="left", padx=(0, 12))
        self.categoria_filtro.bind("<<ComboboxSelected>>", lambda _evento: self.atualizar_estoque())
        ttk.Label(filtros, text="Buscar:").pack(side="left", padx=(0, 5))
        self.busca_var = tk.StringVar()
        busca = ttk.Entry(filtros, textvariable=self.busca_var, width=26)
        busca.pack(side="left", padx=(0, 8))
        busca.bind("<Return>", lambda _evento: self.atualizar_estoque())
        ttk.Button(filtros, text="Filtrar", command=self.atualizar_estoque).pack(side="left")
        ttk.Button(filtros, text="Exportar CSV", command=self.exportar_estoque).pack(side="right")

        quadro = ttk.LabelFrame(self.aba_estoque, text="Posição atual do estoque", padding=8)
        quadro.pack(fill="both", expand=True)
        colunas = ("codigo", "nome", "categoria", "preco", "quantidade", "estoque_minimo", "valor")
        titulos = ("Código", "Nome", "Categoria", "Preço", "Quantidade", "Mínimo", "Valor em estoque")
        self.estoque_tree = self._criar_tabela(quadro, colunas, titulos)
        self.estoque_tree.tag_configure("baixo", background="#fff0e6")

    def _criar_aba_relatorios(self):
        kpis = ttk.Frame(self.aba_relatorios)
        kpis.pack(fill="x", pady=(0, 12))
        self.kpi_produtos = ttk.Label(kpis, text="Produtos: 0", style="KPI.TLabel")
        self.kpi_unidades = ttk.Label(kpis, text="Unidades: 0", style="KPI.TLabel")
        self.kpi_valor = ttk.Label(kpis, text="Valor total: R$ 0,00", style="KPI.TLabel")
        self.kpi_baixo = ttk.Label(kpis, text="Estoque baixo: 0", style="KPI.TLabel")
        for label in (self.kpi_produtos, self.kpi_unidades, self.kpi_valor, self.kpi_baixo):
            label.pack(side="left", expand=True, padx=5, pady=8)

        ttk.Label(
            self.aba_relatorios,
            text="Valor do estoque por categoria",
            font=("TkDefaultFont", 12, "bold"),
        ).pack(anchor="w", pady=(0, 5))
        self.grafico = tk.Canvas(
            self.aba_relatorios, height=360, background="white", highlightthickness=1,
            highlightbackground="#d0d0d0",
        )
        self.grafico.pack(fill="both", expand=True)
        self.grafico.bind("<Configure>", lambda _evento: self.atualizar_relatorio())
        ttk.Button(
            self.aba_relatorios, text="Exportar relatório de estoque (CSV)",
            command=self.exportar_estoque,
        ).pack(anchor="e", pady=(10, 0))

    @staticmethod
    def _criar_tabela(pai, colunas, titulos):
        recipiente = ttk.Frame(pai)
        recipiente.pack(fill="both", expand=True)
        tabela = ttk.Treeview(recipiente, columns=colunas, show="headings", selectmode="browse")
        barra_y = ttk.Scrollbar(recipiente, orient="vertical", command=tabela.yview)
        barra_x = ttk.Scrollbar(recipiente, orient="horizontal", command=tabela.xview)
        tabela.configure(yscrollcommand=barra_y.set, xscrollcommand=barra_x.set)
        tabela.grid(row=0, column=0, sticky="nsew")
        barra_y.grid(row=0, column=1, sticky="ns")
        barra_x.grid(row=1, column=0, sticky="ew")
        recipiente.rowconfigure(0, weight=1)
        recipiente.columnconfigure(0, weight=1)
        for coluna, titulo in zip(colunas, titulos):
            tabela.heading(coluna, text=titulo)
            tabela.column(coluna, width=125, minwidth=80, anchor="w")
        tabela.column("preco", anchor="e", width=110)
        tabela.column("valor", anchor="e", width=145)
        tabela.column("quantidade", anchor="center", width=100)
        tabela.column("estoque_minimo", anchor="center", width=120)
        return tabela

    def _preencher_tabela(self, tabela, linhas, valores, tags=None):
        tabela.delete(*tabela.get_children())
        for linha in linhas:
            iid_tags = tags(linha) if tags else ()
            tabela.insert("", "end", values=valores(linha), tags=iid_tags)

    def atualizar_tudo(self):
        self.atualizar_categorias()
        self.atualizar_produtos()
        self.atualizar_opcoes_produto()
        self.atualizar_movimentacoes()
        self.atualizar_estoque()
        self.atualizar_relatorio()
        resumo = self.banco.obter_resumo()
        baixo = resumo["estoque_baixo"]
        self.alerta_label.configure(
            text=f"ALERTA: {baixo} produto(s) com estoque baixo" if baixo else "Estoque dentro do mínimo",
            foreground="#a33a00" if baixo else "#267346",
        )

    def atualizar_categorias(self):
        categorias = self.banco.listar_categorias()
        atual = self.filtro_categoria_var.get() if hasattr(self, "filtro_categoria_var") else "Todas"
        self.categoria_filtro.configure(values=["Todas", *categorias])
        self.filtro_categoria_var.set(atual if atual == "Todas" or atual in categorias else "Todas")

    def atualizar_produtos(self):
        produtos = self.banco.listar_produtos()
        self._preencher_tabela(
            self.produtos_tree,
            produtos,
            lambda p: (
                p["codigo"], p["nome"], p["categoria"], moeda(p["preco"]),
                p["quantidade"], p["estoque_minimo"],
            ),
        )

    def atualizar_opcoes_produto(self):
        produtos = self.banco.listar_produtos()
        self.produto_por_opcao = {
            f'{p["codigo"]} — {p["nome"]} (estoque: {p["quantidade"]})': p["codigo"]
            for p in produtos
        }
        valores = list(self.produto_por_opcao)
        self.produto_combo.configure(values=valores)
        if self.produto_mov_var.get() not in self.produto_por_opcao:
            self.produto_mov_var.set(valores[0] if valores else "")

    def atualizar_movimentacoes(self):
        historico = self.banco.listar_movimentacoes()
        self._preencher_tabela(
            self.movimentacoes_tree,
            historico,
            lambda m: (
                m["data"], m["tipo"], m["codigo"], m["nome"], m["categoria"], m["quantidade"],
            ),
        )

    def atualizar_estoque(self):
        categoria = self.filtro_categoria_var.get()
        categoria = None if not categoria or categoria == "Todas" else categoria
        produtos = self.banco.listar_produtos(categoria, self.busca_var.get())
        self._preencher_tabela(
            self.estoque_tree,
            produtos,
            lambda p: (
                p["codigo"], p["nome"], p["categoria"], moeda(p["preco"]),
                p["quantidade"], p["estoque_minimo"], moeda(p["preco"] * p["quantidade"]),
            ),
            lambda p: ("baixo",) if p["quantidade"] <= p["estoque_minimo"] else (),
        )
        self.atualizar_relatorio(categoria)

    def atualizar_relatorio(self, categoria=None):
        resumo = self.banco.obter_resumo(categoria)
        self.kpi_produtos.configure(text=f'Produtos: {resumo["produtos"]}')
        self.kpi_unidades.configure(text=f'Unidades: {resumo["unidades"]}')
        self.kpi_valor.configure(text=f'Valor total: {moeda(resumo["valor_total"])}')
        self.kpi_baixo.configure(text=f'Estoque baixo: {resumo["estoque_baixo"]}')
        self.grafico.delete("all")
        largura = max(self.grafico.winfo_width(), 500)
        altura = max(self.grafico.winfo_height(), 280)
        categorias = resumo["por_categoria"]
        if not categorias:
            self.grafico.create_text(
                largura / 2, altura / 2, text="Cadastre produtos para visualizar o relatório.",
                fill="#666",
            )
            return
        margem_esquerda = min(210, largura * 0.32)
        margem_direita = 115
        topo = 18
        altura_linha = max(34, min(52, (altura - 30) / len(categorias)))
        max_valor = max(float(item["valor"]) for item in categorias) or 1
        largura_barra = max(50, largura - margem_esquerda - margem_direita)
        for indice, item in enumerate(categorias):
            centro_y = topo + indice * altura_linha + altura_linha / 2
            valor = float(item["valor"])
            barra = largura_barra * valor / max_valor
            self.grafico.create_text(
                margem_esquerda - 10, centro_y, text=item["categoria"],
                anchor="e", fill="#333",
            )
            self.grafico.create_rectangle(
                margem_esquerda, centro_y - 10, margem_esquerda + barra, centro_y + 10,
                fill="#3478b8", outline="",
            )
            self.grafico.create_text(
                margem_esquerda + barra + 8, centro_y, text=moeda(valor),
                anchor="w", fill="#333",
            )

    def salvar_produto(self):
        try:
            produto = validar_produto(
                self.codigo_var.get(), self.nome_var.get(), self.categoria_var.get(),
                self.preco_var.get(), self.minimo_var.get(),
            )
            if self.editando_codigo:
                self.banco.atualizar_produto(self.editando_codigo, produto)
                acao = "atualizado"
            else:
                self.banco.adicionar_produto(produto)
                acao = "cadastrado"
        except (ValueError, sqlite3.IntegrityError) as error:
            mensagem = "Já existe um produto com esse código." if isinstance(
                error, sqlite3.IntegrityError
            ) else str(error)
            messagebox.showerror("Não foi possível salvar", mensagem, parent=self.janela)
            return
        self.limpar_formulario()
        self.atualizar_tudo()
        self.status_label.configure(text=f"Produto {acao} com sucesso.")

    def selecionar_produto(self, _evento=None):
        selecionados = self.produtos_tree.selection()
        if not selecionados:
            return
        codigo, nome, categoria, preco, _qtd, minimo = self.produtos_tree.item(
            selecionados[0], "values"
        )
        self.editando_codigo = codigo
        self.codigo_var.set(codigo)
        self.nome_var.set(nome)
        self.categoria_var.set(categoria)
        self.preco_var.set(preco.replace("R$ ", "").replace(".", "").replace(",", "."))
        self.minimo_var.set(str(minimo))
        self.codigo_entry.configure(state="disabled")

    def limpar_formulario(self):
        self.editando_codigo = None
        self.codigo_entry.configure(state="normal")
        self.codigo_var.set("")
        self.nome_var.set("")
        self.categoria_var.set("")
        self.preco_var.set("")
        self.minimo_var.set("5")
        for item in self.produtos_tree.selection():
            self.produtos_tree.selection_remove(item)

    def excluir_produto(self):
        selecionados = self.produtos_tree.selection()
        if not selecionados:
            messagebox.showinfo("Excluir produto", "Selecione um produto na tabela.", parent=self.janela)
            return
        codigo = self.produtos_tree.item(selecionados[0], "values")[0]
        if not messagebox.askyesno(
            "Confirmar exclusão", f"Deseja excluir o produto {codigo}?", parent=self.janela
        ):
            return
        try:
            self.banco.excluir_produto(codigo)
        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Produto utilizado",
                "Não é possível excluir um produto que possui movimentações registradas.",
                parent=self.janela,
            )
            return
        self.limpar_formulario()
        self.atualizar_tudo()
        self.status_label.configure(text="Produto excluído.")

    def registrar_movimentacao(self):
        codigo = self.produto_por_opcao.get(self.produto_mov_var.get())
        if not codigo:
            messagebox.showerror("Movimentação", "Cadastre e selecione um produto.", parent=self.janela)
            return
        tipo = self.tipo_var.get()
        if tipo not in ("entrada", "saida"):
            messagebox.showerror("Movimentação", "Selecione entrada ou saída.", parent=self.janela)
            return
        try:
            quantidade = validar_quantidade(self.quantidade_var.get())
            self.banco.registrar_movimentacao(codigo, tipo, quantidade)
        except ValueError as error:
            messagebox.showerror("Quantidade inválida", str(error), parent=self.janela)
            return
        except sqlite3.IntegrityError as error:
            message = str(error)
            if "Estoque insuficiente" in message:
                message = "A quantidade solicitada é maior que o estoque disponível."
            elif "FOREIGN KEY" in message:
                message = "O produto selecionado não foi encontrado."
            messagebox.showerror("Movimentação não registrada", message, parent=self.janela)
            return
        self.quantidade_var.set("")
        self.atualizar_tudo()
        self.status_label.configure(text=f"{tipo.capitalize()} registrada com sucesso.")

    def exportar_estoque(self):
        categoria = self.filtro_categoria_var.get()
        categoria = None if not categoria or categoria == "Todas" else categoria
        produtos = self.banco.listar_produtos(categoria, self.busca_var.get())
        if not produtos:
            messagebox.showinfo("Exportar relatório", "Não há produtos para exportar.", parent=self.janela)
            return
        caminho = filedialog.asksaveasfilename(
            parent=self.janela, title="Salvar relatório de estoque",
            defaultextension=".csv", filetypes=(("Arquivo CSV", "*.csv"),),
            initialfile="relatorio_estoque.csv",
        )
        if not caminho:
            return
        exportar_csv(
            caminho,
            ("Código", "Nome", "Categoria", "Preço unitário", "Quantidade", "Estoque mínimo", "Valor em estoque"),
            (
                (
                    p["codigo"], p["nome"], p["categoria"],
                    f'{p["preco"]:.2f}'.replace(".", ","),
                    p["quantidade"], p["estoque_minimo"],
                    f'{p["preco"] * p["quantidade"]:.2f}'.replace(".", ","),
                )
                for p in produtos
            ),
        )
        self.status_label.configure(text=f"Relatório exportado: {caminho}")
        messagebox.showinfo("Exportação concluída", "O relatório CSV foi salvo.", parent=self.janela)


def main():
    janela = tk.Tk()
    try:
        AplicacaoEstoque(janela)
    except (OSError, sqlite3.Error) as error:
        messagebox.showerror(
            "Falha ao iniciar", f"Não foi possível inicializar o banco de dados:\n{error}",
            parent=janela,
        )
        janela.destroy()
        return
    janela.mainloop()


if __name__ == "__main__":
    main()
'''

"""Interface gráfica do Sistema de Controle de Estoque."""
'''

import sqlite3
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from estoque.banco import BancoEstoque
from estoque.exportacao import exportar_csv
from estoque.validacoes import validar_produto, validar_quantidade


def moeda(valor):
    return f"R$ {valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


class AplicacaoEstoque:
    def __init__(self, janela, banco=None):
        self.janela = janela
        self.banco = banco or BancoEstoque()
        self.editando_codigo = None
        self.produto_por_opcao = {}

        self.janela.title("Sistema de Controle de Estoque")
        self.janela.geometry("1120x720")
        self.janela.minsize(900, 600)

        self._configurar_estilos()
        self._criar_menu()
        self._criar_interface()
        self.atualizar_tudo()

    def _configurar_estilos(self):
        estilo = ttk.Style()

        if "clam" in estilo.theme_names():
            estilo.theme_use("clam")

        estilo.configure("Treeview", rowheight=27)
        estilo.configure(
            "Treeview.Heading",
            font=("TkDefaultFont", 10, "bold")
        )
        estilo.configure(
            "Titulo.TLabel",
            font=("TkDefaultFont", 18, "bold")
        )
        estilo.configure(
            "KPI.TLabel",
            font=("TkDefaultFont", 12, "bold")
        )

    def _criar_menu(self):
        menu = tk.Menu(self.janela)
        navegacao = tk.Menu(menu, tearoff=False)

        navegacao.add_command(
            label="Produtos",
            command=lambda: self.abas.select(self.aba_produtos)
        )
        navegacao.add_command(
            label="Movimentações",
            command=lambda: self.abas.select(self.aba_movimentacoes)
        )
        navegacao.add_command(
            label="Estoque atual",
            command=lambda: self.abas.select(self.aba_estoque)
        )
        navegacao.add_command(
            label="Relatórios",
            command=lambda: self.abas.select(self.aba_relatorios)
        )

        menu.add_cascade(label="Navegar", menu=navegacao)
        menu.add_command(label="Atualizar", command=self.atualizar_tudo)

        self.janela.configure(menu=menu)

    def _criar_interface(self):
        topo = ttk.Frame(self.janela, padding=(18, 14, 18, 8))
        topo.pack(fill="x")

        ttk.Label(
            topo,
            text="Controle de Estoque",
            style="Titulo.TLabel"
        ).pack(side="left")

        self.alerta_label = ttk.Label(
            topo,
            text="",
            foreground="#a33a00"
        )
        self.alerta_label.pack(side="right")

        self.abas = ttk.Notebook(self.janela)
        self.abas.pack(
            fill="both",
            expand=True,
            padx=14,
            pady=(0, 10)
        )

        self.aba_produtos = ttk.Frame(self.abas, padding=12)
        self.aba_movimentacoes = ttk.Frame(self.abas, padding=12)
        self.aba_estoque = ttk.Frame(self.abas, padding=12)
        self.aba_relatorios = ttk.Frame(self.abas, padding=12)

        self.abas.add(self.aba_produtos, text="Produtos")
        self.abas.add(self.aba_movimentacoes, text="Entradas e saídas")
        self.abas.add(self.aba_estoque, text="Estoque atual")
        self.abas.add(self.aba_relatorios, text="Relatórios")

        self._criar_aba_produtos()
        self._criar_aba_movimentacoes()
        self._criar_aba_estoque()
        self._criar_aba_relatorios()

        self.status_label = ttk.Label(
            self.janela,
            text="Pronto",
            relief="sunken",
            anchor="w",
            padding=5
        )
        self.status_label.pack(fill="x", side="bottom")

    def _criar_aba_produtos(self):
        formulario = ttk.LabelFrame(
            self.aba_produtos,
            text="Cadastro de produto",
            padding=10
        )
        formulario.pack(fill="x")

        self.codigo_var = tk.StringVar()
        self.nome_var = tk.StringVar()
        self.categoria_var = tk.StringVar()
        self.preco_var = tk.StringVar()
        self.minimo_var = tk.StringVar(value="5")

        campos = [
            ("Código", self.codigo_var, 16),
            ("Nome", self.nome_var, 26),
            ("Categoria", self.categoria_var, 20),
            ("Preço (R$)", self.preco_var, 14),
            ("Estoque mínimo", self.minimo_var, 14),
        ]

        for coluna, (rotulo, variavel, largura) in enumerate(campos):
            ttk.Label(
                formulario,
                text=rotulo
            ).grid(row=0, column=coluna, sticky="w", padx=4)

            entrada = ttk.Entry(
                formulario,
                textvariable=variavel,
                width=largura
            )
            entrada.grid(
                row=1,
                column=coluna,
                sticky="ew",
                padx=4,
                pady=(3, 8)
            )

            if coluna == 0:
                self.codigo_entry = entrada

        botoes = ttk.Frame(formulario)
        botoes.grid(
            row=2,
            column=0,
            columnspan=5,
            sticky="w",
            padx=4
        )

        ttk.Button(
            botoes,
            text="Salvar produto",
            command=self.salvar_produto
        ).pack(side="left", padx=(0, 6))

        ttk.Button(
            botoes,
            text="Limpar",
            command=self.limpar_formulario
        ).pack(side="left", padx=6)

        ttk.Button(
            botoes,
            text="Excluir selecionado",
            command=self.excluir_produto
        ).pack(side="left", padx=6)

        quadro = ttk.LabelFrame(
            self.aba_produtos,
            text="Produtos cadastrados",
            padding=8
        )
        quadro.pack(fill="both", expand=True, pady=(12, 0))

        colunas = (
            "codigo", "nome", "categoria",
            "preco", "quantidade", "estoque_minimo"
        )

        titulos = (
            "Código", "Nome", "Categoria",
            "Preço", "Quantidade", "Estoque mínimo"
        )

        self.produtos_tree = self._criar_tabela(
            quadro, colunas, titulos
        )

        self.produtos_tree.bind(
            "<<TreeviewSelect>>",
            self.selecionar_produto
        )

    def _criar_aba_movimentacoes(self):
        formulario = ttk.LabelFrame(
            self.aba_movimentacoes,
            text="Registrar movimentação",
            padding=12
        )
        formulario.pack(fill="x")

        self.produto_mov_var = tk.StringVar()
        self.tipo_var = tk.StringVar(value="entrada")
        self.quantidade_var = tk.StringVar()

        ttk.Label(
            formulario,
            text="Produto"
        ).grid(row=0, column=0, sticky="w", padx=5)

        self.produto_combo = ttk.Combobox(
            formulario,
            textvariable=self.produto_mov_var,
            width=48,
            state="readonly"
        )
        self.produto_combo.grid(
            row=1, column=0, padx=5, pady=(3, 8)
        )

        ttk.Label(
            formulario,
            text="Tipo"
        ).grid(row=0, column=1, sticky="w", padx=5)

        ttk.Combobox(
            formulario,
            textvariable=self.tipo_var,
            values=("entrada", "saida"),
            state="readonly",
            width=16
        ).grid(row=1, column=1, padx=5, pady=(3, 8))

        ttk.Label(
            formulario,
            text="Quantidade"
        ).grid(row=0, column=2, sticky="w", padx=5)

        ttk.Entry(
            formulario,
            textvariable=self.quantidade_var,
            width=16
        ).grid(row=1, column=2, padx=5, pady=(3, 8))

        ttk.Button(
            formulario,
            text="Registrar",
            command=self.registrar_movimentacao
        ).grid(row=1, column=3, padx=8, pady=(3, 8))

        quadro = ttk.LabelFrame(
            self.aba_movimentacoes,
            text="Histórico de movimentações",
            padding=8
        )
        quadro.pack(fill="both", expand=True, pady=(12, 0))

        colunas = (
            "data", "tipo", "codigo",
            "nome", "categoria", "quantidade"
        )

        titulos = (
            "Data", "Tipo", "Código",
            "Produto", "Categoria", "Quantidade"
        )

        self.movimentacoes_tree = self._criar_tabela(
            quadro, colunas, titulos
        )

    def _criar_aba_estoque(self):
        filtros = ttk.Frame(self.aba_estoque)
        filtros.pack(fill="x", pady=(0, 8))

        ttk.Label(
            filtros,
            text="Categoria:"
        ).pack(side="left", padx=(0, 5))

        self.filtro_categoria_var = tk.StringVar(value="Todas")

        self.categoria_filtro = ttk.Combobox(
            filtros,
            textvariable=self.filtro_categoria_var,
            state="readonly",
            width=22
        )
        self.categoria_filtro.pack(side="left", padx=(0, 12))

        self.categoria_filtro.bind(
            "<<ComboboxSelected>>",
            lambda _evento: self.atualizar_estoque()
        )

        ttk.Label(
            filtros,
            text="Buscar:"
        ).pack(side="left", padx=(0, 5))

        self.busca_var = tk.StringVar()

        busca = ttk.Entry(
            filtros,
            textvariable=self.busca_var,
            width=26
        )
        busca.pack(side="left", padx=(0, 8))

        busca.bind(
            "<Return>",
            lambda _evento: self.atualizar_estoque()
        )

        ttk.Button(
            filtros,
            text="Filtrar",
            command=self.atualizar_estoque
        ).pack(side="left")

        ttk.Button(
            filtros,
            text="Exportar CSV",
            command=self.exportar_estoque
        ).pack(side="right")

        quadro = ttk.LabelFrame(
            self.aba_estoque,
            text="Posição atual do estoque",
            padding=8
        )
        quadro.pack(fill="both", expand=True)

        colunas = (
            "codigo", "nome", "categoria", "preco",
            "quantidade", "estoque_minimo", "valor"
        )

        titulos = (
            "Código", "Nome", "Categoria", "Preço",
            "Quantidade", "Mínimo", "Valor em estoque"
        )

        self.estoque_tree = self._criar_tabela(
            quadro, colunas, titulos
        )

        self.estoque_tree.tag_configure(
            "baixo",
            background="#fff0e6"
        )

    def _criar_aba_relatorios(self):
        kpis = ttk.Frame(self.aba_relatorios)
        kpis.pack(fill="x", pady=(0, 12))

        self.kpi_produtos = ttk.Label(
            kpis,
            text="Produtos: 0",
            style="KPI.TLabel"
        )

        self.kpi_unidades = ttk.Label(
            kpis,
            text="Unidades: 0",
            style="KPI.TLabel"
        )

        self.kpi_valor = ttk.Label(
            kpis,
            text="Valor total: R$ 0,00",
            style="KPI.TLabel"
        )

        self.kpi_baixo = ttk.Label(
            kpis,
            text="Estoque baixo: 0",
            style="KPI.TLabel"
        )

        for label in (
            self.kpi_produtos,
            self.kpi_unidades,
            self.kpi_valor,
            self.kpi_baixo
        ):
            label.pack(side="left", expand=True, padx=5, pady=8)

        ttk.Label(
            self.aba_relatorios,
            text="Valor do estoque por categoria",
            font=("TkDefaultFont", 12, "bold")
        ).pack(anchor="w", pady=(0, 5))

        self.grafico = tk.Canvas(
            self.aba_relatorios,
            height=360,
            background="white",
            highlightthickness=1,
            highlightbackground="#d0d0d0"
        )
        self.grafico.pack(fill="both", expand=True)

        self.grafico.bind(
            "<Configure>",
            lambda _evento: self.atualizar_relatorio()
        )

        ttk.Button(
            self.aba_relatorios,
            text="Exportar relatório de estoque (CSV)",
            command=self.exportar_estoque
        ).pack(anchor="e", pady=(10, 0))

    @staticmethod
    def _criar_tabela(pai, colunas, titulos):
        recipiente = ttk.Frame(pai)
        recipiente.pack(fill="both", expand=True)

        tabela = ttk.Treeview(
            recipiente,
            columns=colunas,
            show="headings",
            selectmode="browse"
        )

        barra_y = ttk.Scrollbar(
            recipiente,
            orient="vertical",
            command=tabela.yview
        )

        barra_x = ttk.Scrollbar(
            recipiente,
            orient="horizontal",
            command=tabela.xview
        )

        tabela.configure(
            yscrollcommand=barra_y.set,
            xscrollcommand=barra_x.set
        )

        tabela.grid(row=0, column=0, sticky="nsew")
        barra_y.grid(row=0, column=1, sticky="ns")
        barra_x.grid(row=1, column=0, sticky="ew")

        recipiente.rowconfigure(0, weight=1)
        recipiente.columnconfigure(0, weight=1)

        for coluna, titulo in zip(colunas, titulos):
            tabela.heading(coluna, text=titulo)
            tabela.column(
                coluna,
                width=125,
                minwidth=80,
                anchor="w"
            )

        if "preco" in colunas:
            tabela.column("preco", anchor="e", width=110)

        if "valor" in colunas:
            tabela.column("valor", anchor="e", width=145)

        if "quantidade" in colunas:
            tabela.column(
                "quantidade",
                anchor="center",
                width=100
            )

        if "estoque_minimo" in colunas:
            tabela.column(
                "estoque_minimo",
                anchor="center",
                width=120
            )

        return tabela

    def _preencher_tabela(self, tabela, linhas, valores, tags=None):
        tabela.delete(*tabela.get_children())

        for linha in linhas:
            iid_tags = tags(linha) if tags else ()

            tabela.insert(
                "",
                "end",
                values=valores(linha),
                tags=iid_tags
            )

    def atualizar_tudo(self):
        self.atualizar_categorias()
        self.atualizar_produtos()
        self.atualizar_opcoes_produto()
        self.atualizar_movimentacoes()
        self.atualizar_estoque()
        self.atualizar_relatorio()

        resumo = self.banco.obter_resumo()
        baixo = resumo["estoque_baixo"]

        self.alerta_label.configure(
            text=(
                f"ALERTA: {baixo} produto(s) com estoque baixo"
                if baixo else "Estoque dentro do mínimo"
            ),
            foreground="#a33a00" if baixo else "#267346"
        )

    def atualizar_categorias(self):
        categorias = self.banco.listar_categorias()

        atual = (
            self.filtro_categoria_var.get()
            if hasattr(self, "filtro_categoria_var")
            else "Todas"
        )

        self.categoria_filtro.configure(
            values=["Todas", *categorias]
        )

        self.filtro_categoria_var.set(
            atual if atual == "Todas" or atual in categorias
            else "Todas"
        )

    def atualizar_produtos(self):
        produtos = self.banco.listar_produtos()

        self._preencher_tabela(
            self.produtos_tree,
            produtos,
            lambda p: (
                p["codigo"],
                p["nome"],
                p["categoria"],
                moeda(p["preco"]),
                p["quantidade"],
                p["estoque_minimo"]
            )
        )

    def atualizar_opcoes_produto(self):
        produtos = self.banco.listar_produtos()

        self.produto_por_opcao = {
            f'{p["codigo"]} — {p["nome"]} (estoque: {p["quantidade"]})':
            p["codigo"]
            for p in produtos
        }

        valores = list(self.produto_por_opcao)

        self.produto_combo.configure(values=valores)

        if self.produto_mov_var.get() not in self.produto_por_opcao:
            self.produto_mov_var.set(
                valores[0] if valores else ""
            )

    def atualizar_movimentacoes(self):
        historico = self.banco.listar_movimentacoes()

        self._preencher_tabela(
            self.movimentacoes_tree,
            historico,
            lambda m: (
                m["data"],
                m["tipo"],
                m["codigo"],
                m["nome"],
                m["categoria"],
                m["quantidade"]
            )
        )

    def atualizar_estoque(self):
        categoria = self.filtro_categoria_var.get()

        categoria = (
            None if not categoria or categoria == "Todas"
            else categoria
        )

        produtos = self.banco.listar_produtos(
            categoria,
            self.busca_var.get()
        )

        self._preencher_tabela(
            self.estoque_tree,
            produtos,
            lambda p: (
                p["codigo"],
                p["nome"],
                p["categoria"],
                moeda(p["preco"]),
                p["quantidade"],
                p["estoque_minimo"],
                moeda(p["preco"] * p["quantidade"])
            ),
            lambda p: (
                ("baixo",)
                if p["quantidade"] <= p["estoque_minimo"]
                else ()
            )
        )

        self.atualizar_relatorio(categoria)

    def atualizar_relatorio(self, categoria=None):
        resumo = self.banco.obter_resumo(categoria)

        self.kpi_produtos.configure(
            text=f'Produtos: {resumo["produtos"]}'
        )

        self.kpi_unidades.configure(
            text=f'Unidades: {resumo["unidades"]}'
        )

        self.kpi_valor.configure(
            text=f'Valor total: {moeda(resumo["valor_total"])}'
        )

        self.kpi_baixo.configure(
            text=f'Estoque baixo: {resumo["estoque_baixo"]}'
        )

        self.grafico.delete("all")

        largura = max(self.grafico.winfo_width(), 500)
        altura = max(self.grafico.winfo_height(), 280)

        categorias = resumo["por_categoria"]

        if not categorias:
            self.grafico.create_text(
                largura / 2,
                altura / 2,
                text="Cadastre produtos para visualizar o relatório.",
                fill="#666"
            )
            return

        margem_esquerda = min(210, largura * 0.32)
        margem_direita = 115
        topo = 18

        altura_linha = max(
            34,
            min(52, (altura - 30) / len(categorias))
        )

        max_valor = max(
            float(item["valor"]) for item in categorias
        ) or 1

        largura_barra = max(
            50,
            largura - margem_esquerda - margem_direita
        )

        for indice, item in enumerate(categorias):
            centro_y = (
                topo + indice * altura_linha + altura_linha / 2
            )

            valor = float(item["valor"])
            barra = largura_barra * valor / max_valor

            self.grafico.create_text(
                margem_esquerda - 10,
                centro_y,
                text=item["categoria"],
                anchor="e",
                fill="#333"
            )

            self.grafico.create_rectangle(
                margem_esquerda,
                centro_y - 10,
                margem_esquerda + barra,
                centro_y + 10,
                fill="#3478b8",
                outline=""
            )

            self.grafico.create_text(
                margem_esquerda + barra + 8,
                centro_y,
                text=moeda(valor),
                anchor="w",
                fill="#333"
            )

    def salvar_produto(self):
        try:
            produto = validar_produto(
                self.codigo_var.get(),
                self.nome_var.get(),
                self.categoria_var.get(),
                self.preco_var.get(),
                self.minimo_var.get()
            )

            if self.editando_codigo:
                self.banco.atualizar_produto(
                    self.editando_codigo,
                    produto
                )
                acao = "atualizado"
            else:
                self.banco.adicionar_produto(produto)
                acao = "cadastrado"

        except (ValueError, sqlite3.IntegrityError) as error:
            mensagem = (
                "Já existe um produto com esse código."
                if isinstance(error, sqlite3.IntegrityError)
                else str(error)
            )

            messagebox.showerror(
                "Não foi possível salvar",
                mensagem,
                parent=self.janela
            )
            return

        self.limpar_formulario()
        self.atualizar_tudo()

        self.status_label.configure(
            text=f"Produto {acao} com sucesso."
        )

    def selecionar_produto(self, _evento=None):
        selecionados = self.produtos_tree.selection()

        if not selecionados:
            return

        codigo, nome, categoria, preco, _qtd, minimo = (
            self.produtos_tree.item(
                selecionados[0],
                "values"
            )
        )

        self.editando_codigo = codigo
        self.codigo_var.set(codigo)
        self.nome_var.set(nome)
        self.categoria_var.set(categoria)

        self.preco_var.set(
            preco.replace("R$ ", "")
            .replace(".", "")
            .replace(",", ".")
        )

        self.minimo_var.set(str(minimo))
        self.codigo_entry.configure(state="disabled")

    def limpar_formulario(self):
        self.editando_codigo = None

        self.codigo_entry.configure(state="normal")

        self.codigo_var.set("")
        self.nome_var.set("")
        self.categoria_var.set("")
        self.preco_var.set("")
        self.minimo_var.set("5")

        for item in self.produtos_tree.selection():
            self.produtos_tree.selection_remove(item)

    def excluir_produto(self):
        selecionados = self.produtos_tree.selection()

        if not selecionados:
            messagebox.showinfo(
                "Excluir produto",
                "Selecione um produto na tabela.",
                parent=self.janela
            )
            return

        codigo = self.produtos_tree.item(
            selecionados[0],
            "values"
        )[0]

        if not messagebox.askyesno(
            "Confirmar exclusão",
            f"Deseja excluir o produto {codigo}?",
            parent=self.janela
        ):
            return

        try:
            self.banco.excluir_produto(codigo)

        except sqlite3.IntegrityError:
            messagebox.showerror(
                "Produto utilizado",
                "Não é possível excluir um produto que possui movimentações registradas.",
                parent=self.janela
            )
            return

        self.limpar_formulario()
        self.atualizar_tudo()

        self.status_label.configure(
            text="Produto excluído."
        )

    def registrar_movimentacao(self):
        codigo = self.produto_por_opcao.get(
            self.produto_mov_var.get()
        )

        if not codigo:
            messagebox.showerror(
                "Movimentação",
                "Cadastre e selecione um produto.",
                parent=self.janela
            )
            return

        tipo = self.tipo_var.get()

        if tipo not in ("entrada", "saida"):
            messagebox.showerror(
                "Movimentação",
                "Selecione entrada ou saída.",
                parent=self.janela
            )
            return

        try:
            quantidade = validar_quantidade(
                self.quantidade_var.get()
            )

            self.banco.registrar_movimentacao(
                codigo,
                tipo,
                quantidade
            )

        except ValueError as error:
            messagebox.showerror(
                "Quantidade inválida",
                str(error),
                parent=self.janela
            )
            return

        except sqlite3.IntegrityError as error:
            message = str(error)

            if "Estoque insuficiente" in message:
                message = (
                    "A quantidade solicitada é maior "
                    "que o estoque disponível."
                )

            elif "FOREIGN KEY" in message:
                message = (
                    "O produto selecionado não foi encontrado."
                )

            messagebox.showerror(
                "Movimentação não registrada",
                message,
                parent=self.janela
            )
            return

        self.quantidade_var.set("")
        self.atualizar_tudo()

        self.status_label.configure(
            text=f"{tipo.capitalize()} registrada com sucesso."
        )

    def exportar_estoque(self):
        categoria = self.filtro_categoria_var.get()

        categoria = (
            None if not categoria or categoria == "Todas"
            else categoria
        )

        produtos = self.banco.listar_produtos(
            categoria,
            self.busca_var.get()
        )

        if not produtos:
            messagebox.showinfo(
                "Exportar relatório",
                "Não há produtos para exportar.",
                parent=self.janela
            )
            return

        caminho = filedialog.asksaveasfilename(
            parent=self.janela,
            title="Salvar relatório de estoque",
            defaultextension=".csv",
            filetypes=(("Arquivo CSV", "*.csv"),),
            initialfile="relatorio_estoque.csv"
        )

        if not caminho:
            return

        exportar_csv(
            caminho,
            (
                "Código",
                "Nome",
                "Categoria",
                "Preço unitário",
                "Quantidade",
                "Estoque mínimo",
                "Valor em estoque"
            ),
            (
                (
                    p["codigo"],
                    p["nome"],
                    p["categoria"],
                    f'{p["preco"]:.2f}'.replace(".", ","),
                    p["quantidade"],
                    p["estoque_minimo"],
                    f'{p["preco"] * p["quantidade"]:.2f}'.replace(".", ",")
                )
                for p in produtos
            )
        )

        self.status_label.configure(
            text=f"Relatório exportado: {caminho}"
        )

        messagebox.showinfo(
            "Exportação concluída",
            "O relatório CSV foi salvo.",
            parent=self.janela
        )


def main():
    janela = tk.Tk()

    try:
        AplicacaoEstoque(janela)

    except (OSError, sqlite3.Error) as error:
        messagebox.showerror(
            "Falha ao iniciar",
            f"Não foi possível inicializar o banco de dados:\n{error}",
            parent=janela
        )

        janela.destroy()
        return

    janela.mainloop()


if __name__ == "__main__":
    main()
'''