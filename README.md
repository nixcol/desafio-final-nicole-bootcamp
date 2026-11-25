# ETL da Verdejar

Este projeto fictício leva os dados da Verdejar para um banco PostgreSQL. Os clientes e os pedidos vêm de uma API local, os produtos vêm de um CSV. O ETL extrai, limpa, carrega e confere o resultado. Todos os dados são sintéticos.

## Como o banco foi montado

Usei o **caminho B**: PostgreSQL 16 em um contêiner Docker. A conexão é feita pela biblioteca **psycopg**. As demais dependências são `requests` (chamadas à API), `python-dotenv` (leitura do `.env`) e `pytest`. Todas estão em `requirements.txt`.

A senha e os dados de conexão ficam no arquivo `.env`, que não é versionado. 

## Como rodar

Na raiz do projeto, com o Python 3 instalado:

```
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

Suba o banco e aplique o esquema (o `docker run` vai em uma linha só; troque a senha pela mesma do `.env`):

```
docker run --name verdejar-pg -e POSTGRES_PASSWORD=<senha> -e POSTGRES_DB=verdejar -p 5432:5432 -d postgres:16
docker exec -i verdejar-pg psql -U postgres -d verdejar < insumos/schema.sql
```

Em outro terminal, suba a API local e deixe rodando:

```
python3 insumos/api_verdejar.py --dados insumos/dados
```

Com a API e o banco no ar, execute o ETL:

```
python3 -m etl.main
```

Para rodar os testes e as consultas de validação:

```
python3 -m pytest -q tests
docker exec -i verdejar-pg psql -U postgres -d verdejar < consultas_validacao.sql
```

Os testes de reconciliação (`tests/test_reconciliacao.py`) precisam do banco no ar e do ETL já executado. Sem isso, eles são pulados.

## Estrutura

```
etl/extracao.py        extração paginada da API e leitura do CSV; salva os brutos em brutos/
etl/transformacao.py   funções de limpeza (A1 a A6), produtos e itens
etl/carga.py           carga no PostgreSQL
etl/main.py            executa as três etapas na ordem
tests/                 testes de transformação e de reconciliação
CONTRATO_DE_DADOS.md   campos, tipos e regras de cada tabela de destino
consultas_validacao.sql
COMO_USEI_IA.md        registro do uso de IA
```

A pasta `brutos/` guarda uma cópia do que a API e o CSV devolveram, antes de qualquer transformação. Ela está no `.gitignore`.

## Idempotência

A carga apaga as quatro tabelas com `TRUNCATE` e insere tudo de novo, na ordem das chaves estrangeiras (produtos, clientes, pedidos, itens). Tudo acontece em uma única transação e o `commit` só ocorre se todas as inserções terminarem. Como o ETL extrai a origem inteira a cada execução, o banco sempre fica igual ao retrato da origem, e rodar duas vezes seguidas produz as mesmas contagens.

Duas execuções seguidas imprimem a mesma linha final:

```
carga: clientes=1000, produtos=12, pedidos=5000, itens=12455
carga: clientes=1000, produtos=12, pedidos=5000, itens=12455
```

## Saída do ETL

```
extracao: clientes paginas=20 registros=1000
extracao: pedidos paginas=102 registros_brutos=5100
transformacao: pedidos_unicos=5000 repetidos_descartados=100
transformacao: emails_nulos=81 estados_padronizados=151 datas_convertidas=1037 valores_convertidos=1255
divergentes: 238 pedidos com valor_total diferente da soma dos itens
carga: clientes=1000, produtos=12, pedidos=5000, itens=12455
```

## Decisões de transformação

- **Valores em dinheiro** usam `Decimal` com duas casas, e não `float`, para evitar erros de arredondamento nas somas e nas comparações.
- **Datas** são lidas nos dois formatos (`AAAA-MM-DD` e `DD/MM/AAAA`) e gravadas como `AAAA-MM-DD`. Uma data inválida levanta erro em vez de ser gravada.
- **Pedidos repetidos** (mesmo `id`) são descartados antes de gerar os itens, mantendo a primeira ocorrência. 
- **Itens** vêm aninhados dentro de cada pedido na API. A coluna `linha` é a posição do item no pedido, começando em 1.
- **Divergência**: um pedido é marcado como divergente quando a diferença absoluta entre `valor_total` e `valor_itens` passa de um centavo. Os dois valores são gravados como vieram, sem correção.

## Resultados das consultas de validação

Rodei as três consultas de `consultas_validacao.sql` depois da carga.

**(a) Total de vendas por mês** (soma de `valor_total`, todos os status):

| mês | total de vendas |
|---|---|
| 2026-01 | 30449.02 |
| 2026-02 | 33923.86 |
| 2026-03 | 30678.70 |
| 2026-04 | 31253.96 |
| 2026-05 | 30890.02 |
| 2026-06 | 31627.73 |
| 2026-07 | 32796.17 |
| 2026-08 | 29328.04 |
| 2026-09 | 29995.71 |
| 2026-10 | 31104.54 |

A soma dos dez meses é 312047.75, igual à soma geral de `valor_total` na tabela. Essa conferência é feita automaticamente pelo teste `test_consulta_vendas_por_mes_soma_o_total_geral`. Os 1016 pedidos cancelados entram nessa soma; se a análise de vendas precisar excluí-los, basta filtrar por `status`.

**(b) Pedidos por estado:**

| estado | pedidos |
|---|---|
| RS | 1543 |
| SC | 1127 |
| PR | 974 |
| SP | 880 |
| MG | 476 |

A soma é 5000, o total de pedidos carregados.

**(c) Pedidos divergentes:** 238 pedidos. As diferenças entre `valor_total` e `valor_itens` são sempre de 3, 5 ou 10 reais, para mais ou para menos. Os primeiros da lista:

| id | valor_total | valor_itens | diferença |
|---|---|---|---|
| 1 | 125.84 | 130.84 | -5.00 |
| 51 | 26.58 | 23.58 | 3.00 |
| 71 | 144.35 | 134.35 | 10.00 |
| 81 | -1.84 | 3.16 | -5.00 |
| 106 | 47.78 | 44.78 | 3.00 |

## Observações sobre os dados

O pedido 81 tem `valor_total` negativo (-1.84), e é o único entre os 5000. Isso não está entre as seis armadilhas declaradas. Um total negativo é suspeito e mereceria uma conversa com quem mantém o sistema de origem.

## Testes

Os testes de transformação cobrem as seis armadilhas, os produtos e a geração dos itens. Os de reconciliação comparam a origem com o banco: contagem de pedidos e de itens, e a soma de `valor_itens`, com tolerância de um centavo.

Última linha da execução do `pytest`:

```
23 passed
```

## O que eu faria com mais tempo

Adicionaria uma carga incremental por data, para não recarregar tudo a cada execução, e uma validação explícita de totais negativos antes da carga.