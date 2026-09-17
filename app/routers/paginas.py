from __future__ import annotations

from datetime import date

from ..timezone import hoje_rede

from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..database import get_db
from ..dependencies import exigir_perfil, exigir_acesso_turma, get_current_user_pagina
from ..services import listar_linhas_frequencia


templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


@router.get("/")
async def pagina_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/turmas")
async def pagina_turmas(
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user_pagina),
):
    exigir_perfil(usuario, models.Perfil.PROFESSOR)

    contagem = (
        select(models.Matricula.turma_id, func.count(models.Matricula.aluno_id).label("total"))
        .where(models.Matricula.status == models.StatusMatricula.ATIVA)
        .group_by(models.Matricula.turma_id)
        .subquery()
    )

    resultado = await db.execute(
        select(models.Turma, models.Escola, contagem.c.total)
        .join(models.ProfessorTurma, models.ProfessorTurma.turma_id == models.Turma.id)
        .join(models.Escola, models.Escola.id == models.Turma.escola_id)
        .outerjoin(contagem, contagem.c.turma_id == models.Turma.id)
        .where(
            models.ProfessorTurma.professor_id == usuario.id,
            models.Turma.ativo.is_(True),
        )
        .order_by(models.Turma.nome)
    )

    return templates.TemplateResponse(
        "turmas.html",
        {
            "request": request,
            "usuario": usuario,
            "turmas": resultado.all(),
        },
    )


@router.get("/painel/{turma_id}")
async def pagina_painel(
    turma_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user_pagina),
):
    exigir_perfil(usuario, models.Perfil.PROFESSOR)
    turma = await exigir_acesso_turma(usuario, turma_id, db)

    hoje = hoje_rede()
    linhas = await listar_linhas_frequencia(db, turma.id, hoje)

    return templates.TemplateResponse(
        "painel_prof.html",
        {
            "request": request,
            "usuario": usuario,
            "turma": turma,
            "linhas": linhas,
            "hoje": hoje,
        },
    )
