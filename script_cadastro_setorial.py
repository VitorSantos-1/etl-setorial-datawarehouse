import os
import pandas as pd
from sqlalchemy import create_engine

# Configuração de conexão do seu banco de dados
DB_URL = 'mysql+pymysql://root:@localhost:3306/analise_setorial'
engine = create_engine(DB_URL)

ARQUIVO_CADASTRO = r'C:\Users\Usuário\Documents\minha_pasta\Projetos\analise_setorial\cadastro.xlsx'

def obter_produtos_existentes():
    """Busca as chaves primárias de produtos que já estão gravadas no banco."""
    try:
        with engine.connect() as conn:
            df = pd.read_sql("SELECT pk_produto FROM dim_produto", conn)
            return set(df['pk_produto'].astype(int).tolist())
    except Exception:
        return set() # Se a tabela não existir, assume vazia

def executar_cadastro_produtos():
    if not os.path.exists(ARQUIVO_CADASTRO):
        print(f"Erro: Arquivo '{ARQUIVO_CADASTRO}' não encontrado.")
        return

    print("=== INICIANDO CADASTRO DE PRODUTOS ===")
    
    # Lê forçando os códigos a virem como string (preserva zeros à esquerda)
    df_bruto = pd.read_excel(ARQUIVO_CADASTRO, dtype={'Código': int, 'Mercadológico': str})
    
    # Remove linhas sem código ou sem classificação
    df_bruto = df_bruto.dropna(subset=['Código', 'Mercadológico']).copy()

    # Sepearação Inteligente das Chaves
    # Exemplo: '001.013.003' -> fk_mercadologico = '001', fk_submercadologico = '013'
    df_bruto['fk_mercadologico'] = df_bruto['Mercadológico'].apply(lambda x: x.split('.')[0] if '.' in x else x[:3])
    df_bruto['fk_submercadologico'] = df_bruto['Mercadológico'].apply(lambda x: x.split('.')[1] if len(x.split('.')) > 1 else '')

    # Mapeamento para a estrutura física do banco de dados
    df_dim_produto = pd.DataFrame({
        'pk_produto': df_bruto['Código'],
        'descricao_produto': df_bruto['Descrição'],
        'codigo_identificacao': df_bruto['Mercadológico'],
        'fk_mercadologico': df_bruto['fk_mercadologico'],
        'fk_submercadologico': df_bruto['fk_submercadologico']
    })

    # Regra: Evitar Duplicidade
    produtos_no_banco = obter_produtos_existentes()
    df_final = df_dim_produto[~df_dim_produto['pk_produto'].isin(produtos_no_banco)].copy()

    if not df_final.empty:
        df_final.to_sql('dim_produto', con=engine, if_exists='append', index=False)
        print(f"-> Sucesso! {len(df_final)} novos produtos cadastrados em 'dim_produto'.")
    else:
        print("-> Todos os produtos deste arquivo já estão cadastrados. Nenhuma linha duplicada foi inserida.")

if __name__ == '__main__':
    executar_cadastro_produtos()