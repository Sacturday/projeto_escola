from __future__ import annotations

import json
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models
from ..database import AsyncSessionLocal, get_db
from ..dependencies import exigir_perfil, get_current_user
from ..importacao_excel import MAX_ERRORS_RETURNED, importar, ler_primeira_planilha, validar_colunas, validar_dados

router = APIRouter(prefix="/api/admin/importacoes", tags=["admin-importacoes"])


def _tipo(valor: str) -> models.TipoImportacao:
    try:
        return models.TipoImportacao(valor.upper())
    except ValueError as exc:
        raise HTTPException(status_code=400, detail="Tipo de importação inválido") from exc


@router.post("/preview")
async def preview_importacao(
    tipo: str, arquivo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db), usuario: models.Usuario = Depends(get_current_user),
):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    tipo_enum = _tipo(tipo)
    sheet_name, rows, sha256 = await ler_primeira_planilha(arquivo)
    erros = validar_colunas(tipo_enum, rows)
    if not erros:
        erros = await validar_dados(tipo_enum, rows, db)

    # A prévia validada fica registrada para que a confirmação posterior possa
    # ser vinculada ao mesmo arquivo por SHA-256 e por ID de operação.
    importacao = models.Importacao(
        usuario_id=usuario.id, tipo=tipo_enum,
        status=models.ImportacaoStatus.PREVIA_VALIDADA if not erros else models.ImportacaoStatus.FALHA,
        arquivo_nome=arquivo.filename or "arquivo", arquivo_sha256=sha256, linhas_lidas=len(rows),
        linhas_rejeitadas=len(erros), resumo_erro=json.dumps(erros[:MAX_ERRORS_RETURNED], ensure_ascii=False) if erros else None,
        finished_at=None if not erros else datetime.now(timezone.utc),
    )
    db.add(importacao)
    await db.commit()
    await db.refresh(importacao)
    return {
        "importacao_id": importacao.id, "tipo": tipo_enum.value, "planilha": sheet_name, "linhas": len(rows),
        "sha256": sha256, "validada": not erros, "erros": erros[:MAX_ERRORS_RETURNED], "amostra": rows[:10],
        "mensagem": "Prévia validada. Confirme a importação usando o mesmo arquivo." if not erros else "A importação deve ser corrigida antes de prosseguir.",
    }


@router.post("/confirmar")
async def confirmar_importacao(
    tipo: str, importacao_id: int, arquivo: UploadFile = File(...),
    db: AsyncSession = Depends(get_db), usuario: models.Usuario = Depends(get_current_user),
):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    tipo_enum = _tipo(tipo)

    operacao = await db.get(models.Importacao, importacao_id)
    if operacao is None or operacao.usuario_id != usuario.id or operacao.tipo != tipo_enum:
        raise HTTPException(status_code=404, detail="Prévia de importação não encontrada")
    if operacao.status != models.ImportacaoStatus.PREVIA_VALIDADA:
        raise HTTPException(status_code=409, detail="Esta prévia não está disponível para confirmação")

    sheet_name, rows, sha256 = await ler_primeira_planilha(arquivo)
    if sha256 != operacao.arquivo_sha256:
        raise HTTPException(status_code=409, detail="O arquivo confirmado é diferente do arquivo usado na prévia")

    erros = validar_colunas(tipo_enum, rows)
    if not erros:
        erros = await validar_dados(tipo_enum, rows, db)
    if erros:
        operacao.status = models.ImportacaoStatus.FALHA
        operacao.resumo_erro = json.dumps(erros[:MAX_ERRORS_RETURNED], ensure_ascii=False)
        operacao.linhas_rejeitadas = len(erros)
        operacao.finished_at = datetime.now(timezone.utc)
        await db.commit()
        raise HTTPException(status_code=422, detail={"importacao_id": operacao.id, "erros": erros[:MAX_ERRORS_RETURNED]})

    # A operação usa uma única transação para a carga dos dados. O registro de
    # importação foi persistido pela prévia e pode ser atualizado após rollback.
    try:
        importados, erros_execucao = await importar(tipo_enum, rows, db)
        if erros_execucao:
            await db.rollback()
            async with AsyncSessionLocal() as log_db:
                falha = await log_db.get(models.Importacao, importacao_id)
                falha.status = models.ImportacaoStatus.FALHA
                falha.linhas_rejeitadas = len(erros_execucao)
                falha.resumo_erro = json.dumps(erros_execucao[:MAX_ERRORS_RETURNED], ensure_ascii=False)
                falha.finished_at = datetime.now(timezone.utc)
                await log_db.commit()
            raise HTTPException(status_code=422, detail={"importacao_id": importacao_id, "erros": erros_execucao[:MAX_ERRORS_RETURNED]})

        operacao.status = models.ImportacaoStatus.CONCLUIDA
        operacao.linhas_importadas = importados
        operacao.linhas_rejeitadas = 0
        operacao.resumo_erro = None
        operacao.finished_at = datetime.now(timezone.utc)
        await db.commit()
        return {"status": "ok", "importacao_id": operacao.id, "tipo": tipo_enum.value, "linhas_lidas": len(rows), "linhas_importadas": importados, "planilha": sheet_name}
    except HTTPException:
        raise
    except Exception as exc:
        await db.rollback()
        async with AsyncSessionLocal() as log_db:
            falha = await log_db.get(models.Importacao, importacao_id)
            if falha:
                falha.status = models.ImportacaoStatus.FALHA
                falha.resumo_erro = str(exc)
                falha.linhas_rejeitadas = len(rows)
                falha.finished_at = datetime.now(timezone.utc)
                await log_db.commit()
        raise HTTPException(status_code=500, detail="Falha na importação; nenhuma alteração do lote foi mantida") from exc
