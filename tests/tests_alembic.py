"""Validação da configuração do Alembic sem conexão com o banco."""
from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


ROOT = Path(__file__).resolve().parents[1]


def main() -> int:
    config_path = ROOT / "alembic.ini"

    if not config_path.exists():
        raise AssertionError(
            "alembic.ini não encontrado"
        )

    env_path = ROOT / "migrations" / "env.py"

    if not env_path.exists():
        raise AssertionError(
            "migrations/env.py não encontrado"
        )

    env_source = env_path.read_text(
        encoding="utf-8"
    )

    required = [
        "async_engine_from_config",
        "run_async_migrations",
        "asyncio.run",
        "run_sync",
        "DATABASE_URL",
    ]

    for item in required:
        if item not in env_source:
            raise AssertionError(
                f"migrations/env.py não contém: {item}"
            )

    if "psycopg2" in env_source:
        raise AssertionError(
            "migrations/env.py contém referência "
            "a psycopg2."
        )

    config = Config(str(config_path))

    script = ScriptDirectory.from_config(config)

    revisions = list(
        script.walk_revisions()
    )

    if not revisions:
        raise AssertionError(
            "Nenhuma migration encontrada"
        )

    heads = script.get_heads()

    if len(heads) != 1:
        raise AssertionError(
            "Esperado exatamente um head Alembic; "
            f"encontrados: {heads}"
        )

    print(
        "Alembic: OK — "
        f"{len(revisions)} revisions; "
        f"head={heads[0]}"
    )

    print(
        "Alembic asyncpg: configuração "
        "assíncrona encontrada."
    )

    print(
        "Alembic: nenhuma referência a psycopg2."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
