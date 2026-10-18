# GUIA DE DESENVOLVIMENTO & EXTENSÃO — JARVIS

## 1. Estrutura do Código

- `app/core/` — Configuração tipada, logging e orquestrador principal (`JarvisEngine`).
- `app/knowledge/` — Parsers, índices e banco de dados SQLite.
- `app/providers/` — Implementação e fábrica de provedores LLM.
- `app/memory/` — Gerenciamento de histórico de sessão e exportação de notas.
- `app/interface/` — Interface rica de linha de comando (`rich` CLI).
- `tests/` — Bateria de testes unitários e de integração (`pytest`).

## 2. Adicionando uma Nova Ferramenta (`app/tools/`)

Para adicionar uma nova ferramenta (ex: consultar previsão do tempo, monitorar processos ou inspecionar portas de rede):

1. Crie o arquivo em `app/tools/<nome_da_ferramenta>.py`.
2. Herde da interface base:
```python
class BaseTool:
    name: str
    description: str
    security_level: int = 1  # 1 = Leitura, 2 = Escrita, 3 = Execução

    def execute(self, **kwargs) -> Any:
        pass
```
3. Registre a ferramenta no `JarvisEngine`.
4. Crie os testes unitários correspondentes em `tests/test_<nome_da_ferramenta>.py`.

## 3. Rodando a Suíte de Testes
```bash
python -m pytest tests/ -v
```
Todos os novos testes devem atingir 100% de aprovação sem regressões.
