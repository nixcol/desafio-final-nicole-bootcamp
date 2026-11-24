from decimal import Decimal
import pytest

from etl.transformacao import (
    calcular_valor_itens,
    converter_data, 
    converter_valor_total,
    gerar_itens,
    marcar_divergencia,
    padronizar_estado,
    remover_repetidos,
    transformar,
    transformar_produto,
    tratar_email,
)

def pedido_exemplo(**campos):
    pedido = {
        "id": 1,
        "cliente_id": 10,
        "data_pedido": "2026-02-19",
        "status": "entregue",
        "valor_total": "20,00",
        "itens": [
            {"produto_id": 1, "quantidade": 2, "preco_unitario": 4.3},
            {"produto_id": 2, "quantidade": 1, "preco_unitario": 11.4},
        ],
    }
    pedido.update(campos)
    return pedido

# A1: e-mail ausente
def test_a1_email_nulo_ou_vazio_vira_none():
    assert tratar_email({"id": 1, "email": None})["email"] is None
    assert tratar_email({"id": 1, "email": "  "})["email"] is None


def test_a1_email_preenchido_nao_muda():
    assert tratar_email({"id": 1, "email": "ana@ex.com"})["email"] == "ana@ex.com"

# A2: estado em maiúsculas
def test_a2_estado_vira_maiusculo():
    assert padronizar_estado({"estado": "rs"})["estado"] == "RS"
    assert padronizar_estado({"estado": "SP"})["estado"] == "SP"

def test_a2_nao_altera_o_original():
    cliente = {"id": 1, "estado": " rs "}
    padronizar_estado(cliente)
    assert cliente == {"id": 1, "estado": " rs "}

# A3: data em dois formatos
def test_a3_data_iso_permanece():
    assert converter_data({"data_pedido": "2026-02-19"})["data_pedido"] == "2026-02-19"

def test_a3_data_brasileira_vira_iso():
    assert converter_data({"data_pedido": "19/02/2026"})["data_pedido"] == "2026-02-19"

def test_a3_data_invalida_levanta_erro():
    with pytest.raises(ValueError):
        converter_data({"data_pedido": "32/13/2026"})

# A4: valor com vírgula
def test_a4_valor_com_virgula_vira_decimal():
    assert converter_valor_total({"valor_total": "125,84"})["valor_total"] == Decimal("125.84")

def test_a4_valor_numerico_vira_decimal_com_duas_casas():
    assert converter_valor_total({"valor_total": 94.34})["valor_total"] == Decimal("94.34")
    assert converter_valor_total({"valor_total": 10})["valor_total"] == Decimal("10.00")

# A5: pedidos repetidos
def test_a5_repetido_mantem_a_primeira_ocorrencia():
    pedidos = [
        {"id": 1, "status": "entregue"},
        {"id": 2, "status": "cancelado"},
        {"id": 1, "status": "entregue"},
    ]
    assert remover_repetidos(pedidos) == [
        {"id": 1, "status": "entregue"},
        {"id": 2, "status": "cancelado"},
    ]

# A6: valor_itens e divergência
def test_a6_valor_itens_e_a_soma_de_quantidade_vezes_preco():
    # 2 * 4,30 + 1 * 11,40 = 20,00
    assert calcular_valor_itens(pedido_exemplo())["valor_itens"] == Decimal("20.00")

@pytest.mark.parametrize(
    "valor_total, esperado",
    [
        ("20,00", False),  # igual
        ("20,01", False),  # diferença de 1 centavo não conta
        ("20,02", True),   # mais de 1 centavo
        ("15,00", True),   # total menor que a soma dos itens
    ],
)
def test_a6_divergencia(valor_total, esperado):
    pedido = converter_valor_total(pedido_exemplo(valor_total=valor_total))
    pedido = calcular_valor_itens(pedido)
    assert marcar_divergencia(pedido)["divergente"] is esperado

# Produtos e itens
def test_produto_converte_tipos():
    produto = transformar_produto(
        {"produto_id": "3", "nome": "Tomate", "categoria": "legumes", "preco_base": "8.9"}
    )
    assert produto["produto_id"] == 3
    assert produto["preco_base"] == Decimal("8.90")

def test_itens_ganham_pedido_id_e_linha():
    itens = gerar_itens(pedido_exemplo(id=7))
    assert [i["pedido_id"] for i in itens] == [7, 7]
    assert [i["linha"] for i in itens] == [1, 2]
    assert itens[0]["preco_unitario"] == Decimal("4.30")

# Conjunto
def test_transformar_imprime_os_contadores(capsys):
    clientes = [
        {"id": 1, "email": None, "estado": "rs"},
        {"id": 2, "email": "a@b.com", "sestado": "SP"},
    ]
    pedidos = [
        pedido_exemplo(id=1, data_pedido="19/02/2026", valor_total="25,00"),
        pedido_exemplo(id=1, data_pedido="19/02/2026", valor_total="25,00"),
        pedido_exemplo(id=2, valor_total="20,00"),
    ]
    produtos = [{"produto_id": "1", "nome": "A", "categoria": "x", "preco_base": "1.0"}]

    resultado = transformar(clientes, pedidos, produtos)
    saida = capsys.readouterr().out

    assert len(resultado["pedidos"]) == 2
    assert len(resultado["itens"]) == 4
    assert "transformacao: pedidos_unicos=2 repetidos_descartados=1" in saida
    assert (
        "transformacao: emails_nulos=1 estados_padronizados=1 "
        "datas_convertidas=1 valores_convertidos=2" in saida
    )
    assert "divergentes: 1 pedidos com valor_total diferente da soma dos itens" in saida