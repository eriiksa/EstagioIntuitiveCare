import pandas as pd
import re
from database import engine
from decimal import Decimal
# Lib para bater os CNPJs e ver se são reais (Item 2.1)
from validate_docbr import CNPJ


def processar_e_carregar_despesas(path_csv, df_cadastral=None):
    """Lê o arquivo e decide se ele tem dados de despesas (prefixo 411) para processar."""

    # Garante que nome_arquivo esteja sempre definido, somente para reutilizar a variável
    nome_arquivo = path_csv.split('\\')[-1]

    encodings = ['utf-8', 'latin1', 'cp1252']
    df = None

    for enc in encodings:
        try:
            # Lendo como string pra não perder zeros à esquerda ou ter erros de leitura (Item 1.2)
            df = pd.read_csv(path_csv, sep=';', encoding=enc, dtype=str)
            break
        except Exception:
            continue

    if df is None:
        return None

    # Normalização das colunas  com mapping para encontra-las com consistência
    colunas_map = {col: col.upper() for col in df.columns}
    df = df.rename(columns=colunas_map)

    # Identificando a coluna de conta e de valor (Item 3.6/3.7)
    col_conta = next((c for c in df.columns if 'CONTA' in c), None)
    col_valor = next(
        (c for c in df.columns if 'VALOR' in c or 'SALDO' in c), None)
    col_reg_ans = next(
        (c for c in df.columns if 'REG' in c and 'ANS' in c), None)

    if not col_conta or not col_valor:
        return None

    # Filtro pelo prefixo 411 de indenizações e sinistros
    df_filtrado = df[df[col_conta].str.startswith('411', na=False)].copy()

    # Debug para controlar o volume de linhas que estão passando pelas validações
    print(
        f"DEBUG: Linhas encontradas com prefixo 411 no arquivo {nome_arquivo}: {len(df_filtrado)}")

    if df_filtrado.empty:
        return None

    # Limpeza de valores utilizando Decimal, para evitar inconsistências que existiriam usando float
    def limpar_valor(val):
        try:
            return Decimal(str(val).replace(',', '.'))
        except Exception:
            return Decimal('0.00')

    df_filtrado['valor_limpo'] = df_filtrado[col_valor].apply(
        limpar_valor)  # type: ignore

    # Apaga valores negativos e 0 (item 1.3)
    df_filtrado = df_filtrado[df_filtrado['valor_limpo'] > 0].copy()

    # Extração de data pelas colunas e trimestres pelo nome do  Arquivo, já que pelos arquivos estava retornando erroneamente
    col_data = next((c for c in df.columns if 'DATA' in c), None)
    if col_data:
        # Se for apenas o ano (ex: 2025), o to_datetime pode falhar. Tratamos aqui:
        df_filtrado['ano'] = df_filtrado[col_data].str.extract(r'(\d{4})')[0]
        # Trimestre extraído do nome do arquivo (3T2025 -> 3) se não houver na coluna
        tri_match = re.search(r'(\d)T', nome_arquivo)
        df_filtrado['trimestre'] = tri_match.group(1) if tri_match else "1"

    df_filtrado = df_filtrado.dropna(subset=['ano', 'trimestre'])

    # Join com Cadastro de Operadoras Ativas
    if df_cadastral is not None and col_reg_ans:
        # Normalização da coluna reg_ans para ler 6 digitos sem espaço ou decimais
        df_filtrado[col_reg_ans] = df_filtrado[col_reg_ans].astype(
            str).str.strip().str.replace(r'\.0$', '', regex=True).str.zfill(6)

        # Trazendo CNPJ e Nome da operadora para o consolidado (Item 1.3)
        df_filtrado = pd.merge(
            df_filtrado,
            df_cadastral[['registro_ans', 'cnpj', 'razao_social', 'uf']],
            left_on=col_reg_ans,
            right_on='registro_ans',
            how='inner'
        )

        # Evita somar a conta 411 (pai) com a 4111 (filha)
        df = df[df['CD_CONTA_CONTABIL'] == '411'].copy()

        # Remove linhas idênticas que podem surgir depois de processar vários arquivos
        df_filtrado = df_filtrado.drop_duplicates(
            subset=[col_reg_ans, col_conta, 'valor_limpo', 'ano', 'trimestre'])

        # Validação de CNPJ com lib validate_docbr(Item 2.1)
        validador = CNPJ()

        def validar_cnpj_limpo(valor):
            if pd.isna(valor):
                return False
            cnpj_limpo = re.sub(r'\D', '', str(valor))
            return validador.validate(cnpj_limpo)

        # Substitui a coluna cnpj com cnpjs válidos e roda o validar_cnpj_limpo para debug
        df_filtrado['cnpj_valido'] = df_filtrado['cnpj'].apply(
            validar_cnpj_limpo)
        df_filtrado = df_filtrado[df_filtrado['cnpj_valido'] == True].copy()

        # Debug de CNPJS
        print(f"DEBUG: Linhas após a validação de CNPJ: {len(df_filtrado)}")

    if not df_filtrado.empty:
        print(
            f"\n✅ {nome_arquivo}: {len(df_filtrado)} registros cruzados com sucesso!")
        print(df_filtrado[['registro_ans', 'cnpj',
              'razao_social', 'valor_limpo']].head(3))
        print("-" * 50)
    else:
        print(f"\n⚠️ {nome_arquivo}: Nenhum dado restou após o Join/Validação.")

    # Salvando no Postgres em massa
    if not df_filtrado.empty:
        try:
            df_db = df_filtrado[[col_reg_ans, col_conta, 'valor_limpo', 'ano', 'trimestre']].rename(columns={
                col_reg_ans: 'reg_ans', col_conta: 'cd_conta_contabil', 'valor_limpo': 'vl_saldo_final'
            })
            df_db.to_sql('despesas_consolidadas', con=engine,
                         if_exists='append', index=False, chunksize=1000)
            return df_filtrado
        except Exception as e:
            print(f"Erro na carga: {e}")
            return None
    return None


def carregar_operadoras(path_csv):
    """Lê o Relatorio_cadastro de operadoras ativas e prepara a base de nomes e CNPJs (Item 2.2)."""
    encodings = ['utf-8-sig', 'utf-8', 'latin1',
                 'cp1252']  # Utf-8 retornava caracteres desconhecidos, mesmo sendo recomendado no item 3.3 utf-8-sig funciona normalmente
    df_cad = None

    for enc in encodings:  # testa encodings
        try:
            df_cad = pd.read_csv(path_csv, sep=';', encoding=enc, dtype=str)
            # Se o número de colunas criadas pelo pandas for menor que 2, lê o arquivo com o outro encoding da lista encodings
            if df_cad.shape[1] < 2:
                df_cad = pd.read_csv(
                    path_csv, sep=',', encoding=enc, dtype=str)
            break
        except Exception:
            continue

    if df_cad is not None:
        df_cad.columns = df_cad.columns.str.strip().str.lower().str.replace(
            ' ', '_')  # Substitui espaços em branco por _ para normalização

        mapeamento = {
            # Prioriza 'registro_operadora' ou colunas que tenham 'registro' e 'ans' mas NÃO 'data'
            next((c for c in df_cad.columns if 'registro' in c and ('operadora' in c or 'ans' in c) and 'data' not in c), None): 'registro_ans',
            next((c for c in df_cad.columns if 'cnpj' in c), None): 'cnpj',
            next((c for c in df_cad.columns if 'razao' in c or 'social' in c), None): 'razao_social',
            next((c for c in df_cad.columns if 'uf' in c), None): 'uf',
            next((c for c in df_cad.columns if 'modalidade' in c), None): 'modalidade'
        }

        mapeamento = {k: v for k, v in mapeamento.items() if k is not None}
        df_clean = df_cad.rename(columns=mapeamento)[
            list(mapeamento.values())].copy()

        # NORMALIZAÇÃO NO CADASTRO: Garante que o registro_ans tenha 6 dígitos e remove sufixos decimais DEBUG
        df_clean['registro_ans'] = df_clean['registro_ans'].astype(
            str).str.strip().str.replace(r'\.0$', '', regex=True).str.zfill(6)

        df_clean = df_clean.drop_duplicates(subset=['registro_ans'])
        df_clean.to_sql('operadoras_ativas', con=engine,
                        if_exists='replace', index=False)
        return df_clean
    return None
