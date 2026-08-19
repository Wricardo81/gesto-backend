from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from database import SessaoLocal
import models
from security import verificar_senha, criar_token_acesso, obter_contexto_usuario_logado

router = APIRouter()

def get_db():
    db = SessaoLocal()
    try:
        yield db
    finally:
        db.close()

class RequisicaoLogin(BaseModel):
    email: str
    senha: str

@router.post("/api/auth/login")
def fazer_login(
    credenciais: RequisicaoLogin,
    db: Session = Depends(get_db),
):
    usuario = (
        db.query(models.Barbearia)
        .filter(models.Barbearia.email == credenciais.email)
        .first()
    )

    if (
        not usuario
        or not usuario.senha_hash
        or not verificar_senha(credenciais.senha, usuario.senha_hash)
    ):
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha incorretos.",
        )

    token = criar_token_acesso(
    {
        "sub": usuario.slug,
        "role": "tenant_admin",

        "papel": "gestor",
        "perfil_operacional": "gestor",
        "papel_operacional": "gestor",
        "permissoes": ["*"],
    }
)

    return {
        "access_token": token,
        "token_type": "bearer",
        "tenant_slug": usuario.slug,
    }

@router.get("/api/auth/me")
def obter_meu_contexto(
    contexto: dict = Depends(obter_contexto_usuario_logado),
):
    return {
        "autenticado": True,
        "usuario": {
            "sub": contexto.get("sub"),
            "email": contexto.get("email"),
            "role": contexto.get("role"),
            "papel": contexto.get("papel"),
            "permissoes": contexto.get("permissoes", []),
        },
        "tenant": {
            "slug": contexto.get("tenant_slug"),
            "id": contexto.get("tenant_id"),
        },
    }

