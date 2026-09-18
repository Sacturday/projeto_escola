from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]

if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.database import Base
from app import models


def test_tabelas_principais_existentes():
    esperadas = {
        "escolas",
        "usuarios",
        "turmas",
        "alunos",
        "matriculas",
        "professor_turma",
        "frequencias",
        "frequencia_auditoria",
        "importacoes",
    }

    encontradas = set(Base.metadata.tables)

    assert esperadas.issubset(encontradas)


def test_frequencia_tem_unicidade_aluno_turma_data():
    tabela = models.Frequencia.__table__

    nomes = {
        constraint.name
        for constraint in tabela.constraints
        if constraint.name
    }

    assert "uq_frequencia_aluno_turma_data" in nomes


def test_aluno_tem_matricula_unica_por_escola():
    tabela = models.Aluno.__table__

    nomes = {
        constraint.name
        for constraint in tabela.constraints
        if constraint.name
    }

    assert "uq_alunos_escola_matricula" in nomes


def test_professor_turma_e_chave_composta():
    tabela = models.ProfessorTurma.__table__

    colunas_pk = {
        coluna.name
        for coluna in tabela.primary_key.columns
    }

    assert colunas_pk == {"professor_id", "turma_id"}


def test_frequencia_nao_tem_status_neutro_no_banco():
    valores = {
        status.value
        for status in models.StatusFrequencia
    }

    assert "PRESENTE" in valores
    assert "FALTA" in valores
    assert "FALTA_JUSTIFICADA" in valores
    assert "NEUTRO" not in valores


if __name__ == "__main__":
    test_tabelas_principais_existentes()
    test_frequencia_tem_unicidade_aluno_turma_data()
    test_aluno_tem_matricula_unica_por_escola()
    test_professor_turma_e_chave_composta()
    test_frequencia_nao_tem_status_neutro_no_banco()

    print("RESULTADO: OK — modelos SQLAlchemy validados.")
