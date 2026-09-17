# Matriz de compatibilidade Python

A compatibilidade do projeto é validada automaticamente no GitHub Actions para:

- Python 3.12
- Python 3.13
- Python 3.14

A matriz usa exatamente as versões de dependências definidas em `requirements.txt`.

## O que é testado em cada versão

1. Instalação completa de `requirements.txt`.
2. `pip check`, para detectar dependências incompatíveis ou ausentes.
3. Verificação da versão efetivamente executada.
4. Compilação de todos os arquivos `.py`.
5. Importação de todos os módulos Python via `tests_imports.py`.
6. Regras críticas do sistema via `tests_regras.py`.

## Interpretação

- **verde**: a combinação Python + dependências passou a suíte definida.
- **vermelho**: a versão não deve ser usada em produção até que a causa seja corrigida.
- O teste não acessa o Neon nem inicia um servidor web.

## Execução manual equivalente

Após instalar as dependências na versão de Python desejada:

```bash
python -m pip check
python -m compileall -q .
python tests_imports.py
python tests_regras.py
```

O resultado da matriz oficial deve ser obtido pelo workflow `.github/workflows/python-matrix.yml` em um runner do GitHub, porque este ambiente local pode não possuir as três versões do Python nem todos os wheels das dependências.
