from pydantic import BaseModel
from sqlalchemy.orm import Session

import models
from repositories import profissional_repository


class NovoProfissional(BaseModel):
    nome: str


class AtualizarComissaoProfissional(BaseModel):
    comissao_tipo: str = "nenhuma"
    comissao_valor: float = 0


def serializar_profissional(profissional: models.Profissional) -> dict:
    return {
        "id": profissional.id,
        "nome": profissional.nome,
        "comissao_tipo": profissional.comissao_tipo or "nenhuma",
        "comissao_valor": float(profissional.comissao_valor or 0),
    }


def cadastrar_novo_profissional(
    db: Session,
    tenant_slug: str,
    dados: NovoProfissional,
):
    profissional = models.Profissional(
        barbearia_slug=tenant_slug,
        nome=dados.nome,
        comissao_tipo="nenhuma",
        comissao_valor=0,
    )

    db.add(profissional)
    db.commit()
    db.refresh(profissional)

    return serializar_profissional(profissional)


def listar_profissionais(db: Session, tenant_slug: str):
    profissionais = profissional_repository.buscar_profissionais_por_tenant(
        db,
        tenant_slug,
    )

    return [
        serializar_profissional(profissional)
        for profissional in profissionais
    ]


def deletar_profissional(
    db: Session,
    prof_id: int,
    tenant_slug: str,
):
    profissional = (
        db.query(models.Profissional)
        .filter(
            models.Profissional.id == prof_id,
            models.Profissional.barbearia_slug == tenant_slug,
        )
        .first()
    )

    if not profissional:
        return False

    db.delete(profissional)
    db.commit()

    return True


def atualizar_comissao_profissional(
    db: Session,
    tenant_slug: str,
    prof_id: int,
    dados: AtualizarComissaoProfissional,
):
    profissional = (
        db.query(models.Profissional)
        .filter(
            models.Profissional.id == prof_id,
            models.Profissional.barbearia_slug == tenant_slug,
        )
        .first()
    )

    if not profissional:
        return None

    tipo = str(dados.comissao_tipo or "nenhuma").strip().lower()
    valor = float(dados.comissao_valor or 0)

    tipos_validos = {
        "nenhuma",
        "percentual",
        "valor_fixo",
    }

    if tipo not in tipos_validos:
        tipo = "nenhuma"

    if tipo == "nenhuma":
        valor = 0

    if valor < 0:
        valor = 0

    profissional.comissao_tipo = tipo
    profissional.comissao_valor = valor

    db.commit()
    db.refresh(profissional)

    return serializar_profissional(profissional)
