# Sugestões aceitas

- Parar o loop pelo `total_pages`. Eu tinha tentado parar quando a página viesse vazia, mas a IA sugeriu usar o `total_pages` que já vem na resposta da API, que é mais direto.
- Separar os erros de conexão, timeout e 404. Eu tinha feito um `try/except Exception` genérico, e a IA sugeriu separar pra mensagem dizer o que aconteceu de verdade.
- Usar `Decimal` em vez de `float` nos valores de dinheiro na transformação. Eu ia usar `float`, mas a IA explicou que `float` tem erro de arredondamento em binário e podia quebrar a checagem de 1 centavo da divergência e a soma da reconciliação.

# Sugestões rejeitadas

# Falhas

# Retrabalho

