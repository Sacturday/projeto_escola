from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from .. import models, schemas
from ..database import get_db
from ..dependencies import exigir_acesso_escola, exigir_perfil, get_current_user, get_current_user_pagina
from ..security import gerar_hash_senha

router = APIRouter(prefix="/api/admin", tags=["admin"])
pages = APIRouter(prefix="/admin", tags=["admin-pages"])
templates = Jinja2Templates(directory="app/templates")


def _integrity(exc: IntegrityError) -> HTTPException:
    return HTTPException(status_code=409, detail="Registro já existe ou viola uma regra de integridade")


@pages.get("")
async def pagina_admin(request: Request, db: AsyncSession = Depends(get_db), usuario: models.Usuario = Depends(get_current_user_pagina)):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    counts = {}
    for key, model in (("escolas", models.Escola), ("usuarios", models.Usuario), ("turmas", models.Turma), ("alunos", models.Aluno)):
        counts[key] = (await db.execute(select(func.count(model.id)).where(model.ativo.is_(True)))).scalar_one()
    return templates.TemplateResponse("admin.html", {"request": request, "usuario": usuario, "indicadores": counts})


@router.get("/escolas")
async def listar_escolas(db: AsyncSession = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    return (await db.execute(select(models.Escola).order_by(models.Escola.nome))).scalars().all()


@router.post("/escolas")
async def criar_escola(dados: schemas.CriarEscola, db: AsyncSession = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    escola = models.Escola(nome=dados.nome.strip(), codigo=dados.codigo.strip())
    db.add(escola)
    try:
        await db.commit(); await db.refresh(escola)
    except IntegrityError as exc:
        await db.rollback(); raise _integrity(exc) from exc
    return escola


@router.post("/turmas")
async def criar_turma(dados: schemas.CriarTurma, db: AsyncSession = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    escola = await db.get(models.Escola, dados.escola_id)
    if escola is None or not escola.ativo: raise HTTPException(404, "Escola não encontrada")
    obj = models.Turma(escola_id=dados.escola_id, nome=dados.nome.strip(), ano_letivo=dados.ano_letivo, turno=dados.turno)
    db.add(obj)
    try: await db.commit(); await db.refresh(obj)
    except IntegrityError as exc: await db.rollback(); raise _integrity(exc) from exc
    return obj


@router.post("/alunos")
async def criar_aluno(dados: schemas.CriarAluno, db: AsyncSession = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    if await db.get(models.Escola, dados.escola_id) is None: raise HTTPException(404, "Escola não encontrada")
    obj=models.Aluno(escola_id=dados.escola_id, matricula=dados.matricula.strip(), nome=dados.nome.strip(), data_nascimento=dados.data_nascimento)
    db.add(obj)
    try: await db.commit(); await db.refresh(obj)
    except IntegrityError as exc: await db.rollback(); raise _integrity(exc) from exc
    return obj


@router.post("/matriculas")
async def criar_matricula(dados: schemas.CriarMatricula, db: AsyncSession = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    aluno=await db.get(models.Aluno,dados.aluno_id); turma=await db.get(models.Turma,dados.turma_id)
    if aluno is None or turma is None: raise HTTPException(404,"Aluno ou turma não encontrada")
    if aluno.escola_id != turma.escola_id: raise HTTPException(422,"Aluno e turma devem pertencer à mesma escola")
    obj=models.Matricula(aluno_id=aluno.id,turma_id=turma.id,ano_letivo=dados.ano_letivo,data_inicio=dados.data_inicio,status=models.StatusMatricula.ATIVA)
    db.add(obj)
    try: await db.commit(); await db.refresh(obj)
    except IntegrityError as exc: await db.rollback(); raise _integrity(exc) from exc
    return obj


@router.post("/professor-turma")
async def vincular_professor_turma(dados: schemas.VincularProfessorTurma, db: AsyncSession = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    professor=await db.get(models.Usuario,dados.professor_id); turma=await db.get(models.Turma,dados.turma_id)
    if professor is None or turma is None: raise HTTPException(404,"Professor ou turma não encontrada")
    if professor.perfil != models.Perfil.PROFESSOR or professor.escola_id != turma.escola_id: raise HTTPException(422,"Professor e turma incompatíveis")
    db.add(models.ProfessorTurma(professor_id=professor.id,turma_id=turma.id))
    try: await db.commit()
    except IntegrityError as exc: await db.rollback(); raise _integrity(exc) from exc
    return {"status":"ok"}


@router.post("/usuarios")
async def criar_usuario(dados: schemas.CriarUsuario, db: AsyncSession = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    if dados.perfil == schemas.Perfil.ADMIN and dados.escola_id is not None:
        raise HTTPException(400, "ADMIN não pertence a uma escola específica")
    if dados.perfil != schemas.Perfil.ADMIN and dados.escola_id is None:
        raise HTTPException(400, "DIRETOR e PROFESSOR precisam de escola_id")
    if dados.escola_id is not None and await db.get(models.Escola, dados.escola_id) is None:
        raise HTTPException(404, "Escola não encontrada")
    novo=models.Usuario(username=dados.username.strip(),nome=dados.nome.strip(),email=dados.email,senha_hash=gerar_hash_senha(dados.senha),perfil=models.Perfil(dados.perfil.value),escola_id=dados.escola_id)
    db.add(novo)
    try: await db.commit(); await db.refresh(novo)
    except IntegrityError as exc: await db.rollback(); raise _integrity(exc) from exc
    return novo


@router.get("/usuarios")
async def listar_usuarios(db: AsyncSession = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    return (await db.execute(select(models.Usuario).order_by(models.Usuario.nome))).scalars().all()


@router.patch("/usuarios/{usuario_id}/ativo")
async def alterar_status_usuario(usuario_id: int, ativo: bool, db: AsyncSession = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    alvo = await db.get(models.Usuario, usuario_id)
    if alvo is None:
        raise HTTPException(404, "Usuário não encontrado")
    if alvo.id == usuario.id and not ativo:
        raise HTTPException(422, "O ADMIN atual não pode desativar a própria conta")
    alvo.ativo = ativo
    await db.commit()
    return {"id": alvo.id, "ativo": alvo.ativo}


@router.get("/turmas")
async def listar_turmas(db: AsyncSession = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    return (await db.execute(select(models.Turma).order_by(models.Turma.ano_letivo.desc(), models.Turma.nome))).scalars().all()


@router.patch("/turmas/{turma_id}/ativo")
async def alterar_status_turma(turma_id: int, ativo: bool, db: AsyncSession = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    alvo=await db.get(models.Turma,turma_id)
    if alvo is None: raise HTTPException(404,"Turma não encontrada")
    alvo.ativo=ativo; await db.commit(); return {"id":alvo.id,"ativo":alvo.ativo}


@router.get("/alunos")
async def listar_alunos(db: AsyncSession = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    return (await db.execute(select(models.Aluno).order_by(models.Aluno.nome))).scalars().all()


@router.patch("/alunos/{aluno_id}/ativo")
async def alterar_status_aluno(aluno_id: int, ativo: bool, db: AsyncSession = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    alvo=await db.get(models.Aluno,aluno_id)
    if alvo is None: raise HTTPException(404,"Aluno não encontrado")
    alvo.ativo=ativo; await db.commit(); return {"id":alvo.id,"ativo":alvo.ativo}


@pages.get("/importacoes")
async def pagina_importacoes(request: Request, usuario: models.Usuario = Depends(get_current_user_pagina)):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    return templates.TemplateResponse("importacoes.html", {"request": request, "usuario": usuario, "tipos": [t.value for t in models.TipoImportacao]})


@router.get("/importacoes")
async def historico_importacoes(db: AsyncSession = Depends(get_db), usuario: models.Usuario = Depends(get_current_user)):
    exigir_perfil(usuario, models.Perfil.ADMIN)
    resultado = await db.execute(select(models.Importacao).order_by(models.Importacao.created_at.desc()).limit(100))
    return [{"id":x.id,"usuario_id":x.usuario_id,"tipo":x.tipo.value,"status":x.status.value,"arquivo_nome":x.arquivo_nome,"arquivo_sha256":x.arquivo_sha256,"linhas_lidas":x.linhas_lidas,"linhas_importadas":x.linhas_importadas,"linhas_rejeitadas":x.linhas_rejeitadas,"resumo_erro":x.resumo_erro,"created_at":x.created_at,"finished_at":x.finished_at} for x in resultado.scalars().all()]
