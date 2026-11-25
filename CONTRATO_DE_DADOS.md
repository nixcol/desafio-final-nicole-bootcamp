# Contrato de dados

Descreve as tabelas de destino (baseadas no `insumos/schema.sql`): campo, tipo, se aceita nulo, de onde vem e a regra aplicada. 

## clientes

| Campo | Tipo | Aceita nulo? | Origem | Regra |
|---|---|---|---|---|
| id | INTEGER (PK) | Não | API | Vem direto. |
| nome | TEXT | Não | API | Vem direto. |
| email | TEXT | **Sim** | API | Se nulo ou vazio, manter o cliente e gravar `NULL` . |
| cidade | TEXT | Não | API | Vem direto. |
| estado | CHAR(2) | Não | API | **A2:** Texto de 2 letras, obrigatório, sempre em maiúsculas. |
| cadastro_em | DATE | Não | API | Já vem como `AAAA-MM-DD`, só converter o texto para data. |

## produtos

| Campo | Tipo | Aceita nulo? | Origem | Regra |
|---|---|---|---|---|
| produto_id | INTEGER (PK) | Não | CSV | Texto convertido para inteiro. |
| nome | TEXT | Não | CSV | Vem direto. |
| categoria | TEXT | Não | CSV | Vem direto (`folhas`, `legumes`, `frutas`). |
| preco_base | NUMERIC(10,2) | Não | CSV | Texto convertido para número com 2 casas. |

## pedidos

| Campo | Tipo | Aceita nulo? | Origem | Regra |
|---|---|---|---|---|
| id | INTEGER (PK) | Não | API | Carregar cada pedido uma única vez, pelo `id`. |
| cliente_id | INTEGER (FK para clientes.id) | Não | API | Precisa existir em `clientes`. |
| data_pedido | DATE | Não | API | Vem em dois formatos, `AAAA-MM-DD` e `DD/MM/AAAA`. Converter os dois para o tipo de data (`AAAA-MM-DD`). |
| status | TEXT | Não | API | Vem direto (`entregue`, `em_transporte`, `cancelado`). |
| valor_total | NUMERIC(12,2) | Não | API | Pode vir ora como número, ora como texto com vírgula. Converter tudo para número com duas casas. Mantém o valor informado, mesmo quando diverge dos itens. |
| valor_itens | NUMERIC(12,2) | Não | **Calculado** | Soma de `quantidade * preco_unitario` dos itens do pedido, com 2 casas. |
| divergente | BOOLEAN (padrão FALSE) | Não | **Calculado** | `TRUE` se o valor absoluto da diferença entre `valor_total` e `valor_itens` for maior que 0,01 senão `FALSE`. |

## itens_pedido

| Campo | Tipo | Aceita nulo? | Origem | Regra |
|---|---|---|---|---|
| pedido_id | INTEGER (PK, FK para pedidos.id) | Não | API | `id` do pedido a que o item pertence. |
| linha | INTEGER (PK) | Não | **Gerado** | Posição do item dentro do pedido, começando em 1. |
| produto_id | INTEGER (FK para produtos.produto_id) | Não | API | Precisa existir em `produtos`. |
| quantidade | INTEGER | Não | API | Vem direto. |
| preco_unitario | NUMERIC(10,2) | Não | API | Vem como número, arredondar para 2 casas. |

Os itens entram uma vez por pedido. Os pedidos repetidos são descartados antes, e os itens das cópias não são gravados.


## Armadilhas e como o ETL trata cada uma

| Código | Problema nos dados | Onde | Como é tratado |
|---|---|---|---|
| A1 | E-mail ausente | clientes.email | Cliente mantido e e-mail `NULL`. |
| A2 | Estado em maiúscula e minúscula | clientes.estado | Padronizado para maiúsculas antes da carga. |
| A3 | Dois formatos de data | pedidos.data_pedido | Os dois convertidos para o tipo de data do banco. |
| A4 | Valor total como número ou texto com vírgula | pedidos.valor_total | Convertido para número com duas casas. |
| A5 | Pedidos repetidos entre páginas | pedidos.id | Carregado uma única vez, sem duplicar ao rodar de novo. |
| A6 | Valor total diferente da soma dos itens | pedidos.valor_itens e pedidos.divergente | Grava os dois valores e marca `divergente`. |
