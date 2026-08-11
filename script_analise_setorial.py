import os
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine

DB_URL = 'mysql+pymysql://root:@localhost:3306/analise_setorial'
engine = create_engine(DB_URL)

# Caminho do arquivo setorial.
# Padrão: exemplo fictício em data_exemplo/. Sobrescreva com a env var ARQUIVO_SETORIAL
# para apontar para a sua planilha real (não versionada).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_SETORIAL = os.getenv(
    'ARQUIVO_SETORIAL',
    os.path.join(BASE_DIR, 'data_exemplo', 'setorial_exemplo.xlsx')
)


def executar_etl_setorial():
    if not os.path.exists(ARQUIVO_SETORIAL):
        print(f"Erro: Arquivo '{ARQUIVO_SETORIAL}' não encontrado.")
        return

    print("=== INICIANDO FLUXO DE VENDAS SETORIAIS ===")

    # Lê a planilha setorial respeitando os tipos corretos
    df_setorial = pd.read_excel(ARQUIVO_SETORIAL, dtype={'Produto': int})
    df_setorial = df_setorial.dropna(subset=['Produto']).copy()

    # --- VALIDAÇÃO DE DATA (só pergunta se não vier no arquivo) ---
    if 'data' not in df_setorial.columns or df_setorial['data'].isna().any() or df_setorial['data'].empty:
        while True:
            data_input = input("Digite a DATA de movimentação para este lote (MM-AAAA): ").strip()
            try:
                dt = datetime.strptime(data_input, "%m-%Y")
                # Padrão do banco: primeiro dia do mês (AAAA-MM-01)
                df_setorial['data'] = dt.strftime("%Y-%m-01")
                break
            except ValueError:
                print("Formato incorreto. Use o padrão MM-AAAA (Ex: 07-2026).")
    else:
        print("-> Coluna 'data' já detectada no arquivo. Pergunta ignorada.")

    # --- VALIDAÇÃO DE LOJA (só pergunta se não vier no arquivo) ---
    if 'fk_loja' not in df_setorial.columns or df_setorial['fk_loja'].isna().any() or df_setorial['fk_loja'].empty:
        while True:
            loja_input = input("Digite o ID numérico da LOJA para este lote: ").strip()
            if loja_input.isdigit():
                df_setorial['fk_loja'] = int(loja_input)
                break
            else:
                print("Entrada inválida. Digite apenas o número identificador da loja.")
    else:
        print("-> Coluna 'fk_loja' já detectada no arquivo. Pergunta ignorada.")

    # Busca os produtos cadastrados (dimensão) para o cruzamento.
    # O PRODUTO é o único ponto de ligação entre a fato e as dimensões.
    with engine.connect() as conn:
        df_produtos_db = pd.read_sql("SELECT pk_produto FROM dim_produto", conn)

    data_valor = df_setorial['data'].iloc[0]
    loja_valor = int(df_setorial['fk_loja'].iloc[0])

    # Agrupa as vendas por produto (soma repetições do arquivo de entrada)
    df_vendas = df_setorial.groupby('Produto', as_index=False).agg({
        'Quantidade': 'sum',
        'Venda': 'sum',
        'Lucro': 'sum',
    })

    # INNER JOIN: mantém apenas produtos cadastrados que de fato venderam
    df_fato = pd.merge(df_produtos_db, df_vendas, left_on='pk_produto', right_on='Produto', how='inner')

    # Preenche loja e data (dimensões degeneradas da fato)
    df_fato['fk_loja'] = loja_valor
    df_fato['data'] = data_valor

    # Renomeia e seleciona as colunas finais (alinhadas ao schema)
    df_fato = df_fato.rename(columns={
        'pk_produto': 'fk_produto',
        'Quantidade': 'quantidade',
        'Venda': 'venda',
        'Lucro': 'lucro',
    })

    colunas_banco = ['fk_produto', 'fk_loja', 'quantidade', 'venda', 'lucro', 'data']
    df_fato = df_fato[colunas_banco].copy()

    # Garante tipos corretos
    df_fato['fk_produto'] = df_fato['fk_produto'].astype(int)
    df_fato['fk_loja'] = df_fato['fk_loja'].astype(int)

    # Grava no Data Warehouse
    df_fato.to_sql('fato_analise_setorial', con=engine, if_exists='append', index=False)
    print(f"-> Sucesso! {len(df_fato)} registros de vendas alocados na 'fato_analise_setorial'.")


if __name__ == '__main__':
    executar_etl_setorial()
