from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import SessaoLocal
from security import validar_tenant_logado
from services import servico_profissional_service


router = APIRouter()


class AtualizarProfissionaisServico(BaseModel):
    profissional_ids: list[int] = []


def get_db():
    db = SessaoLocal()

    try:
        yield db
    finally:
        db.close()


@router.get("/api/{tenant_slug}/servicos/{servico_id}/profissionais")
def listar_profissionais_do_servico(
    tenant_slug: str,
    servico_id: int,
    db: Session = Depends(get_db),
    _tenant_autorizado: str = Depends(validar_tenant_logado),
):
    return {
        "profissionais": servico_profissional_service.listar_profissionais_do_servico(
            db,
            tenant_slug,
            servico_id,
        )
    }


@router.put("/api/{tenant_slug}/servicos/{servico_id}/profissionais")
def atualizar_profissionais_do_servico(
    tenant_slug: str,
    servico_id: int,
    dados: AtualizarProfissionaisServico,
    db: Session = Depends(get_db),
    _tenant_autorizado: str = Depends(validar_tenant_logado),
):
    profissionais = servico_profissional_service.substituir_profissionais_do_servico(
        db,
        tenant_slug,
        servico_id,
        dados.profissional_ids,
    )

    if profissionais is None:
        raise HTTPException(
            status_code=404,
            detail="Servico nao encontrado.",
        )

    return {
        "profissionais": profissionais,
    }
