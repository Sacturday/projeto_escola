# Matriz de testes de compatibilidade

| Python | Instalação requirements | pip check | compileall | imports | regras | Status de uso |
|---|---|---|---|---|---|---|
| 3.12 | CI | CI | CI | CI | CI | Liberar após CI verde |
| 3.13 | CI | CI | CI | CI | CI | Liberar após CI verde |
| 3.14 | CI | CI | CI | CI | CI | Liberar após CI verde |

**Importante:** a matriz é deliberadamente executada contra o `requirements.txt` atual. Não há `continue-on-error`: uma combinação que falhar marca a execução correspondente como falha. Isso evita declarar compatibilidade sem evidência.
