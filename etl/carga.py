import os
import psycopg
import json
from dotenv import load_dotenv

load_dotenv()

def conectar():
    return psycopg.connect(
        host="localhost",
        port=os.environ["DB_PORT"],
        dbname=os.environ["DB_NAME"],
        user=os.environ["DB_USER"],
        password=os.environ["DB_PASSWORD"],
    )

def carregar_produtos(conn, produtos):
    """Carrega os produtos no banco de dados."""
    sql = "INSERT INTO produtos (produto_id, nome, categoria, preco_base) VALUES (%s, %s, %s, %s)"
    linhas = [(p["produto_id"], p["nome"], p["categoria"], p["preco_base"]) for p in produtos]
    conn.cursor().executemany(sql, linhas)

def carregar_clientes(conn, clientes):
    """Carrega os clientes no banco de dados."""
    sql = "INSERT INTO clientes (id, nome, email, cidade, estado, cadastro_em) VALUES (%s, %s, %s, %s, %s, %s)"
    linhas = [(c["id"], c["nome"], c["email"], c["cidade"], c["estado"], c["cadastro_em"]) for c in clientes]
    conn.cursor().executemany(sql, linhas)

def carregar_pedidos(conn, pedidos):
    sql = "INSERT INTO pedidos (id, cliente_id, data_pedido, status, valor_total, valor_itens, divergente) VALUES (%s, %s, %s, %s, %s, %s, %s)" 
    linhas = [(p["id"], p["cliente_id"], p["data_pedido"], p["status"], p["valor_total"], p["valor_itens"], p["divergente"]) for p in pedidos]
    conn.cursor().executemany(sql, linhas)

def carregar_itens(conn, itens):
    sql = "INSERT INTO itens_pedido (pedido_id, linha, produto_id, quantidade, preco_unitario) VALUES (%s, %s, %s, %s, %s)"
    linhas = [(i["pedido_id"], i["linha"], i["produto_id"], i["quantidade"], i["preco_unitario"]) for i in itens]
    conn.cursor().executemany(sql, linhas)

def contar(conn, tabela): 
    """Conta a quantidade de registros em uma tabela."""
    return conn.execute(f"SELECT count(*) FROM {tabela}").fetchone()[0]

def carregar(dados):
    """Limpa e carrega as quatro tabelas, na ordem das chaves estrangeiras."""
    with conectar() as conn:
        limpar_tabelas(conn)
        carregar_produtos(conn, dados["produtos"])
        carregar_clientes(conn, dados["clientes"])
        carregar_pedidos(conn, dados["pedidos"])
        carregar_itens(conn, dados["itens"])
        print(
            f"carga: clientes={contar(conn, 'clientes')}, produtos={contar(conn, 'produtos')}, pedidos={contar(conn, 'pedidos')}, itens={contar(conn, 'itens_pedido')}"
        )

def limpar_tabelas(conn):
    conn.execute("TRUNCATE itens_pedido, pedidos, clientes, produtos")

if __name__ == "__main__":
    from etl.transformacao import transformar

    with open("brutos/clientes.json", encoding="utf-8") as f:
        clientes = json.load(f)
    with open("brutos/produtos.json", encoding="utf-8") as f:
        produtos = json.load(f)

    with open("brutos/pedidos.json", encoding="utf-8") as f:
        pedidos = json.load(f)

    carregar(transformar(clientes, pedidos, produtos))
