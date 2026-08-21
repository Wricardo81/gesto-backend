import json

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.orm import Session

import models
from database import SessaoLocal
from security import gerar_hash_senha, validar_tenant_logado


router = APIRouter()


def get_db():
    db = SessaoLocal()

    try:
        yield db
    finally:
        db.close()


PERMISSOES_PADRAO_POR_PAPEL = {
    "gestor": ["*"],
    "recepcao": [
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
    "prestador": [
        "ver_dashboard_operacional",
        "ver_agenda_propria",
        "concluir_agendamento",
        "marcar_falta",
        "ver_clientes_dos_proprios_atendimentos",
        "ver_financeiro_proprio",
        "ver_comissao_propria",
    ],
}


class NovoUsuarioOperacional(BaseModel):
    nome: str = Field(min_length=2, max_length=120)
    email: EmailStr
    senha: str = Field(min_length=6, max_length=120)
    papel: str = Field(default="prestador")
    profissional_nome: str | None = None
    permissoes: list[str] | None = None
    ativo: bool = True


class AtualizarUsuarioOperacional(BaseModel):
    nome: str | None = Field(default=None, min_length=2, max_length=120)
    email: EmailStr | None = None
    senha: str | None = Field(default=None, min_length=6, max_length=120)
    papel: str | None = None
    profissional_nome: str | None = None
    permissoes: list[str] | None = None
    ativo: bool | None = None


def normalizar_papel(papel: str | None) -> str:
    papel_normalizado = str(papel or "prestador").strip().lower()

    if papel_normalizado not in {"gestor", "recepcao", "prestador"}:
        raise HTTPException(
            status_code=400,
            detail="Papel operacional invalido.",
        )

    return papel_normalizado


def normalizar_email(email: str) -> str:
    return str(email).strip().lower()


def montar_permissoes(papel: str, permissoes: list[str] | None) -> list[str]:
    if permissoes:
        return [
            str(permissao).strip()
            for permissao in permissoes
            if str(permissao).strip()
        ]

    return PERMISSOES_PADRAO_POR_PAPEL.get(papel, [])


def serializar_usuario_operacional(usuario: models.UsuarioOperacional) -> dict:
    try:
        permissoes = json.loads(usuario.permissoes_json or "[]")
    except json.JSONDecodeError:
        permissoes = []

    return {
        "id": usuario.id,
        "barbearia_slug": usuario.barbearia_slug,
        "nome": usuario.nome,
        "email": usuario.email,
        "papel": usuario.papel,
        "permissoes": permissoes,
        "profissional_nome": usuario.profissional_nome,
        "ativo": usuario.ativo,
        "criado_em": usuario.criado_em.isoformat()
        if usuario.criado_em
        else None,
    }


@router.get("/api/{tenant_slug}/admin/usuarios-operacionais")
def listar_usuarios_operacionais(
    tenant_slug: str,
    db: Session = Depends(get_db),
    _tenant_autorizado: str = Depends(validar_tenant_logado),
):
    usuarios = (
        db.query(models.UsuarioOperacional)
        .filter(models.UsuarioOperacional.barbearia_slug == tenant_slug)
        .order_by(models.UsuarioOperacional.nome.asc())
        .all()
    )

    return {
        "usuarios": [
            serializar_usuario_operacional(usuario)
            for usuario in usuarios
        ]
    }


@router.post("/api/{tenant_slug}/admin/usuarios-operacionais")
def criar_usuario_operacional(
    tenant_slug: str,
    dados: NovoUsuarioOperacional,
    db: Session = Depends(get_db),
    _tenant_autorizado: str = Depends(validar_tenant_logado),
):
    papel = normalizar_papel(dados.papel)
    email = normalizar_email(dados.email)

    existente = (
        db.query(models.UsuarioOperacional)
        .filter(
            models.UsuarioOperacional.barbearia_slug == tenant_slug,
            models.UsuarioOperacional.email == email,
        )
        .first()
    )

    if existente:
        raise HTTPException(
            status_code=409,
            detail="Ja existe um usuario operacional com este e-mail.",
        )

    profissional_nome = (
        str(dados.profissional_nome).strip()
        if dados.profissional_nome
        else None
    )

    if papel == "prestador" and not profissional_nome:
        raise HTTPException(
            status_code=400,
            detail="Prestador precisa estar vinculado a um profissional.",
        )

    usuario = models.UsuarioOperacional(
        barbearia_slug=tenant_slug,
        nome=dados.nome.strip(),
        email=email,
        senha_hash=gerar_hash_senha(dados.senha),
        papel=papel,
        permissoes_json=json.dumps(
            montar_permissoes(papel, dados.permissoes),
            ensure_ascii=False,
        ),
        profissional_nome=profissional_nome,
        ativo=dados.ativo,
    )

    db.add(usuario)
    db.commit()
    db.refresh(usuario)

    return serializar_usuario_operacional(usuario)


@router.put("/api/{tenant_slug}/admin/usuarios-operacionais/{usuario_id}")
def atualizar_usuario_operacional(
    tenant_slug: str,
    usuario_id: int,
    dados: AtualizarUsuarioOperacional,
    db: Session = Depends(get_db),
    _tenant_autorizado: str = Depends(validar_tenant_logado),
):
    usuario = (
        db.query(models.UsuarioOperacional)
        .filter(
            models.UsuarioOperacional.id == usuario_id,
            models.UsuarioOperacional.barbearia_slug == tenant_slug,
        )
        .first()
    )

    if not usuario:
        raise HTTPException(
            status_code=404,
            detail="Usuario operacional nao encontrado.",
        )

    if dados.nome is not None:
        usuario.nome = dados.nome.strip()

    if dados.email is not None:
        usuario.email = normalizar_email(dados.email)

    if dados.senha:
        usuario.senha_hash = gerar_hash_senha(dados.senha)

    if dados.papel is not None:
        usuario.papel = normalizar_papel(dados.papel)

    if dados.profissional_nome is not None:
        usuario.profissional_nome = (
            dados.profissional_nome.strip()
            if dados.profissional_nome.strip()
            else None
        )

    if dados.permissoes is not None:
        usuario.permissoes_json = json.dumps(
            montar_permissoes(usuario.papel, dados.permissoes),
            ensure_ascii=False,
        )

    if dados.ativo is not None:
        usuario.ativo = dados.ativo

    if usuario.papel == "prestador" and not usuario.profissional_nome:
        raise HTTPException(
            status_code=400,
            detail="Prestador precisa estar vinculado a um profissional.",
        )

    db.commit()
    db.refresh(usuario)

    return serializar_usuario_operacional(usuario)
