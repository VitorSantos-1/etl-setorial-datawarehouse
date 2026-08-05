import os
from datetime import datetime
import pandas as pd
from sqlalchemy import create_engine

DB_URL = 'mysql+pymysql://root:@localhost:3306/analise_setorial'
engine = create_engine(DB_URL)

ARQUIVO_SETORIAL = r'C:\Users\Usuário\Documents\minha_pasta\Projetos\analise_setorial\setorial.xls'

# Dicionário do mapeamento de compradores oficiais por código de categoria (Mercadológico)
MAPA_COMPRADORES = {
    '003': 1, '014': 1,  # BRUNO
    '005': 2, '022': 2,  # DIEGO
    '008': 3, '011': 3, '021': 3, '012': 3, '015': 3,  # CARLA
    '001': 4, '004': 4, '006': 4, '010': 4, '020': 4,  # FABIO
    '002': 5, '007': 5, '009': 5, '016': 5   # ELAINE
}

def obter_dicionario_produtos():
    """Busca o mapeamento de produtos no banco para cruzar com o arquivo setorial."""
    try:
        with engine.connect() as conn:
            query = "SELECT pk_produto, fk_mercadologico, fk_submercadologico FROM dim_produto"
            return pd.read_sql(query, conn).set_index('pk_produto').to_dict('index')
    except Exception:
        print("Aviso: Não foi possível ler a dim_produto do banco. Rode o script de cadastro primeiro.")
        return {}

def executar_etl_setorial():
    if not os.path.exists(ARQUIVO_SETORIAL):
        print(f"Erro: Arquivo '{ARQUIVO_SETORIAL}' não encontrado.")
        return

    print("=== INICIANDO FLUXO DE VENDAS SETORIAIS ===")
    
    # Lê a planilha setorial respeitando os tipos corretos
    df_setorial = pd.read_excel(ARQUIVO_SETORIAL, dtype={'Produto': int})
    df_setorial = df_setorial.dropna(subset=['Produto']).copy()

    # ---------------------------------------------------------
    # VALIDAÇÃO DE DATA E LOJA (REGRAS 2, 4 e 5)
    # ---------------------------------------------------------
    # Só pergunta se a coluna não existir ou estiver totalmente zerada/nula no arquivo
    if 'data' not in df_setorial.columns or df_setorial['data'].isna().any() or df_setorial['data'].empty:
        while True:
            data_input = input("Digite a DATA de movimentação para este lote (MM-AAAA): ").strip()
            try:
                dt = datetime.strptime(data_input, "%m-%Y")
                # Converte para o padrão do banco (primeiro dia do mês: AAAA-MM-01)
                df_setorial['data'] = dt.strftime("%Y-%m-01")
                break
            except ValueError:
                print("Formato incorreto. Use o padrão MM-AAAA (Ex: 07-2026).")
    else:
        print("-> Coluna 'data' já detectada no arquivo setorial. Pergunta ignorada.")

    if 'fk_loja' not in df_setorial.columns or df_setorial['fk_loja'].isna().any() or df_setorial['fk_loja'].empty:
        while True:
            loja_input = input("Digite o ID numérico da LOJA para este lote: ").strip()
            if loja_input.isdigit():
                df_setorial['fk_loja'] = int(loja_input)
                break
            else:
                print("Entrada inválida. Digite apenas o número identificador da loja.")
    else:
        print("-> Coluna 'fk_loja' já detectada no arquivo setorial. Pergunta ignorada.")

    # ---------------------------------------------------------
    # PROCV INTELIGENTE DO MERCADOLÓGICO, SUB E COMPRADOR
    # ---------------------------------------------------------
    # 1. Buscar todos os produtos da dimensão do banco de dados
    with engine.connect() as conn:
        query = "SELECT pk_produto, fk_mercadologico, fk_submercadologico FROM dim_produto"
        df_produtos_db = pd.read_sql(query, conn)

    # 2. Obter a data e loja informadas nos inputs
    data_valor = df_setorial['data'].iloc[0]
    loja_valor = int(df_setorial['fk_loja'].iloc[0])

    # 3. Agrupar as vendas por Produto (caso haja repetições no arquivo de entrada)
    df_vendas = df_setorial.groupby('Produto', as_index=False).agg({
        'Quantidade': 'sum',
        'Venda': 'sum',
        'Lucro': 'sum'
    })

    # 4. Cruzamento INNER JOIN para garantir apenas os produtos cadastrados que de fato venderam
    df_fato = pd.merge(df_produtos_db, df_vendas, left_on='pk_produto', right_on='Produto', how='inner')

    # 6. Preencher Loja, Data e Comprador
    df_fato['fk_loja'] = loja_valor
    df_fato['data'] = data_valor
    df_fato['fk_comprador'] = df_fato['fk_mercadologico'].apply(
        lambda merc: MAPA_COMPRADORES.get(str(int(merc)).zfill(3) if pd.notna(merc) else None, None)
    )

    # 7. Renomear e selecionar colunas finais
    df_fato = df_fato.rename(columns={
        'pk_produto': 'fk_produto',
        'Quantidade': 'quantidade',
        'Venda': 'venda',
        'Lucro': 'lucro'
    })
    
    colunas_banco = [
        'fk_produto', 'fk_loja', 'fk_submercadologico', 
        'fk_mercadologico', 'fk_comprador', 'quantidade', 
        'venda', 'lucro', 'data'
    ]
    df_fato = df_fato[colunas_banco].copy()

    # 8. Garantir tipos de dados corretos para inserção e tratamento de nulos
    df_fato['fk_produto'] = df_fato['fk_produto'].astype(int)
    df_fato['fk_loja'] = df_fato['fk_loja'].astype(int)
    
    for col in ['fk_mercadologico', 'fk_submercadologico', 'fk_comprador']:
        df_fato[col] = df_fato[col].astype(object).where(df_fato[col].notna(), None)

    # 9. Gravar no banco de dados
    df_fato.to_sql('fato_analise_setorial', con=engine, if_exists='append', index=False)
    print(f"-> Sucesso! {len(df_fato)} registros de vendas alocados na 'fato_analise_setorial'.")

if __name__ == '__main__':
    executar_etl_setorial()