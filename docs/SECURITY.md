# DIRETRIZES DE SEGURANÇA E PRIVACIDADE — JARVIS

## 1. Níveis de Autorização

- **Nível 1 (Leitura Segura):**
  - Consultas FTS5, busca de tarefas, inventário de métricas e navegação do grafo.
  - Não altera nenhum arquivo do sistema operacional nem do cofre.

- **Nível 2 (Escrita Controlada - Padrão):**
  - Criação de novas notas autorizadas (ex: exportação de sessões para `01 Diário/`).
  - Nunca substitui nem apaga notas existentes.

- **Nível 3 (Execução):**
  - Execução de comandos no host e automações de tarefas.
  - Exige aprovação explícita e interativa no terminal.

- **Nível 4 (Ações Críticas / Destrutivas):**
  - Exclusão de arquivos, alterações em massa de tags/links ou comandos administrativos.
  - Bloqueado por padrão no código.

## 2. Privacidade do Cofre (Isolamento de Dados)
- **Zero Upload Massivo:** O cofre NUNCA é transmitido integralmente para APIs externas.
- **RAG Cirúrgico:** Apenas os fragmentos de texto (chunks) que obtiverem alta pontuação no índice local BM25 são incorporados ao prompt da consulta.
- **Segredos:** Nenhuma chave de API deve ser salva em arquivos markdown ou no versionamento. O `.env` está explicitamente no `.gitignore`.
