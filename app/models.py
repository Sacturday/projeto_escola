from __future__ import annotations
import enum
from datetime import date
from sqlalchemy import Boolean, Column, Date, DateTime, Enum as SAEnum, ForeignKey, Integer, String, Text, UniqueConstraint, func
from .database import Base

class StatusFrequencia(str, enum.Enum):
    PRESENTE = "PRESENTE"
    FALTA = "FALTA"
    FALTA_JUSTIFICADA = "FALTA_JUSTIFICADA"

class Perfil(str, enum.Enum):
    ADMIN = "ADMIN"
    DIRETOR = "DIRETOR"
    PROFESSOR = "PROFESSOR"

class StatusMatricula(str, enum.Enum):
    ATIVA = "ATIVA"
    ENCERRADA = "ENCERRADA"
    TRANSFERIDA = "TRANSFERIDA"

class Escola(Base):
    __tablename__ = "escolas"
    id = Column(Integer, primary_key=True)
    nome = Column(String(200), nullable=False)
    codigo = Column(String(50), unique=True, nullable=False)
    ativo = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    escola_id = Column(Integer, ForeignKey("escolas.id", ondelete="RESTRICT"), nullable=True)
    username = Column(String(100), unique=True, nullable=False)
    nome = Column(String(200), nullable=False)
    email = Column(String(320), unique=True, nullable=True)
    senha_hash = Column(Text, nullable=False)
    perfil = Column(SAEnum(Perfil, name="papel_usuario", native_enum=True), nullable=False)
    ativo = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())

class Turma(Base):
    __tablename__ = "turmas"
    id = Column(Integer, primary_key=True)
    escola_id = Column(Integer, ForeignKey("escolas.id", ondelete="RESTRICT"), nullable=False, index=True)
    nome = Column(String(100), nullable=False)
    ano_letivo = Column(Integer, nullable=False)
    turno = Column(String(30), nullable=True)
    ativo = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    __table_args__ = (UniqueConstraint("escola_id", "nome", "ano_letivo", name="uq_turmas_escola_nome_ano"),)

class Aluno(Base):
    __tablename__ = "alunos"
    id = Column(Integer, primary_key=True)
    escola_id = Column(Integer, ForeignKey("escolas.id", ondelete="RESTRICT"), nullable=False, index=True)
    matricula = Column(String(50), nullable=False)
    nome = Column(String(200), nullable=False)
    data_nascimento = Column(Date, nullable=True)
    ativo = Column(Boolean, nullable=False, default=True, server_default="true")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    __table_args__ = (UniqueConstraint("escola_id", "matricula", name="uq_alunos_escola_matricula"),)

class Matricula(Base):
    __tablename__ = "matriculas"
    id = Column(Integer, primary_key=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id", ondelete="RESTRICT"), nullable=False, index=True)
    turma_id = Column(Integer, ForeignKey("turmas.id", ondelete="RESTRICT"), nullable=False, index=True)
    ano_letivo = Column(Integer, nullable=False)
    data_inicio = Column(Date, nullable=False, default=date.today, server_default=func.current_date())
    data_fim = Column(Date, nullable=True)
    status = Column(SAEnum(StatusMatricula, name="status_matricula", native_enum=True), nullable=False, default=StatusMatricula.ATIVA)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    __table_args__ = (UniqueConstraint("aluno_id", "turma_id", "ano_letivo", name="uq_matriculas_aluno_turma_ano"),)

class ProfessorTurma(Base):
    __tablename__ = "professor_turma"
    professor_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), primary_key=True)
    turma_id = Column(Integer, ForeignKey("turmas.id", ondelete="RESTRICT"), primary_key=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

class Frequencia(Base):
    __tablename__ = "frequencias"
    id = Column(Integer, primary_key=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id", ondelete="RESTRICT"), nullable=False, index=True)
    turma_id = Column(Integer, ForeignKey("turmas.id", ondelete="RESTRICT"), nullable=False, index=True)
    data = Column(Date, nullable=False, index=True)
    status = Column(SAEnum(StatusFrequencia, name="status_frequencia", native_enum=True), nullable=False)
    observacao = Column(Text, nullable=True)
    registrado_por = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    versao = Column(Integer, nullable=False, default=1, server_default="1")
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now())
    __table_args__ = (UniqueConstraint("aluno_id", "turma_id", "data", name="uq_frequencia_aluno_turma_data"),)

class FrequenciaAuditoria(Base):
    __tablename__ = "frequencia_auditoria"
    id = Column(Integer, primary_key=True)
    frequencia_id = Column(Integer, ForeignKey("frequencias.id", ondelete="RESTRICT"), nullable=False, index=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False)
    valor_anterior = Column(SAEnum(StatusFrequencia, name="status_frequencia", native_enum=True), nullable=True)
    valor_novo = Column(SAEnum(StatusFrequencia, name="status_frequencia", native_enum=True), nullable=False)
    motivo = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())

class ImportacaoStatus(str, enum.Enum):
    PREVIA_VALIDADA = "PREVIA_VALIDADA"
    CONCLUIDA = "CONCLUIDA"
    FALHA = "FALHA"

class TipoImportacao(str, enum.Enum):
    ESCOLAS = "ESCOLAS"
    TURMAS = "TURMAS"
    ALUNOS = "ALUNOS"
    MATRICULAS = "MATRICULAS"

class Importacao(Base):
    __tablename__ = "importacoes"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False, index=True)
    tipo = Column(SAEnum(TipoImportacao, name="tipo_importacao", native_enum=True), nullable=False)
    status = Column(SAEnum(ImportacaoStatus, name="status_importacao", native_enum=True), nullable=False)
    arquivo_nome = Column(String(255), nullable=False)
    arquivo_sha256 = Column(String(64), nullable=False, index=True)
    linhas_lidas = Column(Integer, nullable=False, default=0, server_default="0")
    linhas_importadas = Column(Integer, nullable=False, default=0, server_default="0")
    linhas_rejeitadas = Column(Integer, nullable=False, default=0, server_default="0")
    resumo_erro = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), nullable=False, server_default=func.now())
    finished_at = Column(DateTime(timezone=True), nullable=True)
