from __future__ import annotations
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from .. import models, schemas
from ..database import get_db
from ..dependencies import exigir_acesso_escola, exigir_gestao_escola, exigir_perfil, get_current_user

router=APIRouter(prefix="/api/diretor", tags=["diretor"])

@router.get("/professores")
async def professores(db: AsyncSession=Depends(get_db), usuario: models.Usuario=Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.DIRETOR); exigir_acesso_escola(usuario, usuario.escola_id)
    return (await db.execute(select(models.Usuario).where(models.Usuario.escola_id==usuario.escola_id, models.Usuario.perfil==models.Perfil.PROFESSOR, models.Usuario.ativo.is_(True)).order_by(models.Usuario.nome))).scalars().all()

@router.get("/turmas")
async def turmas(db: AsyncSession=Depends(get_db), usuario: models.Usuario=Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.DIRETOR); exigir_acesso_escola(usuario, usuario.escola_id)
    return (await db.execute(select(models.Turma).where(models.Turma.escola_id==usuario.escola_id, models.Turma.ativo.is_(True)).order_by(models.Turma.ano_letivo.desc(), models.Turma.nome))).scalars().all()

@router.get("/alunos")
async def alunos(db: AsyncSession=Depends(get_db), usuario: models.Usuario=Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.DIRETOR); exigir_acesso_escola(usuario, usuario.escola_id)
    return (await db.execute(select(models.Aluno).where(models.Aluno.escola_id==usuario.escola_id, models.Aluno.ativo.is_(True)).order_by(models.Aluno.nome))).scalars().all()

@router.post("/turmas/{turma_id}/professores/{professor_id}")
async def vincular_professor(turma_id:int, professor_id:int, db:AsyncSession=Depends(get_db), usuario:models.Usuario=Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.DIRETOR); exigir_acesso_escola(usuario, usuario.escola_id)
    turma=await db.get(models.Turma,turma_id); professor=await db.get(models.Usuario,professor_id)
    if turma is None or professor is None or turma.escola_id != usuario.escola_id or professor.escola_id != usuario.escola_id or professor.perfil != models.Perfil.PROFESSOR:
        raise HTTPException(422,"Professor e turma devem pertencer à escola do diretor")
    db.add(models.ProfessorTurma(professor_id=professor_id,turma_id=turma_id)); await db.commit(); return {"status":"ok"}
