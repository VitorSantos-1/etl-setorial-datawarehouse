# ETL Setorial e Data Warehouse

Pipeline de ETL em Python que carrega as vendas setoriais de um supermercado em um Data Warehouse
MySQL modelado em star schema, tendo o produto como único ponto de ligação entre a tabela fato e as
dimensões. Cada venda é cruzada com o produto cadastrado e com sua hierarquia mercadológica, de modo
que a base analítica reflita exatamente o que foi vendido e sob qual categoria.

> **Nota de confidencialidade:** todos os dados presentes neste repositório (planilhas, seeds,
> exemplos) são fictícios, gerados aleatoriamente apenas para demonstração. Os dados reais da operação
> são confidenciais e estão protegidos — nenhum dado real, credencial ou informação de terceiros foi
> incluído aqui.

---

## Visão Geral

O projeto transforma duas planilhas operacionais — o cadastro de produtos e o setorial de vendas — em
um Data Warehouse consultável. O cadastro alimenta a dimensão de produto e desmembra o código
mercadológico em categoria e subcategoria; o setorial alimenta a tabela fato com as medidas de
quantidade, venda e lucro. O resultado é uma base pronta para análise de desempenho por segmento, com a
garantia de que apenas itens cadastrados e efetivamente vendidos entram no modelo.

## Contexto de Negócio

Analisar vendas por categoria e subcategoria é essencial para decisões de compra, sortimento e
precificação — mas o dado nasce fragmentado, em planilhas de vendas e de cadastro que nem sempre
conversam. Sem uma camada que padronize a hierarquia mercadológica e concilie venda com cadastro, as
análises setoriais ficam sujeitas a itens órfãos, categorias inconsistentes e retrabalho. Este pipeline
estabelece essa camada, dando à área comercial uma base setorial confiável e repetível.

## O Problema que Resolve

- **Hierarquia mercadológica inconsistente:** códigos como `001.013.003` sem categoria/subcategoria explícitas.
- **Vendas e cadastro desconectados:** dificuldade de cruzar o que vendeu com a categoria a que pertence.
- **Itens órfãos:** vendas de produtos não cadastrados poluindo a análise.
- **Ausência de um modelo analítico** estável para consultas por segmento.

## Público e Decisões Apoiadas

- **Compras e Comercial:** avaliam desempenho por categoria/subcategoria e ajustam sortimento e compra.
- **Diretoria:** acompanha a contribuição de cada segmento em venda e lucro.
- **Analytics/BI:** consome uma base modelada, sem precisar tratar planilha a cada análise.

## Impacto e Valor Gerado

- Consolida cadastro e vendas em um Data Warehouse único e consultável.
- Padroniza a hierarquia mercadológica (categoria e subcategoria) a partir do código do produto.
- Garante integridade: apenas itens cadastrados que venderam entram na fato (INNER JOIN por produto).
- Entrega uma base estável para análises setoriais recorrentes, reduzindo retrabalho.

---

## Arquitetura e Modelagem Dimensional (Star Schema)

```text
        dim_produto
   (produto - categoria - subcategoria - id_unico_submercadologico)
             |  (fk_produto = único elo)
             v
   fato_analise_setorial
   (quantidade - venda R$ - lucro R$ | grão: produto x loja x mês)
   loja e data = dimensões degeneradas na própria fato
```

- **`dim_produto`** — recebe o cadastro, desmembra o código mercadológico (`001.013.003`) em categoria
  e subcategoria e gera um `id_unico_submercadologico` (`001_013`) que identifica o par de forma única.
- **`fato_analise_setorial`** — agrupa as vendas por produto e carrega as medidas (quantidade, venda,
  lucro), validando data e loja. O grão é mensal (primeiro dia do mês).
- **Produto como único elo:** toda a hierarquia mercadológica é alcançada através da dimensão de
  produto; loja e data são dimensões degeneradas na própria fato.
- DDL completo (chaves, FK e índices) em `sql/schema.sql`.

## Stack

Python - Pandas - SQLAlchemy - MySQL 8+ - ETL - Modelagem Dimensional (Star Schema).

## Como Rodar

```bash
pip install -r requirements.txt

# 1. cria o banco e as tabelas
mysql -u root < sql/schema.sql

# 2. popula dim_produto (usa data_exemplo/ por padrão)
python script_cadastro_setorial.py

# 3. carrega os fatos de venda em fato_analise_setorial
python script_analise_setorial.py
```

Para apontar para planilhas reais (fora do repositório), use as variáveis de ambiente
`ARQUIVO_CADASTRO` e `ARQUIVO_SETORIAL`. Sem elas, os scripts usam os exemplos fictícios de `data_exemplo/`.

## Estrutura do Projeto

```text
sql/schema.sql               -> DDL do Data Warehouse (dim_produto, fato, FK, índices)
script_cadastro_setorial.py  -> ETL de cadastro: produtos + hierarquia mercadológica
script_analise_setorial.py   -> ETL de vendas: carga da fato_analise_setorial
requirements.txt             -> Dependências Python
data_exemplo/                -> Planilhas de exemplo (dados fictícios)
```

## Autor

José Vitor Santos Pinheiro — Análise de Dados e Inteligência Comercial (Varejo e Supply Chain).
Contato: vytorsantt@gmail.com
