from __future__ import annotations

from datetime import date, datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class StatusFrequencia(str, Enum):
    PRESENTE = "PRESENTE"
    FALTA = "FALTA"
    FALTA_JUSTIFICADA = "FALTA_JUSTIFICADA"


class StatusChamada(str, Enum):
    NEUTRO = "NEUTRO"
    PRESENTE = "PRESENTE"
    FALTA = "FALTA"
    FALTA_JUSTIFICADA = "FALTA_JUSTIFICADA"


class StatusLancamentoProfessor(str, Enum):
    PRESENTE = "PRESENTE"
    FALTA = "FALTA"


class Perfil(str, Enum):
    ADMIN = "ADMIN"
    DIRETOR = "DIRETOR"
    PROFESSOR = "PROFESSOR"


class FrequenciaLinha(BaseModel):
    aluno_id: int
    turma_id: int
    nome_aluno: str
    matricula: str
    data: date
    frequencia_id: int | None = None
    status: StatusChamada = StatusChamada.NEUTRO
    versao: int | None = None


class FrequenciaUpdate(BaseModel):
    status: StatusFrequencia
    versao: int = Field(ge=1)
    motivo: str | None = None


class FrequenciaResponse(BaseModel):
    id: int
    aluno_id: int
    turma_id: int
    data: date
    status: StatusFrequencia
    registrado_por: int
    updated_at: datetime
    versao: int

    model_config = ConfigDict(from_attributes=True)


class LancamentoFrequencia(BaseModel):
    aluno_id: int
    turma_id: int
    data: date
    status: StatusLancamentoProfessor
    frequencia_id: int | None = None
    versao: int | None = None


class ConfirmarFrequenciasRequest(BaseModel):
    lancamentos: list[LancamentoFrequencia] = Field(min_length=1, max_length=1000)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class CriarUsuario(BaseModel):
    username: str = Field(min_length=3, max_length=100)
    nome: str = Field(min_length=2, max_length=200)
    email: str | None = Field(default=None, max_length=320)
    senha: str = Field(min_length=8, max_length=128)
    perfil: Perfil
    escola_id: int | None = None


class CriarEscola(BaseModel):
    nome: str = Field(min_length=2, max_length=200)
    codigo: str = Field(min_length=1, max_length=50)


class CriarTurma(BaseModel):
    escola_id: int
    nome: str = Field(min_length=1, max_length=100)
    ano_letivo: int
    turno: str | None = Field(default=None, max_length=30)


class CriarAluno(BaseModel):
    escola_id: int
    matricula: str = Field(min_length=1, max_length=50)
    nome: str = Field(min_length=2, max_length=200)
    data_nascimento: date | None = None


class CriarMatricula(BaseModel):
    aluno_id: int
    turma_id: int
    ano_letivo: int
    data_inicio: date


class VincularProfessorTurma(BaseModel):
    professor_id: int
    turma_id: int


class TipoImportacao(str, Enum):
    ESCOLAS = "ESCOLAS"
    TURMAS = "TURMAS"
    ALUNOS = "ALUNOS"
    MATRICULAS = "MATRICULAS"
