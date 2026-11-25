-- (a) Total de vendas por mês (soma de valor_total)
SELECT date_trunc('month', data_pedido)::date AS mes,
       sum(valor_total)                       AS total_vendas
FROM pedidos
GROUP BY 1
ORDER BY 1;

-- (b) Quantidade de pedidos por estado do cliente
SELECT c.estado,
       count(*) AS pedidos
FROM pedidos p
JOIN clientes c ON c.id = p.cliente_id
GROUP BY c.estado
ORDER BY pedidos DESC, c.estado;

-- (c) Pedidos divergentes: valor_total diferente da soma dos itens
SELECT id,
       cliente_id,
       valor_total,
       valor_itens,
       valor_total - valor_itens AS diferenca
FROM pedidos
WHERE divergente
ORDER BY id;