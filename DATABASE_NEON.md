# DATABASE_NEON — Sistema de Frequência Escolar

## Arquitetura

```text
GitHub -> Render (FastAPI) -> Neon PostgreSQL
                     |
                     +-> WebSocket por escola
```

O Render não hospeda o PostgreSQL. O `DATABASE_URL` do Render aponta para o endpoint pooled do Neon.

## Perfis

- **ADMIN:** rede inteira; cadastro, importações, usuários, escolas e correções.
- **DIRETOR:** apenas a escola do usuário; consulta e gestão operacional local.
- **PROFESSOR:** somente turmas vinculadas; lançamento da chamada do dia.

## Entidades

`escolas`, `usuarios`, `turmas`, `alunos`, `matriculas`, `professor_turma`, `frequencias`, `frequencia_auditoria`, `importacoes`.

`escolas.codigo` é obrigatório porque é a chave funcional usada pelos arquivos de importação dependentes.

## Regra de frequência

`NEUTRO` não é valor armazenado no banco. Quando não existe linha em `frequencias` para aluno/turma/data, a interface apresenta **NEUTRO / NÃO LANÇADO**.

O professor deve marcar explicitamente `PRESENTE` ou `FALTA` para todos os alunos ativos e matriculados antes da confirmação. A API repete essa regra no backend.

`FALTA_JUSTIFICADA` é usada em correções administrativas por ADMIN/DIRETOR.

## Integridade

- Unicidade de matrícula por escola.
- Unicidade de turma por escola + nome + ano letivo.
- Unicidade de frequência por aluno + turma + data.
- Professor só pode ser vinculado a turma da mesma escola.
- Frequência exige aluno e turma da mesma escola e matrícula válida na data.
- `updated_at` é atualizado por trigger PostgreSQL.

## Migrações

```bash
alembic upgrade head
```

As revisões atuais são `0001_initial`, `0002_importacoes` e `0003_hardening`.

## Importação Excel — somente ADMIN

Tipos aceitos:

- ESCOLAS: `NOME`, `CODIGO`
- TURMAS: `ESCOLA_CODIGO`, `NOME`, `ANO_LETIVO`, `TURNO`
- ALUNOS: `ESCOLA_CODIGO`, `MATRICULA`, `NOME`, `DATA_NASCIMENTO`
- MATRICULAS: `ESCOLA_CODIGO`, `MATRICULA`, `TURMA_NOME`, `ANO_LETIVO`, `DATA_INICIO`, `DATA_FIM`

Fluxo:

```text
arquivo -> validação -> preview_id + SHA-256 -> confirmação -> transação -> histórico
```

Limites: 10 MB, 50.000 linhas e 64 colunas. Cabeçalhos duplicados ou relações inexistentes são rejeitados.

O usuário nunca precisa acessar o painel do Neon para importar dados.

## Segurança

Em produção:

```env
APP_ENV=production
SECRET_KEY=<segredo-forte>
APP_TIMEZONE=America/Sao_Paulo
```

A `SECRET_KEY` não possui fallback utilizável quando `APP_ENV=production`.

## Seed

```bash
BOOTSTRAP_ADMIN_PASSWORD='senha-forte' \
BOOTSTRAP_DIRECTOR_PASSWORD='senha-diretor' \
BOOTSTRAP_PROFESSOR_PASSWORD='senha-professor' \
DATABASE_URL='postgresql+asyncpg://...' \
python seed.py
```

Não versionar senhas nem `.env`.
