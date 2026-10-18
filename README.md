# ⚔️ JARVIS — SAO SYSTEM v2.0 & CENTRO DE COMANDO
**Assistente Pessoal de IA, Engenharia de Dados & Segundo Cérebro Vetorial integrado com Obsidian e Supabase pgvector**

---

## 🎯 Visão Geral
O **JARVIS (SAO System v2.0)** transforma a sua rotina e ecossistema pessoal em uma estação executiva de alta soberania baseada na filosofia estóico-teológica do Sentinela:
- **Fonte da Verdade:** Obsidian Vault estruturado em arquitetura RPG (`⚔️ Centro de Comando`, `🗡️ Masmorras`, `🏰 Guild Hall`, `📚 Biblioteca Sagrada`).
- **Segundo Cérebro Vetorial:** Supabase `pgvector` com embeddings de 768 dimensões (Gemini / OpenAI) e busca de similaridade por cosseno via HNSW.
- **Console Web Executivo:** Dashboard futurista com partículas, HUD animado do jogador, árvore de habilidades com gráfico radar, registro de vitórias e auditoria diária de XP.

---

## ⚡ Início Rápido

### 1. Requisitos
- **Runtime:** Python 3.10+ (Homologado no Python 3.14.5)
- **Dependências:** `pip install -r requirements.txt`

### 2. Configuração do `.env`
Copie `.env.example` para `.env` e preencha suas chaves:
```env
# Provedor de IA
DEFAULT_LLM_PROVIDER=gemini
GEMINI_API_KEY=sua_chave_aqui

# Supabase Segundo Cérebro (pgvector)
SUPABASE_URL=https://etztvnzxkhdoqwswajgb.supabase.co
SUPABASE_ANON_KEY=sua_anon_key_aqui
```

### 3. Execução

**Dashboard Web RPG (Recomendado):**
```bash
python main.py --web
```
Acesse no navegador: **`http://localhost:8080`**

**Terminal Interativo (CLI):**
```bash
python main.py
```

---

## 🚀 Opções de Deploy

### Opção 1: Render (Cloud)
O repositório inclui o blueprint `render.yaml`.
1. Conecte seu repositório no [Render Dashboard](https://dashboard.render.com/).
2. Crie um novo **Blueprint** apontando para este repositório.
3. Configure as variáveis de ambiente `SUPABASE_URL`, `SUPABASE_ANON_KEY` e `GEMINI_API_KEY`.

### Opção 2: Docker
```bash
docker build -t jarvis-sao .
docker run -p 8080:8080 --env-file .env jarvis-sao
```

---

## 🧪 Testes Automatizados
```bash
python -m pytest
```
Suíte completa com 29 testes cobrindo automação, memória, parsing, segurança, gamificação SAO e motor de embeddings Supabase.
