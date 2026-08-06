import os
import pandas as pd
from sqlalchemy import create_engine, text

# Configuração de conexão do banco de dados
DB_URL = 'mysql+pymysql://root:@localhost:3306/analise_setorial'
engine = create_engine(DB_URL)

# Caminho do arquivo de cadastro (pode ser sobrescrito pela variável de ambiente)
ARQUIVO_CADASTRO = os.getenv(
    'ARQUIVO_CADASTRO',
    r'C:\Users\Usuário\Documents\minha_pasta\Projetos\analise_setorial\cadastro.xlsx'
)

# Mapa oficial: categoria mercadológica -> comprador responsável
MAPA_COMPRADORES = {
    '003': 1, '014': 1,                                # BRUNO
    '005': 2, '022': 2,                                # DIEGO
    '008': 3, '011': 3, '021': 3, '012': 3, '015': 3,  # CARLA
    '001': 4, '004': 4, '006': 4, '010': 4, '020': 4,  # FABIO
    '002': 5, '007': 5, '009': 5, '016': 5,            # ELAINE
}


def obter_produtos_existentes():
    """Chaves primárias de produtos já gravados (evita duplicidade)."""
    try:
        with engine.connect() as conn:
            df = pd.read_sql("SELECT pk_produto FROM dim_produto", conn)
            return set(df['pk_produto'].astype(int).tolist())
    except Exception:
        return set()  # Se a tabela não existir ainda, assume vazia


def garantir_dimensoes_categoria(df_bruto):
    """Garante que dim_mercadologico e dim_submercadologico contenham todas as
    categorias/subcategorias do arquivo ANTES de inserir os produtos,
    preservando a integridade referencial do Data Warehouse."""
    mercadologicos = sorted(df_bruto['fk_mercadologico'].dropna().unique())
    subs = (
        df_bruto.loc[df_bruto['fk_submercadologico'] != '',
                     ['fk_mercadologico', 'fk_submercadologico']]
        .drop_duplicates()
    )

    with engine.begin() as conn:
        # dim_mercadologico: usa o comprador do MAPA (NULL se ainda não mapeado)
        for merc in mercadologicos:
            conn.execute(
                text(
                    "INSERT INTO dim_mercadologico (pk_mercadologico, fk_comprador) "
                    "VALUES (:merc, :comp) "
                    "ON DUPLICATE KEY UPDATE fk_comprador = VALUES(fk_comprador)"
                ),
                {"merc": merc, "comp": MAPA_COMPRADORES.get(str(merc).zfill(3))},
            )
        # dim_submercadologico: pares (mercadológico, submercadológico) do arquivo
        for _, row in subs.iterrows():
            conn.execute(
                text(
                    "INSERT IGNORE INTO dim_submercadologico "
                    "(fk_mercadologico, cod_submercadologico) VALUES (:merc, :sub)"
                ),
                {"merc": row['fk_mercadologico'], "sub": row['fk_submercadologico']},
            )
    print(f"-> Dimensões garantidas: {len(mercadologicos)} mercadológicos e "
          f"{len(subs)} submercadológicos.")


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

    # NOVO: popula as dimensões de categoria antes dos produtos (integridade referencial)
    garantir_dimensoes_categoria(df_bruto)

    # Mapeamento para a estrutura física do banco
    df_dim_produto = pd.DataFrame({
        'pk_produto': df_bruto['Código'],
        'descricao_produto': df_bruto['Descrição'],
        'codigo_identificacao': df_bruto['Mercadológico'],
        'fk_mercadologico': df_bruto['fk_mercadologico'],
        'fk_submercadologico': df_bruto['fk_submercadologico'],
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
