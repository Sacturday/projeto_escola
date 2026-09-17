# Modelos de planilha para importação

As importações são exclusivas do perfil ADMIN e aceitam `.xls` e `.xlsx`.

## ESCOLAS

```text
NOME | CODIGO
E.M. Albert Sabin | EAS001
E.M. Paulo Freire | EPF002
```

`CODIGO` é recomendado porque é usado para relacionar turmas, alunos e matrículas.

## TURMAS

```text
ESCOLA_CODIGO | NOME | ANO_LETIVO | TURNO
EAS001 | 5º Ano A | 2026 | MANHÃ
EAS001 | 5º Ano B | 2026 | TARDE
```

## ALUNOS

```text
ESCOLA_CODIGO | MATRICULA | NOME | DATA_NASCIMENTO
EAS001 | 20260001 | Lucas Silva | 12/04/2015
EAS001 | 20260002 | Beatriz Souza | 03/08/2015
```

## MATRICULAS

```text
ESCOLA_CODIGO | MATRICULA | TURMA_NOME | ANO_LETIVO | DATA_INICIO | DATA_FIM
EAS001 | 20260001 | 5º Ano A | 2026 | 02/02/2026 |
EAS001 | 20260002 | 5º Ano A | 2026 | 02/02/2026 |
```

## Regras

- A primeira linha da primeira planilha preenchida é o cabeçalho.
- Nomes de colunas são normalizados automaticamente (maiúsculas, sem acentos e com `_`).
- Datas podem ser `DD/MM/AAAA`, `AAAA-MM-DD` ou células de data do Excel.
- A importação não grava `frequencias`.
- Usuários não são importados por planilha para evitar transporte de senhas.
- O lote é atômico: qualquer falha durante a carga cancela todas as alterações daquele arquivo.
