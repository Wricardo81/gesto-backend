import sys
from pathlib import Path

from sqlalchemy import text

BACKEND_DIR = Path(__file__).resolve().parents[1]

if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from database import engine


COMANDOS = [
    """
    ALTER TABLE profissionais
    ADD COLUMN IF NOT EXISTS comissao_tipo VARCHAR DEFAULT 'nenhuma' NOT NULL
    """,
    """
    ALTER TABLE profissionais
    ADD COLUMN IF NOT EXISTS comissao_valor FLOAT DEFAULT 0 NOT NULL
    """,
]


for comando in COMANDOS:
    with engine.begin() as conexao:
        conexao.execute(text(comando))

print("Comissoes de profissionais verificadas com sucesso.")
