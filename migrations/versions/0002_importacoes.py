from alembic import op
import sqlalchemy as sa

revision = "0002_importacoes"
down_revision = "0001_initial"
branch_labels = None
depends_on = None


def upgrade() -> None:
    tipo_importacao = sa.Enum("ESCOLAS", "TURMAS", "ALUNOS", "MATRICULAS", name="tipo_importacao")
    status_importacao = sa.Enum("PREVIA_VALIDADA", "CONCLUIDA", "FALHA", name="status_importacao")
    tipo_importacao.create(op.get_bind(), checkfirst=True)
    status_importacao.create(op.get_bind(), checkfirst=True)

    op.create_table(
        "importacoes",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("usuario_id", sa.Integer(), sa.ForeignKey("usuarios.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("tipo", tipo_importacao, nullable=False),
        sa.Column("status", status_importacao, nullable=False),
        sa.Column("arquivo_nome", sa.String(length=255), nullable=False),
        sa.Column("arquivo_sha256", sa.String(length=64), nullable=True),
        sa.Column("linhas_lidas", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("linhas_importadas", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("linhas_rejeitadas", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("resumo_erro", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.func.now()),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("ix_importacoes_usuario_id", "importacoes", ["usuario_id"])
    op.create_index("ix_importacoes_created_at", "importacoes", ["created_at"])


def downgrade() -> None:
    op.drop_index("ix_importacoes_created_at", table_name="importacoes")
    op.drop_index("ix_importacoes_usuario_id", table_name="importacoes")
    op.drop_table("importacoes")
    bind = op.get_bind()
    sa.Enum(name="status_importacao").drop(bind, checkfirst=True)
    sa.Enum(name="tipo_importacao").drop(bind, checkfirst=True)
