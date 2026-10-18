# GUIA DE CONFIGURAÇÃO — JARVIS

## Variáveis de Ambiente (`.env`)

| Variável | Padrão | Descrição |
| :--- | :--- | :--- |
| `OBSIDIAN_VAULT_PATH` | `..` | Caminho relativo ou absoluto para a raiz do cofre Obsidian |
| `DEFAULT_LLM_PROVIDER` | `gemini` | Provedor de IA ativo (`gemini`, `claude`, `ollama`, `openai`) |
| `GEMINI_API_KEY` | *(vazio)* | Chave de API do Google Gemini (se provedor for `gemini`) |
| `ANTHROPIC_API_KEY` | *(vazio)* | Chave de API da Anthropic (se provedor for `claude`) |
| `OPENAI_API_KEY` | *(vazio)* | Chave de API da OpenAI (se provedor for `openai`) |
| `OLLAMA_BASE_URL` | `http://localhost:11434` | Endpoint do daemon local Ollama |
| `OLLAMA_MODEL` | `qwen2.5:1.5b-instruct` | Modelo local sugerido para CPU Ivy Bridge |
| `SECURITY_LEVEL` | `2` | Nível de permissão operacional (1 a 4) |
| `MAX_SEARCH_RESULTS` | `5` | Número de fragmentos mais relevantes retornados pelo RAG |

## Alternando Modelos
Para alterar o provedor ativo, basta editar a linha no arquivo `jarvis/.env`:
```ini
DEFAULT_LLM_PROVIDER=claude
ANTHROPIC_API_KEY=sua-chave-aqui
```
Ou para usar Ollama local:
```ini
DEFAULT_LLM_PROVIDER=ollama
OLLAMA_MODEL=qwen2.5:1.5b-instruct
```
*(Certifique-se de executar `ollama pull qwen2.5:1.5b-instruct` no terminal antes de usar).*
