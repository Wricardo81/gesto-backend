from sqlalchemy import Column, Integer, String, Float
from database import Base

# 1. TABELA DE AGENDAMENTOS (ATUALIZADA)
class Agendamento(Base):
    __tablename__ = "agendamentos"
    id = Column(Integer, primary_key=True, index=True)
    cliente_nome = Column(String)
    servico = Column(String)
    horario = Column(String)
    valor = Column(Float)
    profissional = Column(String) # NOVO: Com quem é o serviço?

# 2. TABELA DE SERVIÇOS
class ServicoBarbearia(Base):
    __tablename__ = "servicos"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String)  
    preco = Column(Float)
    duracao = Column(Integer)

# 3. TABELA DE CONFIGURAÇÕES (ATUALIZADA)
class ConfiguracaoAgenda(Base):
    __tablename__ = "configuracoes"
    id = Column(Integer, primary_key=True, index=True)
    hora_abertura = Column(Integer, default=9)   
    hora_fechamento = Column(Integer, default=18)
    # A NOSSA NOVA COLUNA DE DESIGN
    cor_tema = Column(String, default="#f59e0b") 

# 4. TABELA DA EQUIPE (NOVA)
class Profissional(Base):
    __tablename__ = "profissionais"
    id = Column(Integer, primary_key=True, index=True)
    nome = Column(String) # Ex: Marcos, João