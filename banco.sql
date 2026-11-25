PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS produtos (
    codigo TEXT PRIMARY KEY,
    nome TEXT NOT NULL,
    categoria TEXT NOT NULL,
    preco REAL NOT NULL CHECK (preco >= 0),
    quantidade INTEGER NOT NULL DEFAULT 0 CHECK (quantidade >= 0),
    estoque_minimo INTEGER NOT NULL DEFAULT 5 CHECK (estoque_minimo >= 0)
);

CREATE TABLE IF NOT EXISTS movimentacoes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    produto_codigo TEXT NOT NULL,
    tipo TEXT NOT NULL CHECK (tipo IN ('entrada', 'saida')),
    quantidade INTEGER NOT NULL CHECK (quantidade > 0),
    data TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (produto_codigo) REFERENCES produtos(codigo)
        ON UPDATE CASCADE ON DELETE RESTRICT
);

CREATE INDEX IF NOT EXISTS idx_movimentacoes_data
    ON movimentacoes(data DESC);
CREATE INDEX IF NOT EXISTS idx_movimentacoes_produto
    ON movimentacoes(produto_codigo);

CREATE TRIGGER IF NOT EXISTS validar_saida_estoque
BEFORE INSERT ON movimentacoes
WHEN NEW.tipo = 'saida'
 AND NEW.quantidade > (
     SELECT quantidade FROM produtos WHERE codigo = NEW.produto_codigo
 )
BEGIN
    SELECT RAISE(ABORT, 'Estoque insuficiente para registrar a saída.');
END;

CREATE TRIGGER IF NOT EXISTS atualizar_estoque_movimentacao
AFTER INSERT ON movimentacoes
BEGIN
    UPDATE produtos
    SET quantidade = quantidade +
        CASE NEW.tipo
            WHEN 'entrada' THEN NEW.quantidade
            WHEN 'saida' THEN -NEW.quantidade
        END
    WHERE codigo = NEW.produto_codigo;
END;
