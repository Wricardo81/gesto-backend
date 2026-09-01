from sqlalchemy.orm import Session

import models


def listar_profissionais_do_servico(
    db: Session,
    tenant_slug: str,
    servico_id: int,
):
    vinculos = (
        db.query(models.ServicoProfissional, models.Profissional)
        .join(
            models.Profissional,
            models.Profissional.id == models.ServicoProfissional.profissional_id,
        )
        .filter(
            models.ServicoProfissional.barbearia_slug == tenant_slug,
            models.ServicoProfissional.servico_id == servico_id,
            models.Profissional.barbearia_slug == tenant_slug,
        )
        .order_by(models.Profissional.nome.asc())
        .all()
    )

    return [
        {
            "id": profissional.id,
            "nome": profissional.nome,
            "comissao_tipo": profissional.comissao_tipo or "nenhuma",
            "comissao_valor": float(profissional.comissao_valor or 0),
        }
        for _, profissional in vinculos
    ]


def substituir_profissionais_do_servico(
    db: Session,
    tenant_slug: str,
    servico_id: int,
    profissional_ids: list[int],
):
    servico = (
        db.query(models.ServicoBarbearia)
        .filter(
            models.ServicoBarbearia.id == servico_id,
            models.ServicoBarbearia.barbearia_slug == tenant_slug,
        )
        .first()
    )

    if not servico:
        return None

    ids_limpos = sorted({
        int(profissional_id)
        for profissional_id in profissional_ids
        if profissional_id
    })

    profissionais_validos = (
        db.query(models.Profissional)
        .filter(
            models.Profissional.barbearia_slug == tenant_slug,
            models.Profissional.id.in_(ids_limpos),
        )
        .all()
        if ids_limpos
        else []
    )

    ids_validos = {profissional.id for profissional in profissionais_validos}

    db.query(models.ServicoProfissional).filter(
        models.ServicoProfissional.barbearia_slug == tenant_slug,
        models.ServicoProfissional.servico_id == servico_id,
    ).delete(synchronize_session=False)

    for profissional_id in ids_validos:
        db.add(
            models.ServicoProfissional(
                barbearia_slug=tenant_slug,
                servico_id=servico_id,
                profissional_id=profissional_id,
            )
        )

    db.commit()

    return listar_profissionais_do_servico(db, tenant_slug, servico_id)


def profissional_pode_executar_servico(
    db: Session,
    tenant_slug: str,
    servico_id: int,
    profissional_id: int,
) -> bool:
    total_vinculos = (
        db.query(models.ServicoProfissional)
        .filter(
            models.ServicoProfissional.barbearia_slug == tenant_slug,
            models.ServicoProfissional.servico_id == servico_id,
        )
        .count()
    )

    if total_vinculos == 0:
        return True

    vinculo = (
        db.query(models.ServicoProfissional)
        .filter(
            models.ServicoProfissional.barbearia_slug == tenant_slug,
            models.ServicoProfissional.servico_id == servico_id,
            models.ServicoProfissional.profissional_id == profissional_id,
        )
        .first()
    )

    return vinculo is not None
