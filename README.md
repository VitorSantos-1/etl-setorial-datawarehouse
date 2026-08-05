# 📦 ETL Setorial + Data Warehouse

Pipeline **ETL em Python** que carrega vendas setoriais de um supermercado em um **Data Warehouse MySQL**
modelado em **star schema**, cruzando categorias mercadológicas e atribuindo cada venda ao comprador responsável.

> ⚠️ **Aviso sobre os dados**
> Todos os dados presentes neste repositório (planilhas, seeds, exemplos) são **fictícios** e foram
> **gerados aleatoriamente apenas para demonstração**. Os dados reais da operação em que o projeto
> foi utilizado são **confidenciais e estão protegidos** — nenhum dado real, credencial ou informação
> de terceiros foi incluído aqui.

## 🎯 O que faz
- Lê a planilha setorial e o cadastro de produtos.
- Cruza cada produto com sua **categoria mercadológica** (`dim_produto`).
- Mapeia a categoria ao **comprador responsável** (nomes fictícios neste repo).
- Valida data/loja e carrega os fatos em `fato_vendas_setorial` (modelo dimensional).

## 🏗️ Modelo (star schema)
```
        dim_produto           dim_data
             │                    │
             └──────┐      ┌──────┘
                    ▼      ▼
             fato_vendas_setorial  ──►  (loja, comprador, quantidade, valor)
```
Veja `sql/schema.sql`.

## 🧑‍💻 Stack
`Python` · `Pandas` · `SQLAlchemy` · `MySQL` · `ETL` · `Modelagem Dimensional (Star Schema)`

## ▶️ Como rodar
```bash
pip install pandas sqlalchemy pymysql openpyxl
# crie o banco 'analise_setorial' e rode o schema:
mysql -u root analise_setorial < sql/schema.sql
python script_cadastro_setorial.py   # popula dim_produto
python script_analise_setorial.py    # carrega os fatos
```
Dados de exemplo em `data_exemplo/`.

---

### 🧰 Competências demonstradas
`ETL` · `Data Warehouse` · `Modelagem Dimensional` · `SQL` · `Pandas`

### 👤 Autor
**José Vitor Santos Pinheiro** — Analista de Dados / BI / Ciência de Dados
· vytorsantt@gmail.com
