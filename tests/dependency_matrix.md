# Matriz de dependências — RC-2

A RC-2 moderniza o stack do protótipo antes da integração com Neon e Render.

| Componente | RC-1 | RC-2 | Motivo |
|---|---|---|---|
| FastAPI | 0.104.1 | 0.141.1 | stack atual e suporte Python moderno |
| Uvicorn | 0.24.0 | 0.53.0 | suporte Python 3.12–3.14 |
| SQLAlchemy | 2.0.23 | 2.0.54 | manutenção/compatibilidade atual |
| asyncpg | 0.29.0 | 0.31.0 | wheels atuais para Python 3.13/3.14 |
| Pydantic | 2.5.0 | 2.13.5 | elimina cadeia antiga de pydantic-core |
| python-dotenv | 1.0.0 | 1.2.3 | suporte atual a Python 3.14 |
| Jinja2 | 3.1.2 | 3.1.6 | correções e versão estável atual |
| JWT | python-jose 3.3.0 | PyJWT 2.14.0 | release atual com classifiers 3.12–3.14 |
| Hash de senha | passlib 1.7.4 + bcrypt | pwdlib 0.3.1 + argon2 | passlib não acompanha Python moderno; Argon2id como padrão novo |
| python-multipart | 0.0.6 | 0.0.32 | versão atual com 3.12–3.14 |
| Alembic | 1.13.1 | 1.20.0 | versão atual |
| openpyxl | 3.1.5 | 3.1.5 | continua sendo a versão estável publicada |
| xlrd | 2.0.1 | 2.0.2 | suporte a `.xls` |
| psycopg2-binary | 2.9.9 | removido | não usado pelo código assíncrono |

A matriz CI continua testando as três versões de Python; o `.python-version` fixa 3.12 para o ambiente de produção até que o CI de RC-2 valide todas as versões.
