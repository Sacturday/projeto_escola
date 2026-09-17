"""Initial schema for school attendance system.

Revision ID: 0001_initial
Revises:
"""

from alembic import op
import sqlalchemy as sa

revision = "0001_initial"
down_revision = None
branch_labels = None
depends_on = None


status_frequencia = sa.Enum("PRESENTE", "FALTA", "FALTA_JUSTIFICADA", name="status_frequencia")
papel_usuario = sa.Enum("ADMIN", "DIRETOR", "PROFESSOR", name="papel_usuario")
status_matricula = sa.Enum("ATIVA", "ENCERRADA", "TRANSFERIDA", name="status_matricula")


def upgrade() -> None:
    bind = op.get_bind()
    papel_usuario.create(bind, checkfirst=True)
    status_matricula.create(bind, checkfirst=True)
    status_frequencia.create(bind, checkfirst=True)

    op.create_table(
        "escolas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.Column("codigo", sa.String(length=50), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("codigo", name="uq_escolas_codigo"),
    )

    op.create_table(
        "usuarios",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("escola_id", sa.Integer(), sa.ForeignKey("escolas.id", ondelete="RESTRICT"), nullable=True),
        sa.Column("username", sa.String(length=100), nullable=False),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=True),
        sa.Column("senha_hash", sa.Text(), nullable=False),
        sa.Column("perfil", papel_usuario, nullable=False),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("username", name="uq_usuarios_username"),
        sa.UniqueConstraint("email", name="uq_usuarios_email"),
        sa.CheckConstraint("(perfil = 'ADMIN' AND escola_id IS NULL) OR (perfil IN ('DIRETOR','PROFESSOR') AND escola_id IS NOT NULL)", name="ck_usuario_escola_por_papel"),
    )

    op.create_table(
        "turmas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("escola_id", sa.Integer(), sa.ForeignKey("escolas.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("nome", sa.String(length=100), nullable=False),
        sa.Column("ano_letivo", sa.Integer(), nullable=False),
        sa.Column("turno", sa.String(length=30), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("escola_id", "nome", "ano_letivo", name="uq_turmas_escola_nome_ano"),
    )

    op.create_table(
        "alunos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("escola_id", sa.Integer(), sa.ForeignKey("escolas.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("matricula", sa.String(length=50), nullable=False),
        sa.Column("nome", sa.String(length=200), nullable=False),
        sa.Column("data_nascimento", sa.Date(), nullable=True),
        sa.Column("ativo", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.UniqueConstraint("escola_id", "matricula", name="uq_alunos_escola_matricula"),
    )

    op.create_table(
        "matriculas",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("aluno_id", sa.Integer(), sa.ForeignKey("alunos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("turma_id", sa.Integer(), sa.ForeignKey("turmas.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("ano_letivo", sa.Integer(), nullable=False),
        sa.Column("data_inicio", sa.Date(), nullable=False, server_default=sa.text("CURRENT_DATE")),
        sa.Column("data_fim", sa.Date(), nullable=True),
        sa.Column("status", status_matricula, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("data_fim IS NULL OR data_fim >= data_inicio", name="ck_matriculas_periodo"),
        sa.UniqueConstraint("aluno_id", "turma_id", "ano_letivo", name="uq_matriculas_aluno_turma_ano"),
    )

    op.create_table(
        "professor_turma",
        sa.Column("professor_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("turma_id", sa.Integer(), sa.ForeignKey("turmas.id", ondelete="RESTRICT"), primary_key=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_table(
        "frequencias",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("aluno_id", sa.Integer(), sa.ForeignKey("alunos.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("turma_id", sa.Integer(), sa.ForeignKey("turmas.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("data", sa.Date(), nullable=False),
        sa.Column("status", status_frequencia, nullable=False),
        sa.Column("observacao", sa.Text(), nullable=True),
        sa.Column("registrado_por", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("versao", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.CheckConstraint("versao >= 1", name="ck_frequencia_versao_positiva"),
        sa.UniqueConstraint("aluno_id", "turma_id", "data", name="uq_frequencia_aluno_turma_data"),
    )

    op.create_table(
        "frequencia_auditoria",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("frequencia_id", sa.Integer(), sa.ForeignKey("frequencias.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("valor_anterior", status_frequencia, nullable=True),
        sa.Column("valor_novo", status_frequencia, nullable=False),
        sa.Column("motivo", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
    )

    op.create_index("ix_usuarios_escola_perfil", "usuarios", ["escola_id", "perfil"])
    op.create_index("ix_turmas_escola_ano", "turmas", ["escola_id", "ano_letivo"])
    op.create_index("ix_alunos_escola_ativo", "alunos", ["escola_id", "ativo"])
    op.create_index("ix_matriculas_turma_ano_status", "matriculas", ["turma_id", "ano_letivo", "status"])
    op.create_index("ix_matriculas_aluno_ano", "matriculas", ["aluno_id", "ano_letivo"])
    op.create_index("ix_professor_turma_turma", "professor_turma", ["turma_id"])
    op.create_index("ix_frequencias_turma_data", "frequencias", ["turma_id", "data"])
    op.create_index("ix_frequencias_aluno_data", "frequencias", ["aluno_id", "data"])
    op.create_index("ix_frequencia_auditoria_frequencia_data", "frequencia_auditoria", ["frequencia_id", "created_at"])

    op.execute("""
    CREATE OR REPLACE FUNCTION validar_professor_turma()
    RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE v_papel papel_usuario; v_escola_professor INTEGER; v_escola_turma INTEGER;
    BEGIN
      SELECT perfil, escola_id INTO v_papel, v_escola_professor FROM usuarios WHERE id = NEW.professor_id;
      SELECT escola_id INTO v_escola_turma FROM turmas WHERE id = NEW.turma_id;
      IF v_papel IS DISTINCT FROM 'PROFESSOR'::papel_usuario THEN
        RAISE EXCEPTION 'professor_id deve apontar para usuário PROFESSOR';
      END IF;
      IF v_escola_professor IS DISTINCT FROM v_escola_turma THEN
        RAISE EXCEPTION 'professor e turma devem pertencer à mesma escola';
      END IF;
      RETURN NEW;
    END; $$;
    """)
    op.execute("CREATE TRIGGER trg_validar_professor_turma BEFORE INSERT OR UPDATE ON professor_turma FOR EACH ROW EXECUTE FUNCTION validar_professor_turma();")

    op.execute("""
    CREATE OR REPLACE FUNCTION validar_frequencia_mesma_escola()
    RETURNS trigger LANGUAGE plpgsql AS $$
    DECLARE v_escola_aluno INTEGER; v_escola_turma INTEGER;
    BEGIN
      SELECT escola_id INTO v_escola_aluno FROM alunos WHERE id = NEW.aluno_id;
      SELECT escola_id INTO v_escola_turma FROM turmas WHERE id = NEW.turma_id;
      IF v_escola_aluno IS DISTINCT FROM v_escola_turma THEN
        RAISE EXCEPTION 'aluno e turma devem pertencer à mesma escola';
      END IF;
      IF NOT EXISTS (
        SELECT 1 FROM matriculas m
        WHERE m.aluno_id = NEW.aluno_id
          AND m.turma_id = NEW.turma_id
          AND m.data_inicio <= NEW.data
          AND (m.data_fim IS NULL OR m.data_fim >= NEW.data)
      ) THEN
        RAISE EXCEPTION 'aluno não possui matrícula válida na turma para a data da frequência';
      END IF;
      RETURN NEW;
    END; $$;
    """)
    op.execute("CREATE TRIGGER trg_validar_frequencia_integridade BEFORE INSERT OR UPDATE ON frequencias FOR EACH ROW EXECUTE FUNCTION validar_frequencia_mesma_escola();")


def downgrade() -> None:
    op.execute("DROP TRIGGER IF EXISTS trg_validar_frequencia_integridade ON frequencias")
    op.execute("DROP FUNCTION IF EXISTS validar_frequencia_mesma_escola()")
    op.execute("DROP TRIGGER IF EXISTS trg_validar_professor_turma ON professor_turma")
    op.execute("DROP FUNCTION IF EXISTS validar_professor_turma()")
    op.drop_index("ix_frequencia_auditoria_frequencia_data", table_name="frequencia_auditoria")
    op.drop_index("ix_frequencias_aluno_data", table_name="frequencias")
    op.drop_index("ix_frequencias_turma_data", table_name="frequencias")
    op.drop_index("ix_professor_turma_turma", table_name="professor_turma")
    op.drop_index("ix_matriculas_aluno_ano", table_name="matriculas")
    op.drop_index("ix_matriculas_turma_ano_status", table_name="matriculas")
    op.drop_index("ix_alunos_escola_ativo", table_name="alunos")
    op.drop_index("ix_turmas_escola_ano", table_name="turmas")
    op.drop_index("ix_usuarios_escola_perfil", table_name="usuarios")
    op.drop_table("frequencia_auditoria")
    op.drop_table("frequencias")
    op.drop_table("professor_turma")
    op.drop_table("matriculas")
    op.drop_table("alunos")
    op.drop_table("turmas")
    op.drop_table("usuarios")
    op.drop_table("escolas")
    bind = op.get_bind()
    status_frequencia.drop(bind, checkfirst=True)
    status_matricula.drop(bind, checkfirst=True)
    papel_usuario.drop(bind, checkfirst=True)
