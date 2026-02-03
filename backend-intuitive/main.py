import os
import requests
import pandas as pd
import zipfile
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from file_manager import setup_diretorio, limpar_temporarios
from etl_process import processar_e_carregar_despesas, carregar_operadoras
from database import criar_tabelas

if __name__ == "__main__":
    criar_tabelas()
    base_path = setup_diretorio()
    data_path = os.path.join(base_path, 'data')
    if not os.path.exists(data_path): os.makedirs(data_path)

    lista_dfs_despesas = [] # Lista vazia para reservar os 3 trimestres finais

    chrome_options = Options()
    chrome_options.add_argument("--headless")  # Modo headless para uma velocidade maior da automação

    driver = webdriver.Chrome(options=chrome_options) # Usa o chrome como browser do selenium

    wait = WebDriverWait(driver, 15)
    base_url = "https://dadosabertos.ans.gov.br/FTP/PDA/"

    try:
        # 1. Encontrando o cadastro de operadoras primeiro para popular o join final e então adicionar os dados 
        print("Carregando Cadastro de Operadoras de planos de saude ativas...")
        driver.get(base_url + "operadoras_de_plano_de_saude_ativas/")
        link_cadop = wait.until(EC.presence_of_element_located((By.XPATH, "//a[contains(@href, '.csv')]"))).get_attribute("href") # Busca pela extensão do arquivo, já que os nomes são inconsistentes
        
        path_cad = os.path.join(data_path, "Relatorio_cadop.csv")
        with open(path_cad, 'wb') as f: f.write(requests.get(link_cadop).content) #type:ignore
        df_cadastral = carregar_operadoras(path_cad)

        # 2. BUSCAR OS 3 TRIMESTRES MAIS RECENTES
        driver.get(base_url + "demonstracoes_contabeis/")
        anos = sorted([el.get_attribute("href") for el in wait.until(EC.presence_of_all_elements_located((By.XPATH, "//a[contains(@href, '20')]")))], reverse=True) #type: ignore

        trimestres_validados = 0
        for ano_url in anos:
            if trimestres_validados >= 3: break
            driver.get(ano_url)
            zips = sorted([el.get_attribute("href") for el in driver.find_elements(By.XPATH, "//a[contains(@href, '.zip')]")], reverse=True) #type: ignore
            
            for url_zip in zips:
                if trimestres_validados >= 3: break
                
                # Download e Extração
                nome_arquivo_zip = url_zip.split('/')[-1]
                caminho_zip = os.path.join(data_path, nome_arquivo_zip)

                with open(caminho_zip, 'wb') as f: 
                    f.write(requests.get(url_zip).content)
                
                with zipfile.ZipFile(caminho_zip, 'r') as zip_ref:
                    zip_ref.extractall(data_path)
                os.remove(caminho_zip)

                # Lê todos os zips para checar um por um se há prefixo 411 de indenizações
                arquivos_extraidos = [f for f in os.listdir(data_path) if f.endswith('.csv') and 'Relatorio_cadop' not in f] 
                
                for nome_f in arquivos_extraidos:
                    caminho_f = os.path.join(data_path, nome_f)

                    # O etl_process vai dizer se o arquivo tem 411 ou não
                    df_proc = processar_e_carregar_despesas(caminho_f, df_cadastral=df_cadastral)
                    
                    if df_proc is not None:
                        lista_dfs_despesas.append(df_proc)
                        trimestres_validados += 1
                        print(f"Sucesso: Dados de despesas encontrados em {nome_f}")

                    # Remove o CSV processado para não processar de novo
                    if os.path.exists(caminho_f):
                        os.remove(caminho_f)

        # Se houver 3 dfs que foram validados para entrar na lista_dfs_despesas, concatena os 3 (Itens 1.3 e 2.3)
        if len(lista_dfs_despesas) >= 3:
            df_final = pd.concat(lista_dfs_despesas)
            
            # Converte para float para garantir a ordenação numérica correta
            df_final['valor_float'] = pd.to_numeric(df_final['valor_limpo'], errors='coerce') 

            # Ordena do maior para o menor valor, com isso deu para perceber que os valores eram incrementais e que estavam poluindo a base
            df_final = df_final.sort_values(by='valor_float', ascending=False)
            
            # Remove duplicatas considerando CNPJ, Trimestre e Ano
            # Como está ordenado decrescente, o keep='first' mantém o MAIOR valor de cada trimestre
            df_final = df_final.drop_duplicates(subset=['cnpj', 'trimestre', 'ano'], keep='first')

            path_csv_consolidado = os.path.join(data_path, 'consolidado_despesas.csv')
            path_zip_consolidado = os.path.join(data_path, 'consolidado_despesas.zip')
    
            # CSV Consolidado (Garante precisão enviando o valor original) 
            colunas_finais = ['cnpj', 'razao_social', 'trimestre', 'ano', 'valor_limpo']
            df_final[colunas_finais].to_csv(path_csv_consolidado, sep=';', index=False, encoding='utf-8-sig')

            with zipfile.ZipFile(path_zip_consolidado, 'w', zipfile.ZIP_DEFLATED) as zipf:
                # O arcname garante que só o arquivo entre no zip, sem pastas
                zipf.write(path_csv_consolidado, arcname='consolidado_despesas.csv')

            os.remove(path_csv_consolidado) # deleta o arquivo consolidado_despesas.csv solto
            
            df_agregado = df_final.groupby(['razao_social', 'uf']).agg(
                total_despesas=('valor_float', 'sum'),
                media_trimestral=('valor_float', 'mean'),
                desvio_padrao=('valor_float', 'std') 
            ).reset_index()
            df_agregado = df_agregado.sort_values(by='total_despesas', ascending=False) # ascending=False já que foi solicitado ordem decrescente (item 2.3)

            path_csv_agregado = os.path.join(data_path, 'despesas_agregadas.csv')
            path_zip_final = os.path.join(data_path, 'Teste_Erik.zip')

            df_agregado.to_csv(os.path.join(data_path, 'despesas_agregadas.csv'), sep=';', index=False, encoding='utf-8-sig')
           
            with zipfile.ZipFile(path_zip_final, 'w', zipfile.ZIP_DEFLATED) as zipf:
                zipf.write(path_csv_agregado, arcname='despesas_agregadas.csv' ) 

            os.remove(path_csv_agregado) # deleta o arquivo despesas_agregadas.csv solto
            limpar_temporarios(base_path)

            print("CSVs gerados e banco populado")

    finally:
        driver.quit()