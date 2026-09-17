-- PostgreSQL / Neon — schema inicial do Sistema de Controle de Frequência Escolar
-- IMPORTANTE: NEUTRO NÃO É ARMAZENADO. Ausência de linha em frequencias = NEUTRO/não lançado.

BEGIN;

CREATE TYPE papel_usuario AS ENUM ('ADMIN', 'DIRETOR', 'PROFESSOR');
CREATE TYPE status_frequencia AS ENUM ('PRESENTE', 'FALTA', 'FALTA_JUSTIFICADA');
CREATE TYPE status_matricula AS ENUM ('ATIVA', 'ENCERRADA', 'TRANSFERIDA');
CREATE TYPE tipo_importacao AS ENUM ('ESCOLAS', 'TURMAS', 'ALUNOS', 'MATRICULAS');
CREATE TYPE status_importacao AS ENUM ('PREVIA_VALIDADA', 'CONCLUIDA', 'FALHA');

CREATE TABLE escolas (
    id SERIAL PRIMARY KEY,
    nome VARCHAR(200) NOT NULL,
    codigo VARCHAR(50) UNIQUE NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE usuarios (
    id SERIAL PRIMARY KEY,
    escola_id INTEGER REFERENCES escolas(id) ON DELETE RESTRICT,
    username VARCHAR(100) NOT NULL UNIQUE,
    nome VARCHAR(200) NOT NULL,
    email VARCHAR(320) UNIQUE,
    senha_hash TEXT NOT NULL,
    perfil papel_usuario NOT NULL,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_usuario_escola_por_papel CHECK (
        (perfil = 'ADMIN' AND escola_id IS NULL)
        OR (perfil IN ('DIRETOR', 'PROFESSOR') AND escola_id IS NOT NULL)
    )
);

CREATE TABLE turmas (
    id SERIAL PRIMARY KEY,
    escola_id INTEGER NOT NULL REFERENCES escolas(id) ON DELETE RESTRICT,
    nome VARCHAR(100) NOT NULL,
    ano_letivo INTEGER NOT NULL,
    turno VARCHAR(30),
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_turmas_escola_nome_ano UNIQUE (escola_id, nome, ano_letivo)
);

CREATE TABLE alunos (
    id SERIAL PRIMARY KEY,
    escola_id INTEGER NOT NULL REFERENCES escolas(id) ON DELETE RESTRICT,
    matricula VARCHAR(50) NOT NULL,
    nome VARCHAR(200) NOT NULL,
    data_nascimento DATE,
    ativo BOOLEAN NOT NULL DEFAULT TRUE,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT uq_alunos_escola_matricula UNIQUE (escola_id, matricula)
);

CREATE TABLE matriculas (
    id SERIAL PRIMARY KEY,
    aluno_id INTEGER NOT NULL REFERENCES alunos(id) ON DELETE RESTRICT,
    turma_id INTEGER NOT NULL REFERENCES turmas(id) ON DELETE RESTRICT,
    ano_letivo INTEGER NOT NULL,
    data_inicio DATE NOT NULL DEFAULT CURRENT_DATE,
    data_fim DATE,
    status status_matricula NOT NULL DEFAULT 'ATIVA',
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_matriculas_periodo CHECK (data_fim IS NULL OR data_fim >= data_inicio),
    CONSTRAINT uq_matriculas_aluno_turma_ano UNIQUE (aluno_id, turma_id, ano_letivo)
);

CREATE TABLE professor_turma (
    professor_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    turma_id INTEGER NOT NULL REFERENCES turmas(id) ON DELETE RESTRICT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    PRIMARY KEY (professor_id, turma_id)
);

CREATE TABLE frequencias (
    id SERIAL PRIMARY KEY,
    aluno_id INTEGER NOT NULL REFERENCES alunos(id) ON DELETE RESTRICT,
    turma_id INTEGER NOT NULL REFERENCES turmas(id) ON DELETE RESTRICT,
    data DATE NOT NULL,
    status status_frequencia NOT NULL,
    observacao TEXT,
    registrado_por INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    versao INTEGER NOT NULL DEFAULT 1,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    CONSTRAINT ck_frequencia_versao_positiva CHECK (versao >= 1),
    CONSTRAINT uq_frequencia_aluno_turma_data UNIQUE (aluno_id, turma_id, data)
);

CREATE TABLE frequencia_auditoria (
    id SERIAL PRIMARY KEY,
    frequencia_id INTEGER NOT NULL REFERENCES frequencias(id) ON DELETE RESTRICT,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    valor_anterior status_frequencia,
    valor_novo status_frequencia NOT NULL,
    motivo TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE TABLE importacoes (
    id SERIAL PRIMARY KEY,
    usuario_id INTEGER NOT NULL REFERENCES usuarios(id) ON DELETE RESTRICT,
    tipo tipo_importacao NOT NULL,
    status status_importacao NOT NULL,
    arquivo_nome VARCHAR(255) NOT NULL,
    arquivo_sha256 VARCHAR(64) NOT NULL,
    linhas_lidas INTEGER NOT NULL DEFAULT 0,
    linhas_importadas INTEGER NOT NULL DEFAULT 0,
    linhas_rejeitadas INTEGER NOT NULL DEFAULT 0,
    resumo_erro TEXT,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    finished_at TIMESTAMPTZ
);

CREATE INDEX ix_importacoes_usuario_id ON importacoes (usuario_id);
CREATE INDEX ix_importacoes_created_at ON importacoes (created_at);
CREATE INDEX ix_importacoes_arquivo_sha256 ON importacoes (arquivo_sha256);

CREATE INDEX ix_usuarios_escola_perfil ON usuarios (escola_id, perfil);
CREATE INDEX ix_turmas_escola_ano ON turmas (escola_id, ano_letivo);
CREATE INDEX ix_alunos_escola_ativo ON alunos (escola_id, ativo);
CREATE INDEX ix_matriculas_turma_ano_status ON matriculas (turma_id, ano_letivo, status);
CREATE INDEX ix_matriculas_aluno_ano ON matriculas (aluno_id, ano_letivo);
CREATE INDEX ix_professor_turma_turma ON professor_turma (turma_id);
CREATE INDEX ix_frequencias_turma_data ON frequencias (turma_id, data);
CREATE INDEX ix_frequencias_aluno_data ON frequencias (aluno_id, data);
CREATE INDEX ix_frequencia_auditoria_frequencia_data ON frequencia_auditoria (frequencia_id, created_at);

CREATE OR REPLACE FUNCTION validar_professor_turma()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_papel papel_usuario;
    v_escola_professor INTEGER;
    v_escola_turma INTEGER;
BEGIN
    SELECT perfil, escola_id INTO v_papel, v_escola_professor FROM usuarios WHERE id = NEW.professor_id;
    SELECT escola_id INTO v_escola_turma FROM turmas WHERE id = NEW.turma_id;

    IF v_papel IS DISTINCT FROM 'PROFESSOR'::papel_usuario THEN
        RAISE EXCEPTION 'professor_id deve apontar para usuário PROFESSOR';
    END IF;
    IF v_escola_professor IS DISTINCT FROM v_escola_turma THEN
        RAISE EXCEPTION 'professor e turma devem pertencer à mesma escola';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validar_professor_turma
BEFORE INSERT OR UPDATE ON professor_turma
FOR EACH ROW EXECUTE FUNCTION validar_professor_turma();

CREATE OR REPLACE FUNCTION validar_frequencia_integridade()
RETURNS trigger LANGUAGE plpgsql AS $$
DECLARE
    v_escola_aluno INTEGER;
    v_escola_turma INTEGER;
BEGIN
    SELECT escola_id INTO v_escola_aluno FROM alunos WHERE id = NEW.aluno_id;
    SELECT escola_id INTO v_escola_turma FROM turmas WHERE id = NEW.turma_id;

    IF v_escola_aluno IS DISTINCT FROM v_escola_turma THEN
        RAISE EXCEPTION 'aluno e turma devem pertencer à mesma escola';
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM matriculas m
        WHERE m.aluno_id = NEW.aluno_id
          AND m.turma_id = NEW.turma_id
          AND m.data_inicio <= NEW.data
          AND (m.data_fim IS NULL OR m.data_fim >= NEW.data)
    ) THEN
        RAISE EXCEPTION 'aluno não possui matrícula válida na turma para a data da frequência';
    END IF;
    RETURN NEW;
END;
$$;

CREATE TRIGGER trg_validar_frequencia_integridade
BEFORE INSERT OR UPDATE ON frequencias
FOR EACH ROW EXECUTE FUNCTION validar_frequencia_integridade();

COMMIT;


CREATE OR REPLACE FUNCTION atualizar_updated_at()
RETURNS trigger LANGUAGE plpgsql AS $$
BEGIN NEW.updated_at = NOW(); RETURN NEW; END; $$;

DO $$
DECLARE t text;
BEGIN
  FOREACH t IN ARRAY ARRAY['escolas','usuarios','turmas','alunos','matriculas','frequencias'] LOOP
    EXECUTE format('DROP TRIGGER IF EXISTS trg_%s_updated_at ON %I', t, t);
    EXECUTE format('CREATE TRIGGER trg_%s_updated_at BEFORE UPDATE ON %I FOR EACH ROW EXECUTE FUNCTION atualizar_updated_at()', t, t);
  END LOOP;
END $$;
