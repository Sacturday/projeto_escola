# Sistema de Controle de Frequência Escolar

FastAPI + Jinja2 + HTMX + SQLAlchemy assíncrono + PostgreSQL Neon.

## Perfis

`ADMIN`, `DIRETOR`, `PROFESSOR`.

- ADMIN: visão e gestão global da rede.
- DIRETOR: gestão da própria escola.
- PROFESSOR: somente turmas vinculadas e chamada do dia.

## Frequência

A chamada começa em estado visual **NEUTRO / NÃO LANÇADO**. NEUTRO não é salvo no banco. O professor precisa marcar todos os alunos como `PRESENTE` ou `FALTA` antes de confirmar. `FALTA_JUSTIFICADA` é reservado para correção administrativa.

## Desenvolvimento

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
alembic upgrade head
uvicorn app.main:app --reload
```

## Testes

Após instalar as dependências:

```bash
python tests_imports.py
python tests_regras.py
```

`tests_imports.py` descobre e testa todos os módulos Python. Ele não conecta ao Neon.

## Render + Neon

No Render configure `DATABASE_URL` apontando para o Neon, `SECRET_KEY`, `APP_ENV=production` e `APP_TIMEZONE=America/Sao_Paulo`.

O Build Command é:

```bash
pip install -r requirements.txt && alembic upgrade head
```

O Start Command é:

```bash
uvicorn app.main:app --host 0.0.0.0 --port $PORT
```

## Importação Excel

Somente ADMIN pode acessar `/admin/importacoes` e os endpoints `/api/admin/importacoes/*`.

São aceitos `.xls` e `.xlsx`; a confirmação só aceita o mesmo arquivo usado na prévia, verificado por SHA-256.

Veja `MODELOS_IMPORTACAO.md` e `DATABASE_NEON.md`.

## Matriz de compatibilidade Python

O projeto possui uma matriz de CI em `.github/workflows/python-matrix.yml` para Python **3.12, 3.13 e 3.14**.

Em cada versão, o CI executa:

```bash
python -m pip install -r requirements.txt
python -m pip check
python -m compileall -q .
python tests_imports.py
python tests_regras.py
```

A matriz testa as versões exatas de dependências atualmente fixadas em `requirements.txt`. Uma versão do Python só deve ser considerada aprovada para produção quando sua execução na matriz estiver verde.

Veja também `tests/compatibility_matrix.md`.
