from __future__ import annotations

from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, schemas
from ..database import get_db
from ..dependencies import exigir_acesso_escola, exigir_acesso_turma, exigir_perfil, get_current_user
from ..services import listar_linhas_frequencia
from ..timezone import hoje_rede
from .websockets import websocket_manager

router = APIRouter(prefix="/api/frequencias", tags=["frequencias"])


@router.get("/")
async def listar_frequencias(
    turma_id: int,
    data: date,
    db: AsyncSession = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    turma = await exigir_acesso_turma(usuario, turma_id, db)
    linhas = await listar_linhas_frequencia(db, turma.id, data)
    return [
        schemas.FrequenciaLinha(
            aluno_id=aluno.id,
            turma_id=turma.id,
            nome_aluno=aluno.nome,
            matricula=aluno.matricula,
            data=data,
            frequencia_id=freq.id if freq else None,
            status=schemas.StatusChamada(freq.status.value) if freq else schemas.StatusChamada.NEUTRO,
            versao=freq.versao if freq else None,
        )
        for aluno, freq in linhas
    ]


@router.post("/confirmar")
async def confirmar_frequencias(
    dados: schemas.ConfirmarFrequenciasRequest,
    db: AsyncSession = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    # Somente PROFESSOR registra a chamada. ADMIN/DIRETOR utilizam PATCH para correções.
    exigir_perfil(usuario, models.Perfil.PROFESSOR)
    if not dados.lancamentos:
        raise HTTPException(status_code=422, detail="Nenhum lançamento informado")

    turmas = {item.turma_id for item in dados.lancamentos}
    datas = {item.data for item in dados.lancamentos}
    if len(turmas) != 1 or len(datas) != 1:
        raise HTTPException(status_code=422, detail="Uma confirmação deve conter uma única turma e uma única data")
    turma_id = next(iter(turmas))
    data = next(iter(datas))
    await exigir_acesso_turma(usuario, turma_id, db)
    if data != hoje_rede():
        raise HTTPException(status_code=422, detail="Professor só pode lançar a chamada do dia atual")

    ids_enviados = [item.aluno_id for item in dados.lancamentos]
    if len(ids_enviados) != len(set(ids_enviados)):
        raise HTTPException(status_code=422, detail="Há aluno duplicado nos lançamentos")

    esperado = {
        aluno_id
        for (aluno_id,) in (await db.execute(
            select(models.Aluno.id)
            .join(models.Matricula, models.Matricula.aluno_id == models.Aluno.id)
            .where(
                models.Matricula.turma_id == turma_id,
                models.Matricula.status == models.StatusMatricula.ATIVA,
                models.Matricula.data_inicio <= data,
                models.Matricula.data_fim.is_(None) | (models.Matricula.data_fim >= data),
                models.Aluno.ativo.is_(True),
            )
        )).all()
    }
    recebidos = set(ids_enviados)
    if recebidos != esperado:
        faltantes = sorted(esperado - recebidos)
        extras = sorted(recebidos - esperado)
        raise HTTPException(status_code=422, detail={"mensagem": "A chamada deve conter exatamente todos os alunos matriculados e ativos", "faltantes": faltantes, "extras": extras})

    conflitos: list[dict] = []
    atualizados: list[int] = []
    for item in dados.lancamentos:
        aluno = await db.get(models.Aluno, item.aluno_id)
        if aluno is None:
            conflitos.append({"aluno_id": item.aluno_id, "motivo": "aluno não encontrado"})
            continue

        frequencia = (await db.execute(
            select(models.Frequencia)
            .where(models.Frequencia.aluno_id == item.aluno_id, models.Frequencia.turma_id == turma_id, models.Frequencia.data == data)
            .with_for_update()
        )).scalar_one_or_none()
        novo_status = models.StatusFrequencia(item.status.value)

        if frequencia is None:
            frequencia = models.Frequencia(
                aluno_id=item.aluno_id, turma_id=turma_id, data=data, status=novo_status, registrado_por=usuario.id, versao=1
            )
            db.add(frequencia)
            await db.flush()
            db.add(models.FrequenciaAuditoria(
                frequencia_id=frequencia.id, usuario_id=usuario.id, valor_anterior=None, valor_novo=novo_status, motivo="Lançamento inicial da chamada"
            ))
        else:
            if frequencia.status == models.StatusFrequencia.FALTA_JUSTIFICADA:
                conflitos.append({"aluno_id": item.aluno_id, "motivo": "falta já justificada não pode ser alterada pela chamada"})
                continue
            if item.frequencia_id != frequencia.id or item.versao != frequencia.versao:
                conflitos.append({"aluno_id": item.aluno_id, "motivo": "versão desatualizada"})
                continue
            if frequencia.status != novo_status:
                antigo = frequencia.status
                frequencia.status = novo_status
                frequencia.versao += 1
                frequencia.registrado_por = usuario.id
                db.add(models.FrequenciaAuditoria(
                    frequencia_id=frequencia.id, usuario_id=usuario.id, valor_anterior=antigo, valor_novo=novo_status, motivo="Alteração na chamada"
                ))
        atualizados.append(frequencia.id)

    if conflitos:
        await db.rollback()
        raise HTTPException(status_code=409, detail={"conflitos": conflitos})

    await db.commit()
    await websocket_manager.broadcast_to_escola(usuario.escola_id, "<div id='estatisticas-rede'>Atualizado</div>")
    return {"status": "ok", "atualizados": atualizados}


@router.patch("/{frequencia_id}")
async def atualizar_frequencia(
    frequencia_id: int,
    dados: schemas.FrequenciaUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    exigir_perfil(usuario, models.Perfil.ADMIN, models.Perfil.DIRETOR)
    frequencia = (await db.execute(select(models.Frequencia).where(models.Frequencia.id == frequencia_id).with_for_update())).scalar_one_or_none()
    if not frequencia:
        raise HTTPException(status_code=404, detail="Registro não encontrado")
    turma = await db.get(models.Turma, frequencia.turma_id)
    if turma is None:
        raise HTTPException(status_code=404, detail="Turma não encontrada")
    exigir_acesso_escola(usuario, turma.escola_id)
    if frequencia.versao != dados.versao:
        raise HTTPException(status_code=409, detail="Conflito: registro modificado por outro usuário")
    antigo = frequencia.status
    novo = models.StatusFrequencia(dados.status.value)
    if antigo != novo:
        frequencia.status = novo
        frequencia.versao += 1
        frequencia.registrado_por = usuario.id
        db.add(models.FrequenciaAuditoria(
            frequencia_id=frequencia.id, usuario_id=usuario.id, valor_anterior=antigo, valor_novo=novo, motivo=dados.motivo or "Correção administrativa"
        ))
    await db.commit()
    await db.refresh(frequencia)
    await websocket_manager.broadcast_to_escola(turma.escola_id, "<div id='estatisticas-rede'>Atualizado</div>")
    return frequencia
