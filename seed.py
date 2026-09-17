"""Bootstrap idempotente do ambiente inicial.

Uso local/Codespace apontando para o Neon:
    DATABASE_URL="postgresql+asyncpg://..." python seed.py

Cria:
- uma escola inicial;
- um ADMIN global;
- um DIRETOR da escola;
- um PROFESSOR;
- uma turma;
- alunos e matrículas;
- vínculo professor-turma.
"""

import asyncio
import os


from sqlalchemy import select

from app.database import AsyncSessionLocal
from app import models
from app.security import gerar_hash_senha


async def get_or_create(db, model, where, values):
    obj = (await db.execute(select(model).where(*where))).scalar_one_or_none()
    if obj is None:
        obj = model(**values)
        db.add(obj)
        await db.flush()
    return obj


async def seed():
    admin_password = os.getenv("BOOTSTRAP_ADMIN_PASSWORD")
    if not admin_password:
        raise RuntimeError("Defina BOOTSTRAP_ADMIN_PASSWORD para executar o seed")
    director_password = os.getenv("BOOTSTRAP_DIRECTOR_PASSWORD", admin_password)
    teacher_password = os.getenv("BOOTSTRAP_PROFESSOR_PASSWORD", admin_password)

    async with AsyncSessionLocal() as db:
        escola = await get_or_create(
            db,
            models.Escola,
            [models.Escola.codigo == "DEMO-01"],
            {"nome": "E.M. Albert Sabin", "codigo": "DEMO-01"},
        )

        await get_or_create(
            db,
            models.Usuario,
            [models.Usuario.username == "admin"],
            {
                "username": "admin",
                "nome": "Administrador Inicial",
                "email": "admin@example.local",
                "senha_hash": gerar_hash_senha(admin_password),
                "perfil": models.Perfil.ADMIN,
                "escola_id": None,
            },
        )

        diretor = await get_or_create(
            db,
            models.Usuario,
            [models.Usuario.username == "diretor1"],
            {
                "username": "diretor1",
                "nome": "Diretor(a) Teste",
                "email": "diretor1@example.local",
                "senha_hash": gerar_hash_senha(director_password),
                "perfil": models.Perfil.DIRETOR,
                "escola_id": escola.id,
            },
        )

        professor = await get_or_create(
            db,
            models.Usuario,
            [models.Usuario.username == "professor1"],
            {
                "username": "professor1",
                "nome": "Professor(a) Teste",
                "email": "professor1@example.local",
                "senha_hash": gerar_hash_senha(teacher_password),
                "perfil": models.Perfil.PROFESSOR,
                "escola_id": escola.id,
            },
        )

        turma = await get_or_create(
            db,
            models.Turma,
            [models.Turma.escola_id == escola.id, models.Turma.nome == "5º Ano A", models.Turma.ano_letivo == 2026],
            {"escola_id": escola.id, "nome": "5º Ano A", "ano_letivo": 2026, "turno": "Manhã"},
        )

        alunos = [
            ("20260001", "Lucas Silva Santos"),
            ("20260002", "Beatriz Souza Oliveira"),
            ("20260003", "Enzo Gabriel Costa"),
        ]
        for matricula, nome in alunos:
            aluno = await get_or_create(
                db,
                models.Aluno,
                [models.Aluno.escola_id == escola.id, models.Aluno.matricula == matricula],
                {"escola_id": escola.id, "matricula": matricula, "nome": nome},
            )
            await get_or_create(
                db,
                models.Matricula,
                [models.Matricula.aluno_id == aluno.id, models.Matricula.turma_id == turma.id, models.Matricula.ano_letivo == 2026],
                {
                    "aluno_id": aluno.id,
                    "turma_id": turma.id,
                    "ano_letivo": 2026,
                    "status": models.StatusMatricula.ATIVA,
                },
            )

        vinculo = (
            await db.execute(
                select(models.ProfessorTurma).where(
                    models.ProfessorTurma.professor_id == professor.id,
                    models.ProfessorTurma.turma_id == turma.id,
                )
            )
        ).scalar_one_or_none()
        if vinculo is None:
            db.add(models.ProfessorTurma(professor_id=professor.id, turma_id=turma.id))

        await db.commit()
        print("Seed concluído.")
        print("Seed concluído com as credenciais fornecidas pelas variáveis de ambiente.")
        print("Alunos começam NEUTROS: não há registro em frequencias até o lançamento.")


if __name__ == "__main__":
    asyncio.run(seed())
