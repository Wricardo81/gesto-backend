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

@router.get("/api/auth/perfis-operacionais")
def listar_perfis_operacionais(
    _contexto: dict = Depends(obter_contexto_usuario_logado),
):
    return {
        "perfis": [
            {
                "codigo": "gestor",
                "nome": "Gestor",
                "descricao": "Acesso total ao painel, financeiro, equipe, servicos, agenda e configuracoes.",
                "permissoes_padrao": ["*"],
            },
            {
                "codigo": "recepcao",
                "nome": "Recep\u00e7\u00e3o",
                "descricao": "Atendimento operacional com foco em agenda, clientes, remarcacoes e fila de espera.",
                "permissoes_padrao": [
                    "ver_dashboard",
                    "ver_agenda_geral",
                    "criar_agendamento",
                    "editar_agendamento",
                    "cancelar_agendamento",
                    "marcar_falta",
                    "ver_clientes",
                    "criar_cliente",
                    "editar_cliente",
                    "ver_servicos",
                    "ver_profissionais",
                    "ver_fila_espera",
                    "gerenciar_fila_espera",
                ],
            },
            {
                "codigo": "prestador",
                "nome": "Prestador",
                "descricao": "Profissional que acompanha a propria agenda, atendimentos e resumo financeiro individual.",
                "permissoes_padrao": [
                    "ver_agenda_propria",
                    "concluir_agendamento",
                    "marcar_falta",
                    "ver_clientes_dos_proprios_atendimentos",
                    "ver_financeiro_proprio",
                    "ver_comissao_propria",
                ],
            },
        ]
    }

