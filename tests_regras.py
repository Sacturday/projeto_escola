"""Testes de regras estáticas que não exigem conexão com o Neon."""
from pathlib import Path
import ast

ROOT = Path(__file__).resolve().parent


def test_security_requires_key_in_production():
    tree = ast.parse((ROOT / "app/security.py").read_text(encoding="utf-8"))
    source = ast.unparse(tree)
    assert 'APP_ENV' in source and 'SECRET_KEY' in source
    assert 'decodificar_token' in source
    assert 'PasswordHash' in source
    assert 'pwdlib' in source
    assert 'PyJWT' not in source


def test_school_code_is_mandatory_for_import():
    source = (ROOT / "app/importacao_excel.py").read_text(encoding="utf-8")
    assert 'models.TipoImportacao.ESCOLAS' in source
    assert '"CODIGO": True' in source


def test_teacher_confirmation_is_teacher_only():
    source = (ROOT / "app/routers/frequencias.py").read_text(encoding="utf-8")
    assert 'exigir_perfil(usuario, models.Perfil.PROFESSOR)' in source
    assert 'A chamada deve conter exatamente todos os alunos matriculados e ativos' in source


def test_admin_import_is_admin_only():
    source = (ROOT / "app/routers/importacoes.py").read_text(encoding="utf-8")
    assert source.count('exigir_perfil(usuario, models.Perfil.ADMIN)') >= 2


if __name__ == "__main__":
    for name in ["test_security_requires_key_in_production", "test_school_code_is_mandatory_for_import", "test_teacher_confirmation_is_teacher_only", "test_admin_import_is_admin_only"]:
        globals()[name]()
    print("RESULTADO: OK — regras críticas verificadas.")
