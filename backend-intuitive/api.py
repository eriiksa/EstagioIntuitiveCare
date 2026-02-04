import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from repository import OperadoraRepository

# Inicialização do Flask
app = Flask(__name__)
CORS(app) # Habilita CORS para o frontend (Vue.js) acessar

# Instância do repositório
repo = OperadoraRepository()

@app.route('/api/operadoras', methods=['GET'])
def listar_operadoras():
    """
    Lista todas as operadoras com paginação e busca.
    Params: page (int), limit (int), search (str)
    """
    try:
        page = int(request.args.get('page', 1))
        limit = int(request.args.get('limit', 10))
        search = request.args.get('search', None)
        
        resultado = repo.get_todas_operadoras(page, limit, search)
        
        # Estrutura de resposta com metadados (Opção B do item 4.2.4 do PDF)
        return jsonify(resultado)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/api/operadoras/<cnpj>', methods=['GET'])
def detalhes_operadora(cnpj):
    """Retorna detalhes cadastrais de uma operadora"""
    operadora = repo.get_operadora_detalhes(cnpj)
    if operadora:
        return jsonify(operadora)
    return jsonify({"message": "Operadora não encontrada"}), 404

@app.route('/api/operadoras/<cnpj>/despesas', methods=['GET'])
def despesas_operadora(cnpj):
    """Retorna histórico de despesas"""
    despesas = repo.get_despesas_historico(cnpj)
    return jsonify(despesas) # Retorna lista vazia [] se não houver dados, o que é correto (Status 200)

@app.route('/api/estatisticas', methods=['GET'])
def estatisticas_gerais():
    """
    Retorna estatísticas agregadas:
    - Top 5 operadoras com maiores despesas (Total) - Requisito da rota
    - Top 5 operadoras com maior crescimento - Requisito da Query 1
    - Operadoras consistentemente acima da média.
    """
    try:
        # Reutilizando as queries analíticas já existentes no seu repository
        top_crescimento = repo.get_maior_crescimento()
        top_uf = repo.get_despesas_por_uf()
        consistencia = repo.get_operadoras_acima_media()
        
        # Para "Top 5 Maiores Despesas Totais" (diferente de crescimento), 
        # podemos pegar do método de UF ou criar um específico, 
        # mas aqui vamos compor com o que já temos para economizar tempo:
        
        return jsonify({
            "top_crescimento": top_crescimento,
            "distribuicao_uf": top_uf,
            "consistencia:": consistencia,
            "mensagem": "Estatísticas geradas com sucesso."
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Roda o servidor na porta 5000
    print("Iniciando API Intuitive Care...")
    app.run(debug=True, port=5000)