import json
from decimal import Decimal

import psycopg
import pytest

from etl.carga import conectar

TOLERANCIA = Decimal("0.01")

@pytest.fixture(scope="module")
def conn():
    try:
        conexao = conectar()
    except psycopg.OperationalError:
        pytest.skip("banco indisponível: suba o contêiner e rode o ETL antes")
    yield conexao
    conexao.close()

@pytest.fixture(scope="module")
def pedidos_origem():
    """Pedidos únicos da origem (primeira ocorrência de cada id), lidos de brutos/."""
    try:
        with open("brutos/pedidos.json", encoding="utf-8") as f:
            brutos = json.load(f)
    except FileNotFoundError:
        pytest.skip("brutos/pedidos.json não existe: rode o ETL antes")
    unicos = {}
    for pedido in brutos:
        unicos.setdefault(pedido["id"], pedido)
    return list(unicos.values())

def valor_itens_origem(pedido):
    """Soma quantidade * preço dos itens, direto da origem (sem usar o ETL)."""
    return sum(
        (item["quantidade"] * Decimal(str(item["preco_unitario"])) for item in pedido["itens"]),
        Decimal("0"),
    )

def test_contagem_de_pedidos_unicos_bate(conn, pedidos_origem):
    no_banco = conn.execute("SELECT count(*) FROM pedidos").fetchone()[0]
    assert no_banco == len(pedidos_origem)

def test_contagem_de_itens_bate(conn, pedidos_origem):
    esperado = sum(len(p["itens"]) for p in pedidos_origem)
    no_banco = conn.execute("SELECT count(*) FROM itens_pedido").fetchone()[0]
    assert no_banco == esperado

def test_soma_de_valor_itens_bate(conn, pedidos_origem):
    origem = sum((valor_itens_origem(p) for p in pedidos_origem), Decimal("0"))
    destino = conn.execute("SELECT sum(valor_itens) FROM pedidos").fetchone()[0]
    assert abs(origem - destino) <= TOLERANCIA

def test_soma_dos_itens_na_tabela_de_itens_bate(conn, pedidos_origem):
    origem = sum((valor_itens_origem(p) for p in pedidos_origem), Decimal("0"))
    destino = conn.execute("SELECT sum(quantidade * preco_unitario) FROM itens_pedido").fetchone()[0]
    assert abs(origem - destino) <= TOLERANCIA

def test_consulta_vendas_por_mes_soma_o_total_geral(conn):
    """Teste de consulta: a soma dos meses tem que ser igual à soma geral da tabela."""
    por_mes = conn.execute(
        "SELECT date_trunc('month', data_pedido) AS mes, sum(valor_total) "
        "FROM pedidos GROUP BY mes"
    ).fetchall()
    soma_dos_meses = sum((total for _, total in por_mes), Decimal("0"))
    total_geral = conn.execute("SELECT sum(valor_total) FROM pedidos").fetchone()[0]
    assert abs(soma_dos_meses - total_geral) <= TOLERANCIA