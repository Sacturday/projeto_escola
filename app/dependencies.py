from __future__ import annotations

from fastapi import Depends, HTTPException, Request, WebSocket, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models
from .database import get_db
from .security import decodificar_token


async def _usuario_por_token(token: str | None, db: AsyncSession) -> models.Usuario:
    erro = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")
    if not token:
        raise erro

    payload = decodificar_token(token)
    if payload is None or "sub" not in payload:
        raise erro

    usuario = (
        await db.execute(
            select(models.Usuario).where(
                models.Usuario.username == payload["sub"],
                models.Usuario.ativo.is_(True),
            )
        )
    ).scalar_one_or_none()

    if usuario is None:
        raise erro
    return usuario


async def get_current_user(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> models.Usuario:
    return await _usuario_por_token(request.cookies.get("access_token"), db)


async def get_current_user_pagina(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> models.Usuario:
    redireciona = HTTPException(status_code=303, headers={"Location": "/"})
    try:
        return await _usuario_por_token(request.cookies.get("access_token"), db)
    except HTTPException:
        raise redireciona


async def get_current_user_websocket(
    websocket: WebSocket,
    db: AsyncSession = Depends(get_db),
) -> models.Usuario:
    return await _usuario_por_token(websocket.cookies.get("access_token"), db)


def exigir_perfil(usuario: models.Usuario, *perfis: models.Perfil) -> None:
    if usuario.perfil not in perfis:
        raise HTTPException(status_code=403, detail="Perfil sem permissão para esta operação")


def exigir_acesso_escola(usuario: models.Usuario, escola_id: int) -> None:
    if usuario.perfil == models.Perfil.ADMIN:
        return
    if usuario.escola_id != escola_id:
        raise HTTPException(status_code=403, detail="Sem permissão para esta escola")


async def exigir_acesso_turma(
    usuario: models.Usuario,
    turma_id: int,
    db: AsyncSession,
) -> models.Turma:
    turma = await db.get(models.Turma, turma_id)
    if turma is None or not turma.ativo:
        raise HTTPException(status_code=404, detail="Turma não encontrada")

    exigir_acesso_escola(usuario, turma.escola_id)

    if usuario.perfil == models.Perfil.PROFESSOR:
        vinculo = (
            await db.execute(
                select(models.ProfessorTurma).where(
                    models.ProfessorTurma.professor_id == usuario.id,
                    models.ProfessorTurma.turma_id == turma_id,
                )
            )
        ).scalar_one_or_none()
        if vinculo is None:
            raise HTTPException(status_code=403, detail="Professor não vinculado a esta turma")

    return turma


def exigir_gestao_escola(usuario: models.Usuario, escola_id: int) -> None:
    exigir_perfil(usuario, models.Perfil.ADMIN, models.Perfil.DIRETOR)
    exigir_acesso_escola(usuario, escola_id)
