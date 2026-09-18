"""Smoke tests de integridade dos módulos Python do projeto.

Uso:
    python tests_imports.py

O teste:
1. descobre os módulos Python normais do projeto;
2. compila os arquivos para detectar erros de sintaxe;
3. importa os módulos para detectar imports quebrados;
4. verifica símbolos críticos de app.security.

`migrations.env` é deliberadamente excluído da importação direta: ele é um
script executado dentro do contexto do Alembic e depende de
`alembic.context.config` existir durante a execução.
"""
from __future__ import annotations

import importlib
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXCLUDED_MODULES = {
    "migrations.env",
}


def discover_modules() -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
       if rel.as_posix() in {
            "tests_imports.py",
            "tests_regras.py",
            "tests_alembic.py",
        }:
            continue
        if "__pycache__" in rel.parts:
            continue

        parts = list(rel.parts)
        filename = parts.pop()
        stem = Path(filename).stem
        module = ".".join(parts) if stem == "__init__" else ".".join([*parts, stem])
        if module and module not in EXCLUDED_MODULES:
            found.append((module, path))
    return found


def main() -> int:
    modules = discover_modules()
    compile_failures: list[tuple[str, str]] = []
    import_failures: list[tuple[str, str]] = []

    for module, path in modules:
        try:
            py_compile.compile(str(path), doraise=True)
        except Exception as exc:  # noqa: BLE001
            compile_failures.append((module, f"{type(exc).__name__}: {exc}"))

    for module, _path in modules:
        if any(name == module for name, _ in compile_failures):
            continue
        try:
            importlib.import_module(module)
        except Exception as exc:  # noqa: BLE001
            import_failures.append((module, f"{type(exc).__name__}: {exc}"))

    symbol_failure = None
    try:
        from app.security import (
            criar_access_token,
            decodificar_token,
            gerar_hash_senha,
            verificar_senha,
        )

        for name, value in {
            "criar_access_token": criar_access_token,
            "decodificar_token": decodificar_token,
            "gerar_hash_senha": gerar_hash_senha,
            "verificar_senha": verificar_senha,
        }.items():
            if not callable(value):
                raise TypeError(f"{name} não é chamável")

        senha = "Teste-RC2-123!"
        hash_senha = gerar_hash_senha(senha)
        if not verificar_senha(senha, hash_senha):
            raise AssertionError("round-trip do hash de senha falhou")

        token = criar_access_token({"sub": "teste", "perfil": "PROFESSOR"})
        payload = decodificar_token(token)
        if not payload or payload.get("sub") != "teste":
            raise AssertionError("round-trip do JWT falhou")
    except Exception as exc:  # noqa: BLE001
        symbol_failure = f"{type(exc).__name__}: {exc}"

    print(f"Módulos descobertos: {len(modules)}")
    print(f"Arquivos compilados com sucesso: {len(modules) - len(compile_failures)}")
    print(f"Módulos importados com sucesso: {len(modules) - len(compile_failures) - len(import_failures)}")
    print(f"Excluído da importação direta: {', '.join(sorted(EXCLUDED_MODULES))}")

    if compile_failures:
        print("\nERROS DE COMPILAÇÃO:")
        for module, error in compile_failures:
            print(f"  - {module}: {error}")

    if import_failures:
        print("\nERROS DE IMPORTAÇÃO:")
        for module, error in import_failures:
            print(f"  - {module}: {error}")

    if symbol_failure:
        print(f"\nERRO EM app.security: {symbol_failure}")

    if compile_failures or import_failures or symbol_failure:
        print("\nRESULTADO: FALHA")
        return 1

    print("\nRESULTADO: OK — módulos normais compilados e importados.")
    print("OK — app.security e decodificar_token estão presentes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
