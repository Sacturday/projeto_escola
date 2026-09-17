from __future__ import annotations
from datetime import date
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from . import models

async def listar_linhas_frequencia(db: AsyncSession, turma_id: int, data: date):
    resultado = await db.execute(
        select(models.Aluno, models.Frequencia)
        .join(models.Matricula, models.Matricula.aluno_id == models.Aluno.id)
        .outerjoin(models.Frequencia, (models.Frequencia.aluno_id == models.Aluno.id) & (models.Frequencia.turma_id == turma_id) & (models.Frequencia.data == data))
        .where(models.Matricula.turma_id == turma_id, models.Matricula.status == models.StatusMatricula.ATIVA, models.Matricula.data_inicio <= data, models.Matricula.data_fim.is_(None) | (models.Matricula.data_fim >= data), models.Aluno.ativo.is_(True))
        .order_by(models.Aluno.nome)
    )
    return resultado.all()
