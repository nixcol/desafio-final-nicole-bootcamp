from datetime import datetime
from decimal import Decimal

CENTAVO = Decimal("0.01")

def para_decimal(valor):
    """Converte número ou texto para Decimal com 2 casas."""
    if isinstance(valor, str):
        valor = valor.strip().replace(",", ".")
    return Decimal(str(valor)).quantize(CENTAVO)

def tratar_email(cliente):
    """A1: e-mail ausente ou vazio vira None."""
    email = cliente.get("email")
    if isinstance(email, str):
        email = email.strip()
    novo = cliente.copy()
    novo["email"] = email or None  # "" e None viram None
    return novo

def padronizar_estado(cliente):
    """A2: sigla do estado sempre em maiúsculas."""
    novo = cliente.copy()
    novo["estado"] = cliente["estado"].strip().upper()
    return novo

def transformar_cliente(cliente):
    return padronizar_estado(tratar_email(cliente))

def transformar_produto(produto):
    """Converte os textos do CSV: produto_id vira inteiro, preco_base vira Decimal."""
    novo = produto.copy()
    novo["produto_id"] = int(produto["produto_id"])
    novo["preco_base"] = para_decimal(produto["preco_base"])
    return novo

def converter_data(pedido):
    """A3: data_pedido em AAAA-MM-DD ou DD/MM/AAAA vira sempre AAAA-MM-DD."""
    texto = pedido["data_pedido"].strip()
    formato = "%d/%m/%Y" if "/" in texto else "%Y-%m-%d"
    data = datetime.strptime(texto, formato)  # data inválida levanta ValueError
    novo = pedido.copy()
    novo["data_pedido"] = data.strftime("%Y-%m-%d")
    return novo

def converter_valor_total(pedido):
    """A4: valor_total (número ou texto com vírgula) vira Decimal com 2 casas."""
    novo = pedido.copy()
    novo["valor_total"] = para_decimal(pedido["valor_total"])
    return novo

def remover_repetidos(pedidos):
    """A5: mantém só a primeira ocorrência de cada id de pedido."""
    vistos = set()
    unicos = []
    for pedido in pedidos:
        if pedido["id"] not in vistos:
            vistos.add(pedido["id"])
            unicos.append(pedido)
    return unicos

def calcular_valor_itens(pedido):
    """A6: valor_itens = soma de quantidade * preco_unitario."""
    soma = sum(
        (item["quantidade"] * para_decimal(item["preco_unitario"]) for item in pedido["itens"]),
        Decimal("0.00"),
    )
    novo = pedido.copy()
    novo["valor_itens"] = soma.quantize(CENTAVO)
    return novo

def marcar_divergencia(pedido):
    """A6: divergente é True se |valor_total - valor_itens| > 0,01."""
    diferenca = abs(pedido["valor_total"] - pedido["valor_itens"])
    novo = pedido.copy()
    novo["divergente"] = diferenca > CENTAVO
    return novo

def transformar_pedido(pedido):
    pedido = converter_data(pedido)
    pedido = converter_valor_total(pedido)
    pedido = calcular_valor_itens(pedido)
    return marcar_divergencia(pedido)

def gerar_itens(pedido):
    """Transforma os itens aninhados do pedido em linhas da tabela itens_pedido.

    pedido_id vem do pedido; linha é a posição do item (1, 2, 3...).
    """
    return [
        {
            "pedido_id": pedido["id"],
            "linha": numero,
            "produto_id": item["produto_id"],
            "quantidade": item["quantidade"],
            "preco_unitario": para_decimal(item["preco_unitario"]),
        }
        for numero, item in enumerate(pedido["itens"], start=1)
    ]

def transformar(clientes_brutos, pedidos_brutos, produtos_brutos):
    """Aplica todas as transformações, imprime os contadores e devolve os dados."""
    produtos = [transformar_produto(p) for p in produtos_brutos]

    clientes = []
    emails_nulos = 0
    estados_padronizados = 0
    for bruto in clientes_brutos:
        tratado = transformar_cliente(bruto)
        if tratado["email"] is None:
            emails_nulos += 1
        if tratado["estado"] != bruto["estado"]:
            estados_padronizados += 1
        clientes.append(tratado)

    unicos = remover_repetidos(pedidos_brutos)
    repetidos_descartados = len(pedidos_brutos) - len(unicos)

    pedidos = []
    itens = []
    datas_convertidas = 0
    valores_convertidos = 0
    divergentes = 0
    for bruto in unicos:
        tratado = transformar_pedido(bruto)
        if tratado["data_pedido"] != bruto["data_pedido"]:
            datas_convertidas += 1
        if isinstance(bruto["valor_total"], str):
            valores_convertidos += 1
        if tratado["divergente"]:
            divergentes += 1
        pedidos.append(tratado)
        itens.extend(gerar_itens(tratado))

    print(f"transformacao: pedidos_unicos={len(pedidos)} repetidos_descartados={repetidos_descartados}")
    print(
        f"transformacao: emails_nulos={emails_nulos} estados_padronizados={estados_padronizados} "
        f"datas_convertidas={datas_convertidas} valores_convertidos={valores_convertidos}"
    )
    print(f"divergentes: {divergentes} pedidos com valor_total diferente da soma dos itens")

    return {
        "clientes": clientes,
        "produtos": produtos,
        "pedidos": pedidos,
        "itens": itens,
    }