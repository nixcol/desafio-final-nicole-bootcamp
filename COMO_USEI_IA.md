# Como usei a IA

Usei a IA praticamente em formato de pair programming durante o desafio, indo etapa por etapa. A ideia foi usar a ferramenta pra destravar partes que eu não dominava bem, mas sempre revisando e testando cada pedaço pra ter certeza de que eu entendia o que estava rodando.

No geral, os principais pontos em que a IA ajudou foram:

- **Esqueleto das funções e organização do código**: usei a IA pra montar a estrutura inicial dos módulos (`extracao.py`, `transformacao.py` e `carga.py`) e pensar em como quebrar cada armadilha (A1 a A6) em funções pequenas e fáceis de ler, em vez de deixar tudo misturado num bloco só.
- **Explicação de conceitos**: sempre que aparecia alguma dúvida mais técnica (como a diferença entre `Decimal` e `float` pra dinheiro, como funciona transação e rollback no `psycopg`, ordem de chaves estrangeiras no PostgreSQL e como garantir idempotência na carga) eu pedia pra IA explicar.
- **Criação dos testes automatizados**: essa foi a parte em que mais precisei de ajuda, porque eu ainda não tinha tanta familiaridade com `pytest`. A IA me ajudou a estruturar `tests/test_transformacao.py` e `tests/test_reconciliacao.py`, mostrando como montar cenários de borda e usar recursos que eu não conhecia bem, como `fixture`, `parametrize`, `pytest.raises`, `capsys` e `pytest.skip`.
- **Estruturação dos arquivos `.md` e comentários no código**: usei a IA pra ajudar a organizar a documentação e escrever comentários mais claros nas funções.

# Sugestões aceitas

- Parar o loop pelo `total_pages`. Eu tinha tentado parar quando a página viesse vazia, mas a IA sugeriu usar o `total_pages` que já vem na resposta da API, que é mais direto.
- Separar os erros de conexão, timeout e 404. Eu tinha feito um `try/except Exception` genérico, e a IA sugeriu separar pra mensagem dizer o que aconteceu de verdade.
- Usar `Decimal` em vez de `float` nos valores de dinheiro na transformação. Eu ia usar `float`, mas a IA explicou que `float` tem erro de arredondamento e podia quebrar a checagem de 1 centavo da divergência e a soma da reconciliação.
- Fazer cópia dos dicionários (`cliente.copy()`, `pedido.copy()`) em vez de alterar os dados originais direto. A IA sugeriu isso pra evitar efeito colateral nos testes e pra eu conseguir comparar o registro bruto com o tratado na hora de contar `estados_padronizados` e `datas_convertidas`.
- Colocar o `TRUNCATE` e todos os `INSERT`s dentro de um único bloco `with conectar() as conn:`. Assim, se alguma inserção falhar no meio, o PostgreSQL faz rollback e o banco não fica vazio nem carregado pela metade.
- Usar `@pytest.mark.parametrize` nos casos de borda da divergência (diferença de `0,00`, `0,01`, `0,02` e total menor) e `pytest.skip` no `test_reconciliacao.py` quando o banco ou a pasta `brutos/` não estiverem disponíveis.

# Sugestões rejeitadas

- Usar `pandas` pra ler o CSV e fazer as limpezas. A IA sugeriu porque ficaria mais curto, mas preferi fazer em Python puro porque são poucos dados e assim eu conseguia entender cada passo.
- Checar registro por registro no banco pra atualizar os que já existem. A IA sugeriu isso pra não duplicar dados ao rodar de novo, mas como o ETL sempre traz a base inteira, limpar com `TRUNCATE` e inserir tudo ficou mais simples.
- Criar classes pra `Cliente`, `Pedido` e `Item` em vez de usar dicionários. Achei que ia complicar à toa pro tamanho do projeto.
- Trocar os `print` de resumo pela biblioteca `logging`. Como o ETL é pequeno e eu só precisava ver os contadores no terminal, preferi manter o `print` mesmo.

# Falhas

- Ordem errada nas chaves estrangeiras na primeira versão do `carga.py`. Não atentei a ordem do código ao inserir `pedidos` antes de `clientes` e o `TRUNCATE` não começava pelas tabelas filhas (`itens_pedido, pedidos, clientes, produtos`), o que gerou erro de integridade no PostgreSQL logo no primeiro teste.
- Comparação de divergência com `float` antes de migrar pra `Decimal`. Em testes com diferença exata de 1 centavo (`20.01 - 20.00`), a subtração em binário dava `0.010000000000001563` e marcava `divergente = True` indevidamente.

# Retrabalho

- Tirar credenciais do banco do código. Nos primeiros testes com o contêiner Docker eu tinha deixado porta, usuário e senha direto no `carga.py` mas depois refatorei pra ler do `.env` com `python-dotenv` e conferi se `.env` e `brutos/` estavam fora do versionamento.


