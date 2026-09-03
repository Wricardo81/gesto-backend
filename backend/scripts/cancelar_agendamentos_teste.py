import argparse
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

import models
from database import SessaoLocal


def buscar_agendamentos_teste(db, tenant_slug: str):
    return (
        db.query(models.Agendamento)
        .filter(
            models.Agendamento.barbearia_slug == tenant_slug,
            models.Agendamento.status != "cancelado",
            (
                models.Agendamento.cliente_nome.ilike("Teste%")
                | (models.Agendamento.telefone_cliente == "81999999999")
            ),
        )
        .order_by(models.Agendamento.id.asc())
        .all()
    )


def cancelar_agendamentos_teste(tenant_slug: str, executar: bool):
    db = SessaoLocal()

    try:
        agendamentos = buscar_agendamentos_teste(db, tenant_slug)

        if not agendamentos:
            print("Nenhum agendamento de teste ativo encontrado.")
            return

        print(f"Agendamentos de teste encontrados: {len(agendamentos)}")

        for agendamento in agendamentos:
            print(
                f"- id={agendamento.id} | "
                f"cliente={agendamento.cliente_nome} | "
                f"servico={agendamento.servico} | "
                f"profissional={agendamento.profissional} | "
                f"data={agendamento.data} | "
                f"horario={agendamento.horario} | "
                f"status={agendamento.status}"
            )

        if not executar:
            print("")
            print("Modo simulacao: nada foi alterado.")
            print("Para cancelar, rode novamente com --executar.")
            return

        agora = datetime.now(timezone.utc)

        for agendamento in agendamentos:
            agendamento.status = "cancelado"
            agendamento.motivo_cancelamento = (
                "Agendamento de teste cancelado para limpeza de producao."
            )
            agendamento.cancelado_por = "sistema"
            agendamento.cancelado_em = agora
            agendamento.observacao_interna = (
                "Registro de teste mantido apenas para historico tecnico."
            )

        db.commit()

        print("")
        print(f"Agendamentos de teste cancelados: {len(agendamentos)}")

    finally:
        db.close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Cancela agendamentos de teste sem excluir historico."
    )

    parser.add_argument(
        "--tenant",
        required=True,
        help="Slug da empresa/tenant.",
    )

    parser.add_argument(
        "--executar",
        action="store_true",
        help="Aplica o cancelamento. Sem isso, roda apenas em modo simulacao.",
    )

    args = parser.parse_args()

    cancelar_agendamentos_teste(
        tenant_slug=args.tenant,
        executar=args.executar,
    )
