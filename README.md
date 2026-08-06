# 📦 ETL Setorial + Data Warehouse

Pipeline **ETL em Python** que carrega vendas setoriais de um supermercado em um **Data Warehouse MySQL**
modelado em **star schema normalizado (3FN)**, cruzando cada produto com sua categoria mercadológica
e atribuindo a venda ao **comprador responsável**.

> ⚠️ **Aviso sobre os dados**
> Todos os dados presentes neste repositório (planilhas, seeds, exemplos) são **fictícios** e foram
> **gerados aleatoriamente apenas para demonstração**. Os dados reais da operação em que o projeto
> foi utilizado são **confidenciais e estão protegidos** — nenhum dado real, credencial ou informação
> de terceiros foi incluído aqui.

## 🎯 O que faz
- Lê a planilha de **cadastro** de produtos e popula `dim_produto` + a hierarquia mercadológica
  (`dim_mercadologico` → `dim_submercadologico`), garantindo a integridade referencial antes da carga.
- Mapeia cada **categoria mercadológica** ao seu **comprador responsável** (`MAPA_COMPRADORES` → `dim_comprador`).
- Lê a planilha **setorial** de vendas, agrupa por produto e carrega as medidas
  (quantidade, venda, lucro) em `fato_analise_setorial`, validando data e loja.

## 🏗️ Modelo dimensional (star / snowflake)
```
   dim_comprador
        ▲
        │ (categoria → comprador)
   dim_mercadologico ◄── dim_submercadologico
        ▲                      ▲
        │                      │
   dim_produto ────────────────┘        dim_loja      dim_data
        │                                   │            │
        └───────────────┬───────────────────┴────────────┘
                        ▼
              fato_analise_setorial
        (quantidade · venda R$ · lucro R$ | grão: produto × loja × mês)
```
Dimensões: `dim_comprador`, `dim_mercadologico`, `dim_submercadologico`, `dim_produto`, `dim_loja`, `dim_data`.
Fato: `fato_analise_setorial`. DDL completo (chaves, FKs, índices e seeds fictícios) em [`sql/schema.sql`](sql/schema.sql).

## 🧑‍💻 Stack
`Python` · `Pandas` · `SQLAlchemy` · `MySQL 8+` · `ETL` · `Modelagem Dimensional (Star/Snowflake, 3FN)`

## ▶️ Como rodar
```bash
pip install -r requirements.txt

# 1. cria o banco e todas as tabelas (o próprio script já faz CREATE DATABASE)
mysql -u root < sql/schema.sql

# 2. popula dim_produto + hierarquia mercadológica (usa data_exemplo/ por padrão)
python script_cadastro_setorial.py

# 3. carrega os fatos de venda em fato_analise_setorial
python script_analise_setorial.py
```
Para apontar para as suas planilhas reais (fora do repositório), use as variáveis de ambiente
`ARQUIVO_CADASTRO` e `ARQUIVO_SETORIAL`. Sem elas, os scripts usam os exemplos fictícios de `data_exemplo/`.

## 📁 Estrutura
```
sql/schema.sql               # DDL do Data Warehouse (MySQL) — dimensões, fato, FKs, índices, seeds
script_cadastro_setorial.py  # ETL de cadastro: produtos + hierarquia mercadológica
script_analise_setorial.py   # ETL de vendas: carga da fato_analise_setorial
requirements.txt             # dependências Python
data_exemplo/                # planilhas de exemplo (dados fictícios)
```

---

### 🧰 Competências demonstradas
`ETL` · `Data Warehouse` · `Modelagem Dimensional` · `Normalização (3FN)` · `SQL` · `Pandas`

### 👤 Autor
**José Vitor Santos Pinheiro** — Analista de Dados / BI / Ciência de Dados
· vytorsantt@gmail.com
