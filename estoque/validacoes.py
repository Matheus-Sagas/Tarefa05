"""Validações compartilhadas pela interface do sistema."""

import math


def validar_produto(codigo, nome, categoria, preco, estoque_minimo):
    codigo = codigo.strip()
    nome = nome.strip()
    categoria = categoria.strip()

    if not codigo:
        raise ValueError("Informe o código do produto.")
    if not nome:
        raise ValueError("Informe o nome do produto.")
    if not categoria:
        raise ValueError("Informe a categoria do produto.")

    try:
        preco = float(str(preco).strip().replace(",", "."))
    except ValueError as error:
        raise ValueError("O preço deve ser um número válido.") from error
    if not math.isfinite(preco) or preco < 0:
        raise ValueError("O preço não pode ser negativo.")

    try:
        estoque_minimo = int(estoque_minimo)
    except (TypeError, ValueError) as error:
        raise ValueError("O estoque mínimo deve ser um número inteiro.") from error
    if estoque_minimo < 0:
        raise ValueError("O estoque mínimo não pode ser negativo.")

    return {
        "codigo": codigo,
        "nome": nome,
        "categoria": categoria,
        "preco": preco,
        "estoque_minimo": estoque_minimo,
    }


def validar_quantidade(quantidade):
    try:
        quantidade = int(quantidade)
    except (TypeError, ValueError) as error:
        raise ValueError("A quantidade deve ser um número inteiro.") from error
    if quantidade <= 0:
        raise ValueError("A quantidade deve ser maior que zero.")
    return quantidade
