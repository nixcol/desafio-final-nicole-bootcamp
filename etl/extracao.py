import csv
import json
import os

import requests

URL_API = "http://127.0.0.1:8000"
PASTA_BRUTOS = "brutos"

def buscar_paginas(rota, page_size=50):
    """Busca todas as páginas de uma rota da API. Devolve uma tupla (itens, total_pages). Se der algum erro, mostra a
    mensagem e devolve None.
    """
    itens = []
    page = 1
    total_pages = 1

    while page <= total_pages:
        try:
            resp = requests.get(
                f"{URL_API}/{rota}",
                params={"page": page, "page_size": page_size},
                timeout=10,
            )
        except requests.exceptions.ConnectionError:
            print(f"Erro: não consegui conectar na API ({URL_API}). Ela está rodando?")
            return None
        except requests.exceptions.Timeout:
            print(f"Erro: a API demorou demais para responder em /{rota}.")
            return None
        except requests.exceptions.RequestException as e:
            print(f"Erro na requisição de /{rota}: {e}")
            return None

        if resp.status_code == 404:
            print(f"Erro: a página {page} de /{rota} não existe (404).")
            return None
        if resp.status_code != 200:
            print(f"Erro: /{rota}, página {page}, retornou status {resp.status_code}.")
            return None

        try:
            dados = resp.json()
            total_pages = dados["total_pages"]
            itens += dados["items"]
        except (ValueError, KeyError):
            print(f"Erro: resposta inválida da API em /{rota}, página {page}.")
            return None

        page += 1

    return itens, total_pages


def salvar_bruto(nome, dados):
    """Salva os dados crus em brutos/<nome>.json, para poder reprocessar depois sem chamar a API de novo."""
    os.makedirs(PASTA_BRUTOS, exist_ok=True)
    caminho = os.path.join(PASTA_BRUTOS, nome + ".json")
    with open(caminho, "w", encoding="utf-8") as f:
        json.dump(dados, f, ensure_ascii=False, indent=2)


def ler_produtos(caminho="insumos/dados/produtos.csv"):
    """Lê o produtos.csv e devolve uma lista de dicionários. Devolve None se o arquivo não existir.
    """
    try:
        with open(caminho, newline="", encoding="utf-8") as f:
            return list(csv.DictReader(f))
    except FileNotFoundError:
        print(f"Arquivo de produtos não encontrado: {caminho}")
        return None


def extrair():
    """Extrai clientes, pedidos e produtos, salva os brutos e devolve tudo num dicionário. Devolve None se alguma etapa falhar."""
    resultado = {}

    for rota in ["clientes", "pedidos"]:
        busca = buscar_paginas(rota)
        if busca is None:
            return None
        dados, total_pages = busca
        salvar_bruto(rota, dados)
        resultado[rota] = dados

        # resumo da rota, uma linha só
        nome_registros = "registros_brutos" if rota == "pedidos" else "registros"
        print(f"extracao: {rota} paginas={total_pages} {nome_registros}={len(dados)}")

    produtos = ler_produtos()
    if produtos is None:
        return None
    salvar_bruto("produtos", produtos)
    resultado["produtos"] = produtos

    return resultado


if __name__ == "__main__":
    extrair()
