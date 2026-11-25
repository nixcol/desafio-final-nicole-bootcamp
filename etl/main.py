import psycopg

from etl.carga import carregar
from etl.extracao import extrair
from etl.transformacao import transformar

def main():
    dados = extrair()
    if dados is None:
        print("ETL interrompido: a extração falhou.")
        return 1

    tratados = transformar(dados["clientes"], dados["pedidos"], dados["produtos"])

    try:
        carregar(tratados)
    except psycopg.OperationalError as erro:
        print(f"ETL interrompido: não conseguiu usar o banco ({erro}).")
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())