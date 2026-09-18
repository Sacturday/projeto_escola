"""Validação da configuração do Alembic sem conexão com o Neon."""
from pathlib import Path
from alembic.config import Config
from alembic.script import ScriptDirectory

ROOT = Path(__file__).resolve().parent


def main() -> int:
    config_path = ROOT / "alembic.ini"
    if not config_path.exists():
        raise AssertionError("alembic.ini não encontrado")

    config = Config(str(config_path))
    script = ScriptDirectory.from_config(config)
    revisions = list(script.walk_revisions())
    if not revisions:
        raise AssertionError("Nenhuma migration encontrada")

    heads = script.get_heads()
    if len(heads) != 1:
        raise AssertionError(f"Esperado exatamente um head Alembic; encontrados: {heads}")

    print(f"Alembic: OK — {len(revisions)} revisions; head={heads[0]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
