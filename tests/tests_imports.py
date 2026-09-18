"""Testes de integridade dos módulos Python do projeto."""
from __future__ import annotations

import importlib
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

EXCLUDED_MODULES = {
    "migrations.env",
}


def discover_modules() -> list[tuple[str, Path]]:
    found: list[tuple[str, Path]] = []

    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)

        # A pasta tests contém somente testes e não faz parte
        # dos módulos normais da aplicação.
        if "tests" in rel.parts:
            continue

        # Arquivos de cache do Python não devem ser testados.
        if "__pycache__" in rel.parts:
            continue

        parts = list(rel.parts)
        filename = parts.pop()

        stem = Path(filename).stem

        if stem == "__init__":
            module = ".".join(parts)
        else:
            module = ".".join([*parts, stem])

        if module and module not in EXCLUDED_MODULES:
            found.append((module, path))

    return found


def test_security_symbols() -> None:
    from app.security import (
        criar_access_token,
        decodificar_token,
        gerar_hash_senha,
        verificar_senha,
    )

    functions = {
        "criar_access_token": criar_access_token,
        "decodificar_token": decodificar_token,
        "gerar_hash_senha": gerar_hash_senha,
        "verificar_senha": verificar_senha,
    }

    for name, value in functions.items():
        if not callable(value):
            raise TypeError(f"{name} não é chamável")

    senha = "Teste-RC2-123!"
    senha_hash = gerar_hash_senha(senha)

    if not verificar_senha(senha, senha_hash):
        raise AssertionError("Round-trip do hash de senha falhou")

    token = criar_access_token(
        {
            "sub": "teste",
            "perfil": "PROFESSOR",
        }
    )

    payload = decodificar_token(token)

    if not payload or payload.get("sub") != "teste":
        raise AssertionError("Round-trip do JWT falhou")


def main() -> int:
    modules = discover_modules()

    compile_failures: list[tuple[str, str]] = []
    import_failures: list[tuple[str, str]] = []

    for module, path in modules:
        try:
            py_compile.compile(
                str(path),
                doraise=True,
            )
        except Exception as exc:
            compile_failures.append(
                (
                    module,
                    f"{type(exc).__name__}: {exc}",
                )
            )

    for module, _path in modules:
        if any(
            name == module
            for name, _error in compile_failures
        ):
            continue

        try:
            importlib.import_module(module)
        except Exception as exc:
            import_failures.append(
                (
                    module,
                    f"{type(exc).__name__}: {exc}",
                )
            )

    security_error = None

    try:
        test_security_symbols()
    except Exception as exc:
        security_error = (
            f"{type(exc).__name__}: {exc}"
        )

    print(f"Módulos descobertos: {len(modules)}")
    print(
        "Arquivos compilados com sucesso: "
        f"{len(modules) - len(compile_failures)}"
    )
    print(
        "Módulos importados com sucesso: "
        f"{len(modules) - len(compile_failures) - len(import_failures)}"
    )
    print(
        "Excluído da importação direta: "
        f"{', '.join(sorted(EXCLUDED_MODULES))}"
    )

    if compile_failures:
        print("\nERROS DE COMPILAÇÃO:")

        for module, error in compile_failures:
            print(f"  - {module}: {error}")

    if import_failures:
        print("\nERROS DE IMPORTAÇÃO:")

        for module, error in import_failures:
            print(f"  - {module}: {error}")

    if security_error:
        print(
            f"\nERRO EM app.security: {security_error}"
        )

    if (
        compile_failures
        or import_failures
        or security_error
    ):
        print("\nRESULTADO: FALHA")
        return 1

    print(
        "\nRESULTADO: OK — módulos normais "
        "compilados e importados."
    )
    print(
        "OK — app.security e decodificar_token "
        "estão presentes."
    )

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
