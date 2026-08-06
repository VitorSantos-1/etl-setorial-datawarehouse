import os
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine, text

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

# Mapa oficial: categoria mercadológica -> comprador responsável
MAPA_COMPRADORES = {
    '003': 1, '014': 1,                                # BRUNO
    '005': 2, '022': 2,                                # DIEGO
    '008': 3, '011': 3, '021': 3, '012': 3, '015': 3,  # CARLA
    '001': 4, '004': 4, '006': 4, '010': 4, '020': 4,  # FABIO
    '002': 5, '007': 5, '009': 5, '016': 5,            # ELAINE
}


def garantir_loja_e_data(loja_id, data_valor):
    """Garante que dim_loja e dim_data possuam as chaves usadas neste lote,
    ANTES de gravar os fatos (integridade referencial)."""
    dt = pd.to_datetime(data_valor)
    with engine.begin() as conn:
        conn.execute(
            text("INSERT IGNORE INTO dim_loja (pk_loja) VALUES (:loja)"),
            {"loja": int(loja_id)},
        )
        conn.execute(
            text("INSERT IGNORE INTO dim_data (pk_data, ano, mes) "
                 "VALUES (:d, :ano, :mes)"),
            {"d": dt.strftime("%Y-%m-%d"), "ano": int(dt.year), "mes": int(dt.month)},
        )
    print(f"-> Dimensões garantidas: loja {loja_id} e data {dt.strftime('%Y-%m-%d')}.")


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

    # Busca os produtos cadastrados (dimensão) para o cruzamento
    with engine.connect() as conn:
        df_produtos_db = pd.read_sql(
            "SELECT pk_produto, fk_mercadologico, fk_submercadologico FROM dim_produto", conn
        )

    data_valor = df_setorial['data'].iloc[0]
    loja_valor = int(df_setorial['fk_loja'].iloc[0])

    # NOVO: popula dim_loja e dim_data antes dos fatos (integridade referencial)
    garantir_loja_e_data(loja_valor, data_valor)

    # Agrupa as vendas por produto (soma repetições do arquivo de entrada)
    df_vendas = df_setorial.groupby('Produto', as_index=False).agg({
        'Quantidade': 'sum',
        'Venda': 'sum',
        'Lucro': 'sum',
    })

    # INNER JOIN: mantém apenas produtos cadastrados que de fato venderam
    df_fato = pd.merge(df_produtos_db, df_vendas, left_on='pk_produto', right_on='Produto', how='inner')

    # Preenche loja, data e comprador (PROCV do comprador pela categoria)
    df_fato['fk_loja'] = loja_valor
    df_fato['fk_data'] = data_valor
    df_fato['fk_comprador'] = df_fato['fk_mercadologico'].apply(
        lambda merc: MAPA_COMPRADORES.get(str(int(merc)).zfill(3)) if pd.notna(merc) else None
    )

    # Renomeia e seleciona as colunas finais (alinhadas ao schema)
    df_fato = df_fato.rename(columns={
        'pk_produto': 'fk_produto',
        'Quantidade': 'quantidade',
        'Venda': 'venda',
        'Lucro': 'lucro',
    })

    colunas_banco = [
        'fk_produto', 'fk_loja', 'fk_data', 'fk_comprador',
        'fk_mercadologico', 'fk_submercadologico',
        'quantidade', 'venda', 'lucro',
    ]
    df_fato = df_fato[colunas_banco].copy()

    # Garante tipos corretos e trata nulos
    df_fato['fk_produto'] = df_fato['fk_produto'].astype(int)
    df_fato['fk_loja'] = df_fato['fk_loja'].astype(int)
    for col in ['fk_mercadologico', 'fk_submercadologico', 'fk_comprador']:
        df_fato[col] = df_fato[col].astype(object).where(df_fato[col].notna(), None)

    # Grava no Data Warehouse
    df_fato.to_sql('fato_analise_setorial', con=engine, if_exists='append', index=False)
    print(f"-> Sucesso! {len(df_fato)} registros de vendas alocados na 'fato_analise_setorial'.")


if __name__ == '__main__':
    executar_etl_setorial()
