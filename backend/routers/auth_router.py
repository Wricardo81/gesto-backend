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
    email_normalizado = credenciais.email.strip().lower()

    usuario = (
        db.query(models.Barbearia)
        .filter(models.Barbearia.email == email_normalizado)
        .first()
    )

    if (
        usuario
        and usuario.senha_hash
        and verificar_senha(credenciais.senha, usuario.senha_hash)
    ):
        token = criar_token_acesso(
            {
                "sub": usuario.slug,
                "tenant_slug": usuario.slug,
                "email": usuario.email,
                "role": "tenant_admin",
                "papel": "gestor",
                "perfil_operacional": "gestor",
                "papel_operacional": "gestor",
                "permissoes": ["*"],
                "nome": usuario.nome,
            }
        )

        return {
            "access_token": token,
            "token_type": "bearer",
            "tenant_slug": usuario.slug,
        }

    usuario_operacional = (
        db.query(models.UsuarioOperacional)
        .filter(models.UsuarioOperacional.email == email_normalizado)
        .first()
    )

    if (
        not usuario_operacional
        or not usuario_operacional.ativo
        or not usuario_operacional.senha_hash
        or not verificar_senha(
            credenciais.senha,
            usuario_operacional.senha_hash,
        )
    ):
        raise HTTPException(
            status_code=401,
            detail="E-mail ou senha incorretos.",
        )

    import json

    try:
        permissoes = json.loads(usuario_operacional.permissoes_json or "[]")
    except json.JSONDecodeError:
        permissoes = []

    token = criar_token_acesso(
        {
            "sub": usuario_operacional.barbearia_slug,
            "tenant_slug": usuario_operacional.barbearia_slug,
            "email": usuario_operacional.email,
            "role": "tenant_admin",
            "papel": usuario_operacional.papel,
            "perfil_operacional": usuario_operacional.papel,
            "papel_operacional": usuario_operacional.papel,
            "permissoes": permissoes,
            "profissional_nome": usuario_operacional.profissional_nome,
            "usuario_operacional_id": usuario_operacional.id,
            "nome": usuario_operacional.nome,
        }
    )

    return {
        "access_token": token,
        "token_type": "bearer",
        "tenant_slug": usuario_operacional.barbearia_slug,
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
            "profissional_nome": contexto.get("profissional_nome"),
            "usuario_operacional_id": contexto.get("usuario_operacional_id"),
            "nome": contexto.get("nome"),
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

