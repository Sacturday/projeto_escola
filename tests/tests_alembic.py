"""Validação da configuração do Alembic sem conexão com o banco."""
from __future__ import annotations

from pathlib import Path

from alembic.config import Config
from alembic.script import ScriptDirectory


ROOT = Path(__file__).resolve().parent


def validar_env_async() -> None:
    env_path = ROOT / "migrations" / "env.py"

    if not env_path.exists():
        raise AssertionError("migrations/env.py não encontrado")

    source = env_path.read_text(encoding="utf-8")

    obrigatorios = [
        "async_engine_from_config",
        "asyncio.run",
        "run_async_migrations",
        "run_sync",
        "DATABASE_URL",
    ]

    for trecho in obrigatorios:
        if trecho not in source:
            raise AssertionError(
                f"migrations/env.py não contém o componente esperado: {trecho}"
            )

    if "psycopg2" in source:
        raise AssertionError(
            "migrations/env.py ainda contém referência a psycopg2; "
            "o projeto deve utilizar asyncpg."
        )


def main() -> int:
    config_path = ROOT / "alembic.ini"

    if not config_path.exists():
        raise AssertionError("alembic.ini não encontrado")

    validar_env_async()

    config = Config(str(config_path))
    script = ScriptDirectory.from_config(config)

    revisions = list(script.walk_revisions())

    if not revisions:
        raise AssertionError("Nenhuma migration encontrada")

    heads = script.get_heads()

    if len(heads) != 1:
        raise AssertionError(
            f"Esperado exatamente um head Alembic; encontrados: {heads}"
        )

    print(
        f"Alembic: OK — {len(revisions)} revisions; head={heads[0]}"
    )
    print("Alembic asyncpg: OK — configuração assíncrona encontrada.")
    print("Alembic: OK — nenhuma referência a psycopg2.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
