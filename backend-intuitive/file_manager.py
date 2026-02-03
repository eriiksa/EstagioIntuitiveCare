import os
import zipfile
import shutil
import winreg
from pathlib import Path

def setup_diretorio():
    """
    Cria uma pasta temporária LOCAL no projeto para baixar os arquivos.
    NÃO retorna o Desktop, para evitar acidentes de deleção.
    """
    # Cria uma pasta 'consolidado_despesas' dentro da pasta do projeto
    base_path = Path(__file__).parent / "consolidado_despesas"
    data_path = base_path / "data"
    
    # Cria as pastas se não existirem
    data_path.mkdir(parents=True, exist_ok=True)
    
    return str(base_path)

def get_desktop_real():
    """Busca o caminho exato da Área de Trabalho no Registro do Windows (OneDrive ou Local)."""
    try:
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
        desktop_path, _ = winreg.QueryValueEx(key, "Desktop")
        return os.path.expandvars(desktop_path)
    except Exception as e:
        print(f"Erro ao buscar Desktop: {e}")
        return os.path.join(os.path.expanduser("~"), "Desktop")

def extrair_zip(caminho_projeto):
    """Extrai o arquivo ZIP baixado e remove o original."""
    try:
        # Extrai sempre para a subpasta 'data' relativa ao zip
        pasta_destino = os.path.join(os.path.dirname(caminho_projeto), 'data')
        with zipfile.ZipFile(caminho_projeto, 'r') as zip_ref:
            zip_ref.extractall(pasta_destino)
        os.remove(caminho_projeto)
    except Exception as e:
        print(f"Erro ao extrair ZIP: {e}")

def limpar_temporarios(caminho_base_temp):
    """
    1. Descobre onde é o Desktop Real.
    2. Cria uma pasta 'Output_Intuitive' no Desktop.
    3. Move os ZIPs prontos para lá.
    4. Deleta a pasta temporária de trabalho.
    """
    base_path = Path(caminho_base_temp)
    data_path = base_path / 'data'
    
    # 1. Pega o destino correto (Desktop)
    desktop_root = Path(get_desktop_real())
    
    # 2. Cria a pasta final organizada
    pasta_final = desktop_root / "Output_Intuitive"
    pasta_final.mkdir(parents=True, exist_ok=True)

    arquivos_finais = ['consolidado_despesas.zip', 'Teste_Erik.zip']

    print(f"Finalizando: Organizando arquivos em: {pasta_final}")

    for arquivo in arquivos_finais:
        origem = data_path / arquivo
        destino = pasta_final / arquivo
        
        if origem.exists():
            # Move para dentro da pasta nova
            shutil.move(str(origem), str(destino), copy_function=shutil.copy2)

    # 4. Limpa a bagunça do projeto
    if base_path.exists():
        try:
            shutil.rmtree(base_path)
            print("Limpeza concluída! Pasta temporária removida.")
        except Exception as e:
            print(f"Aviso: Não foi possível deletar a pasta temporária completamente: {e}")
    """
    1. Descobre onde é o Desktop Real.
    2. Move os ZIPs prontos da pasta temporária para o Desktop.
    3. Deleta a pasta temporária com segurança.
    """
    base_path = Path(caminho_base_temp)
    data_path = base_path / 'data'
    
    # Pega o destino correto (Desktop)
    desktop_path = Path(get_desktop_real())

    arquivos_finais = ['consolidado_despesas.zip', 'Teste_Erik.zip']

    print(f"Finalizando: Movendo arquivos para: {desktop_path}")

    for arquivo in arquivos_finais:
        origem = data_path / arquivo
        destino = desktop_path / arquivo
        
        if origem.exists():
            # Move e sobrescreve se necessário
            shutil.move(str(origem), str(destino), copy_function=shutil.copy2)

    if base_path.exists():
        try:
            shutil.rmtree(base_path)
        except Exception as e:
            print(f"Aviso: Não foi possível deletar a pasta temporária completamente: {e}")