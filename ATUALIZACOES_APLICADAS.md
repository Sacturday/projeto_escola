# Atualizações e hardening aplicados

## Perfis e RBAC
- Perfis finais: `ADMIN`, `DIRETOR`, `PROFESSOR`.
- ADMIN tem escopo global.
- DIRETOR é limitado à própria escola.
- PROFESSOR é limitado às turmas em `professor_turma`.
- WebSocket valida usuário ativo e escopo da escola.
- Importação Excel é exclusiva do ADMIN.

## Frequência
- `NEUTRO` não é persistido.
- Ausência de registro em `frequencias` significa não lançado.
- PROFESSOR pode confirmar somente a chamada do dia atual.
- A confirmação exige exatamente todos os alunos ativos e matriculados da turma para a data.
- PROFESSOR não pode alterar `FALTA_JUSTIFICADA`.
- ADMIN/DIRETOR fazem correções posteriores via `PATCH` com `motivo` e auditoria.
- Concorrência otimista usa `versao`.

## Importação Excel
- `.xls` e `.xlsx`.
- `ESCOLAS.CODIGO` é obrigatório para suportar a cadeia Escola -> Turma -> Aluno -> Matrícula.
- Cabeçalhos duplicados são rejeitados.
- Limites: 10 MB, 50.000 linhas e 64 colunas.
- Validação relacional é executada antes da carga.
- Preview gera `importacao_id` e SHA-256; a confirmação só aceita o mesmo arquivo.
- A carga de dados é transacional; em falha, o lote é revertido.
- O histórico mantém uma única operação e muda de `PREVIA_VALIDADA` para `CONCLUIDA` ou `FALHA`.
- Usuários/senhas não são importados por planilha.

## Banco e produção
- Neon é o PostgreSQL da aplicação; Render hospeda somente o FastAPI.
- `create_all()` foi removido do startup.
- Alembic é o mecanismo oficial de evolução do schema.
- `updated_at` possui trigger PostgreSQL para alterações feitas fora do ORM.
- `SECRET_KEY` é obrigatória quando `APP_ENV=production`.
- `seed.py` exige `BOOTSTRAP_ADMIN_PASSWORD` e permite credenciais separadas via ambiente.

## Testes
- `tests_imports.py`: descobre e compila/importa todos os módulos Python quando as dependências estão instaladas.
- `tests_regras.py`: verifica regras críticas sem precisar de conexão com o Neon.
- Neste ambiente, a execução efetiva dos imports completos não pôde terminar porque as dependências externas não estão instaladas e a rede de pacotes está indisponível. A compilação dos módulos e os testes estáticos passaram.

## 2026-09-17 — Matriz Python 3.12/3.13/3.14

- Adicionado `.github/workflows/python-matrix.yml`.
- A matriz executa Python 3.12, 3.13 e 3.14 sem `continue-on-error`.
- Cada versão instala o `requirements.txt` exato, executa `pip check`, `compileall`, `tests_imports.py` e `tests_regras.py`.
- Adicionada documentação em `tests/README.md` e `tests/compatibility_matrix.md`.
- A compatibilidade não é presumida: cada versão precisa passar o CI para ser considerada apta para produção.
