import sys
from pathlib import Path

from sqlalchemy import inspect, text

sys.path.append(str(Path(__file__).resolve().parents[1]))

from database import engine


def criar_tabela_servico_profissionais():
    inspector = inspect(engine)

    if inspector.has_table("servico_profissionais"):
        print("Tabela servico_profissionais ja existe.")
        return

    sql = """
    CREATE TABLE servico_profissionais (
        id SERIAL PRIMARY KEY,
        barbearia_slug VARCHAR NOT NULL,
        servico_id INTEGER NOT NULL REFERENCES servicos(id) ON DELETE CASCADE,
        profissional_id INTEGER NOT NULL REFERENCES profissionais(id) ON DELETE CASCADE,
        criado_em TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
        CONSTRAINT uq_servico_profissional_tenant UNIQUE (
            barbearia_slug,
            servico_id,
            profissional_id
        )
    )
    """

    with engine.begin() as conexao:
        conexao.execute(text(sql))

    print("Tabela servico_profissionais criada com sucesso.")


if __name__ == "__main__":
    criar_tabela_servico_profissionais()
