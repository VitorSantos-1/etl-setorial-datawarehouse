import os
import pandas as pd
from sqlalchemy import create_engine

# Configuração de conexão do banco de dados
DB_URL = 'mysql+pymysql://root:@localhost:3306/analise_setorial'
engine = create_engine(DB_URL)

# Caminho do arquivo de cadastro.
# Padrão: exemplo fictício em data_exemplo/. Sobrescreva com a env var ARQUIVO_CADASTRO
# para apontar para a sua planilha real (não versionada).
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_CADASTRO = os.getenv(
    'ARQUIVO_CADASTRO',
    os.path.join(BASE_DIR, 'data_exemplo', 'cadastro_exemplo.xlsx')
)


def obter_produtos_existentes():
    """Chaves primárias de produtos já gravados (evita duplicidade)."""
    try:
        with engine.connect() as conn:
            df = pd.read_sql("SELECT pk_produto FROM dim_produto", conn)
            return set(df['pk_produto'].astype(int).tolist())
    except Exception:
        return set()  # Se a tabela não existir ainda, assume vazia


def executar_cadastro_produtos():
    if not os.path.exists(ARQUIVO_CADASTRO):
        print(f"Erro: Arquivo '{ARQUIVO_CADASTRO}' não encontrado.")
        return

    print("=== INICIANDO CADASTRO DE PRODUTOS ===")

    # Lê preservando os tipos corretos (código inteiro, mercadológico como texto)
    df_bruto = pd.read_excel(ARQUIVO_CADASTRO, dtype={'Código': int, 'Mercadológico': str})
    df_bruto = df_bruto.dropna(subset=['Código', 'Mercadológico']).copy()

    # Separação das chaves: '001.013.003' -> mercadológico '001', sub '013'
    df_bruto['fk_mercadologico'] = df_bruto['Mercadológico'].apply(
        lambda x: x.split('.')[0] if '.' in x else x[:3]
    )
    df_bruto['fk_submercadologico'] = df_bruto['Mercadológico'].apply(
        lambda x: x.split('.')[1] if len(x.split('.')) > 1 else ''
    )

    # Mapeamento para a estrutura física do banco.
    # id_unico_submercadologico ('001_013') identifica o par categoria+subcategoria.
    df_dim_produto = pd.DataFrame({
        'pk_produto': df_bruto['Código'],
        'descricao_produto': df_bruto['Descrição'],
        'codigo_identificacao': df_bruto['Mercadológico'],
        'fk_mercadologico': df_bruto['fk_mercadologico'],
        'fk_submercadologico': df_bruto['fk_submercadologico'],
        'id_unico_submercadologico': (
            df_bruto['fk_mercadologico'].str.zfill(3) + '_' +
            df_bruto['fk_submercadologico'].str.zfill(3)
        ),
    })

    # Regra: evitar duplicidade
    produtos_no_banco = obter_produtos_existentes()
    df_final = df_dim_produto[~df_dim_produto['pk_produto'].isin(produtos_no_banco)].copy()

    if not df_final.empty:
        df_final.to_sql('dim_produto', con=engine, if_exists='append', index=False)
        print(f"-> Sucesso! {len(df_final)} novos produtos cadastrados em 'dim_produto'.")
    else:
        print("-> Todos os produtos deste arquivo já estão cadastrados. Nada foi inserido.")


if __name__ == '__main__':
    executar_cadastro_produtos()
