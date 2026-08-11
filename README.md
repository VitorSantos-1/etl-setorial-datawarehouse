# 📦 ETL Setorial + Data Warehouse

Pipeline **ETL em Python** que carrega vendas setoriais de um supermercado em um **Data Warehouse MySQL**
modelado em **star schema**, tendo o **produto** como único ponto de ligação entre a tabela fato e as
dimensões — cada venda é cruzada com o produto cadastrado e sua hierarquia mercadológica.

> ⚠️ **Aviso sobre os dados**
> Todos os dados presentes neste repositório (planilhas, seeds, exemplos) são **fictícios** e foram
> **gerados aleatoriamente apenas para demonstração**. Os dados reais da operação em que o projeto
> foi utilizado são **confidenciais e estão protegidos** — nenhum dado real, credencial ou informação
> de terceiros foi incluído aqui.

## 🎯 O que faz
- Lê a planilha de **cadastro** de produtos e popula `dim_produto`, desmembrando o código
  mercadológico (`'001.013.003'`) em **categoria** e **subcategoria** e gerando um
  `id_unico_submercadologico` (`'001_013'`) que identifica o par de forma única.
- Lê a planilha **setorial** de vendas, agrupa por produto e carrega as medidas
  (quantidade, venda, lucro) em `fato_analise_setorial`, validando data e loja.
- Cruzamento **INNER JOIN** produto a produto: só entram na fato os itens cadastrados que de fato venderam.

## 🏗️ Modelo dimensional (star schema)
```
        dim_produto
   (produto · categoria · subcategoria ·
    id_unico_submercadologico)
             │  (fk_produto = único elo)
             ▼
   fato_analise_setorial
   (quantidade · venda R$ · lucro R$ | grão: produto × loja × mês)
   loja e data = dimensões degeneradas na própria fato
```
O **produto** é o único ponto de ligação entre a fato e as dimensões; toda a hierarquia mercadológica
(categoria → subcategoria) é alcançada através dele. **Loja** e **data** são dimensões degeneradas
armazenadas diretamente na fato (grão mensal — 1º dia do mês).
DDL completo (chaves, FK, índices) em [`sql/schema.sql`](sql/schema.sql).

## 🧑‍💻 Stack
`Python` · `Pandas` · `SQLAlchemy` · `MySQL 8+` · `ETL` · `Modelagem Dimensional (Star Schema)`

## ▶️ Como rodar
```bash
pip install -r requirements.txt

# 1. cria o banco e as tabelas
mysql -u root < sql/schema.sql

# 2. popula dim_produto (usa data_exemplo/ por padrão)
python script_cadastro_setorial.py

# 3. carrega os fatos de venda em fato_analise_setorial
python script_analise_setorial.py
```
Para apontar para as suas planilhas reais (fora do repositório), use as variáveis de ambiente
`ARQUIVO_CADASTRO` e `ARQUIVO_SETORIAL`. Sem elas, os scripts usam os exemplos fictícios de `data_exemplo/`.

## 📁 Estrutura
```
sql/schema.sql               # DDL do Data Warehouse (MySQL) — dim_produto, fato, FK, índices
script_cadastro_setorial.py  # ETL de cadastro: produtos + hierarquia mercadológica
script_analise_setorial.py   # ETL de vendas: carga da fato_analise_setorial
requirements.txt             # dependências Python
data_exemplo/                # planilhas de exemplo (dados fictícios)
```

---

### 🧰 Competências demonstradas
`ETL` · `Data Warehouse` · `Modelagem Dimensional (Star Schema)` · `SQL` · `Pandas`

### 👤 Autor
**José Vitor Santos Pinheiro** — Analista de Dados / BI / Ciência de Dados
· vytorsantt@gmail.com
