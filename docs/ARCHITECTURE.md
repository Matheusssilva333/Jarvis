# ARQUITETURA DO SISTEMA — JARVIS / SENTINELA CORE

## 1. Visão Arquitetural

```
[ Usuário ]
    │
    ▼
[ Interface CLI (Rich) ] ──▶ [ Orquestrador Central (JarvisEngine) ]
                                    │               │               │
                 ┌──────────────────┘               │               └──────────────────┐
                 ▼                                  ▼                                  ▼
      [ KnowledgeRetriever ]            [ ConversationMemory ]              [ BaseLLMProvider ]
                 │                                                                     │
     ┌───────────┴───────────┐                                                 ┌───────┴───────┐
     ▼                       ▼                                                 ▼               ▼
[ SQLite FTS5 ]       [ Grafo Links / Tasks ]                             [ Gemini/Claude ] [ Ollama ]
     ▲                       ▲
     └───────────┬───────────┘
                 │
        [ VaultIndexer ]
                 ▲
                 │
       [ Obsidian Vault (.md) ]
```

## 2. Componentes

### 2.1. Knowledge Layer (`app/knowledge/`)
- **NoteParser:** Processador determinístico para Markdown, extraindo frontmatter YAML, cabeçalhos hierárquicos, tags Unicode, wikilinks `[[Nota]]` e tarefas Obsidian (`- [ ]`, `- [x]`, `✅`, `📅`, prioridades).
- **KnowledgeStorage:** Banco relacional SQLite operando em modo WAL com tabela virtual FTS5 (`unicode61 remove_diacritics 2`) e ranking estatístico BM25.
- **VaultIndexer:** Sincronizador incremental que calcula o hash SHA-256 e timestamp `mtime` de cada nota. Se o arquivo não sofreu modificação, ele não é reprocessado (varredura completa em ~10ms).
- **KnowledgeRetriever:** Camada de consulta que unifica busca de seções com snippets, grafos de links e backlinks, e inventário de tarefas.

### 2.2. Memory Layer (`app/memory/`)
- **ConversationMemory:** Buffer deslizante com controle estrito de turnos para manter contexto conversacional sem explosão de tokens. Suporta serialização em Markdown compatível com Obsidian.

### 2.3. Providers Layer (`app/providers/`)
- Abstração agnóstica via `BaseLLMProvider`.
- Suporte a provedores em nuvem de alta capacidade (Gemini, Claude, OpenAI) e local via Ollama (`qwen2.5:1.5b-instruct`).
- Mecanismo de fallback inteligente: na ausência de chaves de API ou modelos locais, o sistema opera de forma segura com o `MockProvider` e consultas SQL diretas.

### 2.4. Core Layer (`app/core/`)
- **JarvisEngine:** Ponto único de coordenação. Recebe prompts, identifica intenções especiais (tarefas, métricas, reindexação), injeta apenas os chunks recuperados pertinentes e gera respostas contextualizadas no tom do Projeto Sentinela.
