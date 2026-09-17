"""Hardening: school codes, import hash and timestamp triggers."""
from alembic import op
import sqlalchemy as sa

revision = "0003_hardening"
down_revision = "0002_importacoes"
branch_labels = None
depends_on = None


def upgrade() -> None:
    bind = op.get_bind()
    null_codes = bind.execute(sa.text("SELECT COUNT(*) FROM escolas WHERE codigo IS NULL")).scalar_one()
    if null_codes:
        raise RuntimeError("Existem escolas sem CODIGO. Corrija os dados antes de aplicar 0003_hardening.")
    op.alter_column("escolas", "codigo", existing_type=sa.String(length=50), nullable=False)
    columns = {row["column_name"] for row in bind.execute(sa.text("SELECT column_name FROM information_schema.columns WHERE table_name = 'importacoes'")).mappings()}
    if "arquivo_sha256" not in columns:
        op.add_column("importacoes", sa.Column("arquivo_sha256", sa.String(length=64), nullable=True))
    op.execute("UPDATE importacoes SET arquivo_sha256 = repeat('0', 64) WHERE arquivo_sha256 IS NULL")
    op.alter_column("importacoes", "arquivo_sha256", existing_type=sa.String(length=64), nullable=False)
    op.create_index("ix_importacoes_arquivo_sha256", "importacoes", ["arquivo_sha256"])
    op.execute("""
    CREATE OR REPLACE FUNCTION atualizar_updated_at()
    RETURNS trigger LANGUAGE plpgsql AS $$
    BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$;
    """)
    for table in ("escolas", "usuarios", "turmas", "alunos", "matriculas", "frequencias"):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")
        op.execute(f"CREATE TRIGGER trg_{table}_updated_at BEFORE UPDATE ON {table} FOR EACH ROW EXECUTE FUNCTION atualizar_updated_at()")


def downgrade() -> None:
    for table in ("escolas", "usuarios", "turmas", "alunos", "matriculas", "frequencias"):
        op.execute(f"DROP TRIGGER IF EXISTS trg_{table}_updated_at ON {table}")
    op.execute("DROP FUNCTION IF EXISTS atualizar_updated_at()")
    op.drop_index("ix_importacoes_arquivo_sha256", table_name="importacoes")
    op.drop_column("importacoes", "arquivo_sha256")
    op.alter_column("escolas", "codigo", existing_type=sa.String(length=50), nullable=True)
