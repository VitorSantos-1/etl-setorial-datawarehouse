-- ============================================================================
--  DATA WAREHOUSE — ANÁLISE SETORIAL DE VENDAS
--  Star schema simplificado — MySQL 8+ / InnoDB
--
--  Reconstruído a partir de:
--    • script_cadastro_setorial.py  (popula dim_produto)
--    • script_analise_setorial.py   (popula fato_analise_setorial)
--
--  Modelagem: o PRODUTO é o único ponto de ligação entre a fato e as
--  dimensões. A hierarquia mercadológica (categoria/subcategoria) fica
--  descrita na própria dim_produto; loja e data entram na fato como
--  dimensões degeneradas (grão mensal).
-- ============================================================================

CREATE DATABASE IF NOT EXISTS analise_setorial
  CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
USE analise_setorial;

-- ----------------------------------------------------------------------------
--  DIMENSÃO: PRODUTO
--  'codigo_identificacao' guarda o mercadológico completo ('001.013.003').
--  A categoria ('001') e a subcategoria ('013') são desmembradas em colunas
--  próprias; 'id_unico_submercadologico' ('001_013') identifica o par
--  categoria+subcategoria de forma única.
-- ----------------------------------------------------------------------------
CREATE TABLE dim_produto (
  pk_produto                 INT           NOT NULL,   -- coluna 'Código' da planilha
  descricao_produto          VARCHAR(120)  NULL,
  codigo_identificacao       VARCHAR(20)   NULL,       -- '001.013.003'
  fk_mercadologico           CHAR(3)       NULL,       -- '001'
  fk_submercadologico        CHAR(3)       NULL,       -- '013'
  id_unico_submercadologico  VARCHAR(7)    NULL,       -- '001_013'
  PRIMARY KEY (pk_produto)
) ENGINE=InnoDB;

-- ----------------------------------------------------------------------------
--  FATO: VENDAS SETORIAIS
--  Grão: produto × loja × mês.
--  Medidas: quantidade, venda (R$), lucro (R$).
--
--  fk_produto é a ÚNICA ligação com as dimensões (dim_produto). fk_loja e
--  data são dimensões degeneradas, armazenadas na própria fato — toda a
--  hierarquia mercadológica é alcançada via produto.
-- ----------------------------------------------------------------------------
CREATE TABLE fato_analise_setorial (
  pk_fato      BIGINT         NOT NULL AUTO_INCREMENT,
  fk_produto   INT            NOT NULL,
  fk_loja      INT            NOT NULL,
  data         DATE           NOT NULL,        -- 1º dia do mês (AAAA-MM-01)
  quantidade   DECIMAL(14,3)  NOT NULL DEFAULT 0,
  venda        DECIMAL(14,2)  NOT NULL DEFAULT 0,
  lucro        DECIMAL(14,2)  NOT NULL DEFAULT 0,
  PRIMARY KEY (pk_fato),
  CONSTRAINT fk_fato_produto
    FOREIGN KEY (fk_produto) REFERENCES dim_produto (pk_produto)
) ENGINE=InnoDB;

CREATE INDEX ix_fato_data    ON fato_analise_setorial (data);
CREATE INDEX ix_fato_produto ON fato_analise_setorial (fk_produto);
CREATE INDEX ix_fato_loja    ON fato_analise_setorial (fk_loja);
