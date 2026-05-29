from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

# Aqui definimos o endereço do nosso banco de dados.
# Estamos usando o SQLite local. No futuro, trocaremos essa string pela do PostgreSQL!
URL_DO_BANCO = "sqlite:///./gesto.db"

# O Engine é o motor que efetivamente se comunica com o banco
engine = create_engine(
    URL_DO_BANCO, connect_args={"check_same_thread": False}
)

# A Sessão é a nossa "conversa" com o banco (para salvar ou buscar dados)
SessaoLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base é a classe mãe que todas as nossas tabelas vão herdar
Base = declarative_base()