from sqlalchemy import text
from database import SessionLocal

class OperadoraRepository():
    def __init__(self):
        self.db = SessionLocal
    
    def get_maior_crescimento(self):
        """Query de maior crescimento percentual de despesas"""

        sql = text("""
        WITH periodos AS (
            SELECT 
                MIN(ano * 10 + trimestre) as min_periodo,
                MAX(ano * 10 + trimestre) as max_periodo
            FROM despesas_consolidadas
        ),
        despesas_inicio AS (
            SELECT d.reg_ans, SUM(d.vl_saldo_final) as total_inicial
            FROM despesas_consolidadas d
            JOIN periodos p ON (d.ano * 10 + d.trimestre) = p.min_periodo
            GROUP BY d.reg_ans
            HAVING SUM(d.vl_saldo_final) > 0
        ),
        despesas_fim AS (
            SELECT d.reg_ans, SUM(d.vl_saldo_final) as total_final
            FROM despesas_consolidadas d
            JOIN periodos p ON (d.ano * 10 + d.trimestre) = p.max_periodo
            GROUP BY d.reg_ans
        )
        SELECT 
            o.registro_ans,
            o.razao_social,
            di.total_inicial,
            df.total_final,
            ROUND(((df.total_final - di.total_inicial) / di.total_inicial) * 100, 2) as crescimento_percentual
        FROM despesas_inicio di
        JOIN despesas_fim df ON di.reg_ans = df.reg_ans
        JOIN operadoras_ativas o ON di.reg_ans = o.registro_ans
        ORDER BY crescimento_percentual DESC
        LIMIT 5;
        """)
        
        db = None 
        try:
            db = self.db()
            result = db.execute(sql).fetchall() # Converte o resultado (lista de tuplas) em lista de dicionários para a API

            return [
                {
                    "registro_ans": row.registro_ans,
                    "razao_social": row.razao_social,
                    "total_inicial": float(row.total_inicial),
                    "total_final": float(row.total_final),
                    "crescimento_percentual": float(row.crescimento_percentual)
                } 
                for row in result
            ]
        except Exception as e:
            print(f"Erro ao executar query de crescimento: {e}")
            return []
        finally:
            if db is not None:
                db.close()


    def get_despesas_por_uf(self):
        """
        Executa a Query 2: Distribuição por UF.
        """
        sql = text("""
        SELECT 
            o.uf,
            SUM(d.vl_saldo_final) as despesa_total,
            COUNT(DISTINCT d.reg_ans) as qtd_operadoras,
            ROUND(SUM(d.vl_saldo_final) / COUNT(DISTINCT d.reg_ans), 2) as media_por_operadora
        FROM despesas_consolidadas d
        JOIN operadoras_ativas o ON d.reg_ans = o.registro_ans
        GROUP BY o.uf
        ORDER BY despesa_total DESC
        LIMIT 5;
        """)
        
        db = None
        try:
            db = self.db()
            result = db.execute(sql).fetchall()

            return [
                {
                    "uf": row.uf,
                    "despesa_total": float(row.despesa_total),
                    "qtd_operadoras": int(row.qtd_operadoras),
                    "media_por_operadora": float(row.media_por_operadora)
                }
                for row in result
            ]
        except Exception as e:
            print(f"Erro na query por UF: {e}")
            return []
        finally:
            if db is not None:
                db.close()


    def get_operadoras_acima_media(self):
        """
        Executa a Query 3: Operadoras consistentemente acima da média.
        """
        sql = text("""
        WITH despesas_por_trimestre AS (
            SELECT reg_ans, ano, trimestre, SUM(vl_saldo_final) as total_operadora
            FROM despesas_consolidadas
            GROUP BY reg_ans, ano, trimestre
        ),
        media_geral_trimestre AS (
            SELECT ano, trimestre, AVG(total_operadora) as media_mercado
            FROM despesas_por_trimestre
            GROUP BY ano, trimestre
        ),
        analise_performance AS (
            SELECT 
                d.reg_ans,
                CASE WHEN d.total_operadora > m.media_mercado THEN 1 ELSE 0 END as acima_da_media
            FROM despesas_por_trimestre d
            JOIN media_geral_trimestre m ON d.ano = m.ano AND d.trimestre = m.trimestre
        )
        SELECT COUNT(*) as qtd_operadoras_top_gastos
        FROM (
            SELECT reg_ans
            FROM analise_performance
            GROUP BY reg_ans
            HAVING SUM(acima_da_media) >= 2
        ) operadoras_filtradas;
        """)
        
        db = None
        try:
            db = self.db()
            result = db.execute(sql).scalar() # scalar() pega o único valor retornado

            return {"qtd_operadoras_consistentes": result}
        except Exception as e:
            print(f"Erro na query de consistência: {e}")
            return {"qtd_operadoras_consistentes": 0}
        finally:
            if db is not None:
                db.close()
                
    def get_todas_operadoras(self, page=1, limit=10, termo_busca=None):
        """Busca operadoras com paginação e filtro opcional (Item 4.2 e 4.3)"""
        offset = (page - 1) * limit
        
        # Base da query
        query_str = "SELECT registro_ans, cnpj, razao_social, modalidade, uf FROM operadoras_ativas"
        params = {}
        
        # Adiciona filtro de busca se houver (Item 4.3)
        if termo_busca:
            query_str += " WHERE razao_social ILIKE :busca OR cnpj ILIKE :busca"
            params["busca"] = f"%{termo_busca}%"
        
        query_str += " ORDER BY razao_social LIMIT :limit OFFSET :offset"
        params["limit"] = limit
        params["offset"] = offset
        
        # Query para contar total (para metadados da paginação)
        count_query_str = "SELECT COUNT(*) FROM operadoras_ativas"
        if termo_busca:
            count_query_str += " WHERE razao_social ILIKE :busca OR cnpj ILIKE :busca"

        db = None
        try:
            db = self.db()
            # Busca dados
            result = db.execute(text(query_str), params).fetchall()
            operadoras = [
                {
                    "registro_ans": row.registro_ans,
                    "cnpj": row.cnpj,
                    "razao_social": row.razao_social,
                    "uf": row.uf,
                    "modalidade": row.modalidade
                } for row in result
            ]
            
            # Busca total para paginação
            total = db.execute(text(count_query_str), params).scalar()
            
            return {"data": operadoras, "total": total, "page": page, "limit": limit}
        except Exception as e:
            print(f"Erro ao buscar operadoras: {e}")
            return {"data": [], "total": 0}
        finally:
            if db: db.close()

    def get_operadora_detalhes(self, cnpj_busca):
        """Busca detalhes de uma operadora específica pelo CNPJ"""
        sql = text("SELECT * FROM operadoras_ativas WHERE cnpj = :cnpj")
        
        db = None
        try:
            db = self.db()
            row = db.execute(sql, {"cnpj": cnpj_busca}).fetchone()
            
            if row:
                return {
                    "registro_ans": row.registro_ans,
                    "cnpj": row.cnpj,
                    "razao_social": row.razao_social,
                    "modalidade": row.modalidade,
                    "uf": row.uf
                }
            return None
        finally:
            if db: db.close()

    def get_despesas_historico(self, cnpj_busca):
        """Busca histórico de despesas de uma operadora pelo CNPJ"""
        sql = text("""
            SELECT d.ano, d.trimestre, d.vl_saldo_final, d.cd_conta_contabil
            FROM despesas_consolidadas d
            JOIN operadoras_ativas o ON d.reg_ans = o.registro_ans
            WHERE o.cnpj = :cnpj
            ORDER BY d.ano DESC, d.trimestre DESC
        """)
        
        db = None
        try:
            db = self.db()
            result = db.execute(sql, {"cnpj": cnpj_busca}).fetchall()
            return [
                {
                    "ano": row.ano,
                    "trimestre": row.trimestre,
                    "valor": float(row.vl_saldo_final),
                    "conta": row.cd_conta_contabil
                } for row in result
            ]
        finally:
            if db: db.close()
