from sqlalchemy import create_engine, Column, String, Integer, ForeignKey, Numeric
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from typing import Any
DATABASE_URL = "postgresql://postgres:darkvortex@localhost:5432/intuitive_care"

engine = create_engine(DATABASE_URL)

# Criação da Sessão (Para realizar as operações na DB)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base : Any = declarative_base()
class OperadorasAtivas(Base):
    """Tabela de Dados Cadastrais das Operadoras de plano de saúde"""
    __tablename__ = 'operadoras_ativas'
    registro_ans = Column(String, primary_key=True, index=True) # O Registro ANS é o que liga ao arquivo de despesas
    cnpj = Column(String) # cnpj duplicados são tratados no ETL.py
    razao_social = Column(String)
    modalidade = Column(String)
    uf = Column(String)  
class DespesasConsolidadas(Base):
    """Tabela para armazenar os dados do CSV de despesas consolidadas"""
    __tablename__ = 'despesas_consolidadas'
    id = Column(Integer, primary_key=True, autoincrement=True)
    reg_ans = Column(String)
    cd_conta_contabil = Column(String)
    vl_saldo_final = Column(Numeric(18, 2)) #Suporta números com 18 digitos (Trilhão) e limita a duas casas decimais
    ano = Column(Integer)
    trimestre = Column(Integer)

def criar_tabelas():
    Base.metadata.create_all(bind=engine)
    print("Tabelas criadas com sucesso no banco 'intuitive_care'!")

if __name__ == "__main__":
    criar_tabelas()