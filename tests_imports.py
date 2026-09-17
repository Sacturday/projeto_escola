"""Smoke tests de integridade dos módulos Python do projeto.

Uso recomendado no Render/Codespace/ambiente local, após instalar requirements.txt:
    python tests_imports.py

O teste:
1. descobre todos os módulos Python do projeto (app/*, migrations/* e seed.py);
2. compila todos os arquivos para detectar erros de sintaxe;
3. importa todos os módulos para detectar imports quebrados;
4. verifica explicitamente símbolos críticos de app.security.

Observação: a etapa de importação requer as dependências de requirements.txt instaladas.
O teste NÃO conecta ao Neon e NÃO inicia o servidor.
"""
from __future__ import annotations

import importlib
import py_compile
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def discover_modules() -> list[tuple[str, Path]]:
    """Retorna (nome_importavel, arquivo) para todo .py do projeto, exceto este teste."""
    found: list[tuple[str, Path]] = []
    for path in sorted(ROOT.rglob("*.py")):
        rel = path.relative_to(ROOT)
        if rel.as_posix() == "tests_imports.py" or "__pycache__" in rel.parts:
            continue

        parts = list(rel.parts)
        filename = parts.pop()
        stem = Path(filename).stem

        if stem == "__init__":
            module = ".".join(parts) if parts else ""
        else:
            module = ".".join([*parts, stem])

        if module:
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
        from app.security import criar_access_token, decodificar_token, gerar_hash_senha, verificar_senha

        for name, value in {
            "criar_access_token": criar_access_token,
            "decodificar_token": decodificar_token,
            "gerar_hash_senha": gerar_hash_senha,
            "verificar_senha": verificar_senha,
        }.items():
            if not callable(value):
                raise TypeError(f"{name} não é chamável")
    except Exception as exc:  # noqa: BLE001
        symbol_failure = f"{type(exc).__name__}: {exc}"

    print(f"Módulos descobertos: {len(modules)}")
    print(f"Arquivos compilados com sucesso: {len(modules) - len(compile_failures)}")
    print(f"Módulos importados com sucesso: {len(modules) - len(compile_failures) - len(import_failures)}")

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

    print("\nRESULTADO: OK — todos os módulos foram compilados e importados.")
    print("OK — app.security e decodificar_token estão presentes.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
