-- Data Warehouse (star schema) — Análise Setorial de Vendas
CREATE TABLE dim_produto (
  pk_produto            INT PRIMARY KEY,
  fk_mercadologico      VARCHAR(10),
  fk_submercadologico   VARCHAR(10),
  descricao             VARCHAR(120)
);
CREATE TABLE dim_data (
  pk_data   INT PRIMARY KEY,   -- AAAAMMDD
  ano       INT,
  mes       INT
);
CREATE TABLE fato_vendas_setorial (
  pk            BIGINT AUTO_INCREMENT PRIMARY KEY,
  fk_produto    INT REFERENCES dim_produto(pk_produto),
  fk_data       INT REFERENCES dim_data(pk_data),
  fk_comprador  INT,
  loja          VARCHAR(40),
  quantidade    DECIMAL(14,3),
  valor         DECIMAL(14,2)
);
