import os
import psycopg
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

def limpar_tabelas(conn):
    conn.execute("TRUNCATE itens_pedido, pedidos, clientes, produtos")

if __name__ == "__main__":
    import json
    from etl.transformacao import transformar_produto

    with open("brutos/produtos.json", encoding="utf-8") as f:
        produtos = [transformar_produto(p) for p in json.load(f)]

    with conectar() as conn:
        limpar_tabelas(conn)
        carregar_produtos(conn, produtos)
        print(conn.execute("SELECT count(*) FROM produtos").fetchone())