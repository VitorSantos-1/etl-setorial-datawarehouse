-- ============================================================================
--  DATA WAREHOUSE — ANÁLISE SETORIAL DE VENDAS
--  Modelo dimensional normalizado (snowflake) — MySQL 8+ / InnoDB
--
--  Reconstruído por engenharia reversa a partir de:
--    • script_cadastro_setorial.py  (popula dim_produto)
--    • script_analise_setorial.py   (popula fato_analise_setorial)
--
--  Normalização até a 3ª Forma Normal (3FN):
--    - cada dimensão em sua própria tabela, sem dependências transitivas;
--    - o vínculo "categoria → comprador" fica em dim_mercadologico,
--      eliminando a repetição do comprador em cada linha de venda.
-- ============================================================================

CREATE DATABASE IF NOT EXISTS analise_setorial
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE analise_setorial;

-- ----------------------------------------------------------------------------
--  DIMENSÃO: COMPRADOR  (responsável de compras por categoria)
--  Fonte: dicionário MAPA_COMPRADORES em script_analise_setorial.py
-- ----------------------------------------------------------------------------
CREATE TABLE dim_comprador (
  pk_comprador    INT          NOT NULL,
  nome_comprador  VARCHAR(60)  NOT NULL,
  PRIMARY KEY (pk_comprador)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
--  DIMENSÃO: CATEGORIA MERCADOLÓGICA  (ex.: '001')
--  Cada categoria pertence a UM comprador (dependência funcional
--  categoria → comprador movida para cá = 3FN).
-- ----------------------------------------------------------------------------
CREATE TABLE dim_mercadologico (
  pk_mercadologico  CHAR(3)      NOT NULL,      -- '001' .. '022'
  descricao         VARCHAR(80)  NULL,
  fk_comprador      INT          NULL,   -- NULL = categoria ainda sem comprador definido
  PRIMARY KEY (pk_mercadologico),
  CONSTRAINT fk_merc_comprador
    FOREIGN KEY (fk_comprador) REFERENCES dim_comprador (pk_comprador)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
--  DIMENSÃO: SUBCATEGORIA (submercadológico) — ex.: '013'
--  Pertence a uma categoria mercadológica → chave composta.
-- ----------------------------------------------------------------------------
CREATE TABLE dim_submercadologico (
  fk_mercadologico      CHAR(3)      NOT NULL,
  cod_submercadologico  CHAR(3)      NOT NULL,
  descricao             VARCHAR(80)  NULL,
  PRIMARY KEY (fk_mercadologico, cod_submercadologico),
  CONSTRAINT fk_sub_merc
    FOREIGN KEY (fk_mercadologico) REFERENCES dim_mercadologico (pk_mercadologico)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
--  DIMENSÃO: PRODUTO
--  'codigo_identificacao' guarda o mercadológico completo ('001.013.003').
-- ----------------------------------------------------------------------------
CREATE TABLE dim_produto (
  pk_produto            INT           NOT NULL,   -- coluna 'Código' da planilha
  descricao_produto     VARCHAR(120)  NULL,
  codigo_identificacao  VARCHAR(20)   NULL,       -- '001.013.003'
  fk_mercadologico      CHAR(3)       NOT NULL,
  fk_submercadologico   CHAR(3)       NULL,
  PRIMARY KEY (pk_produto),
  CONSTRAINT fk_prod_merc
    FOREIGN KEY (fk_mercadologico) REFERENCES dim_mercadologico (pk_mercadologico)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
--  DIMENSÃO: LOJA
-- ----------------------------------------------------------------------------
CREATE TABLE dim_loja (
  pk_loja    INT          NOT NULL,   -- ID informado no ETL (input 'LOJA')
  nome_loja  VARCHAR(60)  NULL,
  PRIMARY KEY (pk_loja)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
--  DIMENSÃO: DATA  (grão mensal — sempre o 1º dia do mês: AAAA-MM-01)
-- ----------------------------------------------------------------------------
CREATE TABLE dim_data (
  pk_data  DATE      NOT NULL,        -- 'YYYY-MM-01'
  ano      SMALLINT  NOT NULL,
  mes      TINYINT   NOT NULL,
  PRIMARY KEY (pk_data)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
--  FATO: VENDAS SETORIAIS
--  Grão: produto × loja × mês.
--  Medidas: quantidade, venda (R$), lucro (R$).
--
--  Obs. de modelagem: fk_mercadologico, fk_submercadologico e fk_comprador
--  são deriváveis de fk_produto (via dim_produto → dim_mercadologico).
--  Foram mantidos aqui porque o script_analise_setorial.py os grava —
--  é uma desnormalização controlada, típica de star schema, para acelerar
--  consultas. Para 3FN estrita, basta removê-los e obtê-los por JOIN.
-- ----------------------------------------------------------------------------
CREATE TABLE fato_analise_setorial (
  pk_fato              BIGINT         NOT NULL AUTO_INCREMENT,
  fk_produto           INT            NOT NULL,
  fk_loja              INT            NOT NULL,
  fk_data              DATE           NOT NULL,
  fk_comprador         INT            NULL,
  fk_mercadologico     CHAR(3)        NULL,
  fk_submercadologico  CHAR(3)        NULL,
  quantidade           DECIMAL(14,3)  NOT NULL DEFAULT 0,
  venda                DECIMAL(14,2)  NOT NULL DEFAULT 0,
  lucro                DECIMAL(14,2)  NOT NULL DEFAULT 0,
  PRIMARY KEY (pk_fato),
  CONSTRAINT fk_fato_produto
    FOREIGN KEY (fk_produto)   REFERENCES dim_produto (pk_produto),
  CONSTRAINT fk_fato_loja
    FOREIGN KEY (fk_loja)      REFERENCES dim_loja (pk_loja),
  CONSTRAINT fk_fato_data
    FOREIGN KEY (fk_data)      REFERENCES dim_data (pk_data),
  CONSTRAINT fk_fato_comprador
    FOREIGN KEY (fk_comprador) REFERENCES dim_comprador (pk_comprador),
  CONSTRAINT fk_fato_merc
    FOREIGN KEY (fk_mercadologico) REFERENCES dim_mercadologico (pk_mercadologico)
) ENGINE=InnoDB;

CREATE INDEX ix_fato_data      ON fato_analise_setorial (fk_data);
CREATE INDEX ix_fato_produto   ON fato_analise_setorial (fk_produto);
CREATE INDEX ix_fato_comprador ON fato_analise_setorial (fk_comprador);

-- ============================================================================
--  SEEDS — dados de referência extraídos diretamente do código
--  (nomes de compradores fictícios, conforme aviso do README)
-- ============================================================================

-- Compradores (MAPA_COMPRADORES)
INSERT INTO dim_comprador (pk_comprador, nome_comprador) VALUES
  (1, 'BRUNO'),
  (2, 'DIEGO'),
  (3, 'CARLA'),
  (4, 'FABIO'),
  (5, 'ELAINE');

-- Categorias mercadológicas e seu comprador responsável (MAPA_COMPRADORES)
INSERT INTO dim_mercadologico (pk_mercadologico, fk_comprador) VALUES
  ('003', 1), ('014', 1),                                     -- BRUNO
  ('005', 2), ('022', 2),                                     -- DIEGO
  ('008', 3), ('011', 3), ('021', 3), ('012', 3), ('015', 3), -- CARLA
  ('001', 4), ('004', 4), ('006', 4), ('010', 4), ('020', 4), -- FABIO
  ('002', 5), ('007', 5), ('009', 5), ('016', 5);             -- ELAINE
