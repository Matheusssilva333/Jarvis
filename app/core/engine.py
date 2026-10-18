"""Central JARVIS Brain and Query Orchestrator."""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any

from app.core.config import logger, settings
from app.knowledge.retriever import KnowledgeRetriever, SearchResult
from app.memory.manager import ConversationMemory
from app.providers.base import BaseLLMProvider, LLMResponse
from app.providers.factory import get_llm_provider
from app.sao.manager import SAOSystemManager
from app.tools.registry import ToolRegistry


@dataclass
class EngineResponse:
    reply: str
    sources: list[str] = field(default_factory=list)
    tasks_retrieved: int = 0
    latency_seconds: float = 0.0
    model: str = ""
    provider: str = ""


SYSTEM_PROMPT = """Você é o JARVIS / Sentinela Core v2.0, o assistente pessoal de elite e clone analítico de Matheus Silva.

# 🧠 DIRETRIZES FUNDAMENTAIS DE PERSONALIDADE
- **Tom:** Autoritário, Socrático, Profundo e Cirúrgico. Frases curtas, diretas e com densidade de pensamento.
- **Rigor Industrial:** Responda com base em evidências verificáveis. Despreze prolixidade e ruído digital.
- **Dialética Metal-Espírito:** Integração entre disciplina técnica (Engenharia de Software, Caldeiraria, Normas Técnicas, Automação) e sabedoria (autodomínio, propósito, teologia bíblica).
- **Gamificação Realista (SAO System):** A vida é um log de auditoria. Trate tarefas e metas como XP e evolução de Rank.

# 📚 USO DO CONHECIMENTO DO COFRE OBSIDIAN
- O cofre do Obsidian é a sua memória factual.
- Sempre que citar informações do contexto fornecido, referencie a nota de origem com wikilinks: [[Nome da Nota]].
- Se uma informação não constar nas anotações recuperadas, admita com honestidade cirúrgica sem inventar dados.
- Não confunda anotações do cofre com palpites aleatórios.

# 🛠️ AÇÃO E PROATIVIDADE
- Ajude Matheus a manter foco implacável na sua preparação para a Petrobras (Parada de Manutenção UT2), faculdade de ADS e transição para Engenharia de Software.
"""


class JarvisEngine:
    """Orchestrates intent parsing, vault retrieval, memory, tools, and LLM generation."""

    def __init__(
        self,
        provider: BaseLLMProvider | None = None,
        retriever: KnowledgeRetriever | None = None,
        memory: ConversationMemory | None = None,
        tools: ToolRegistry | None = None,
        sao: SAOSystemManager | None = None,
    ):
        self.provider = provider or get_llm_provider()
        self.retriever = retriever or KnowledgeRetriever()
        self.memory = memory or ConversationMemory()
        self.tools = tools or ToolRegistry()
        self.sao = sao or SAOSystemManager()

    def process(self, user_input: str) -> EngineResponse:
        """Process user input with knowledge retrieval and contextual generation."""
        start_time = time.time()
        clean_input = user_input.strip()

        if not clean_input:
            return EngineResponse(reply="Comando vazio. Apresente uma instrução válida.")

        low = clean_input.lower()

        # 1. Quick intent interception for SAO System
        if any(kw in low for kw in ["processe meu progresso", "processar diario", "processar diário", "meu xp de hoje", "processe meu dia"]):
            return self._handle_sao_process_daily()

        if any(kw in low for kw in ["status do jogador", "meu status atual", "meu rank", "meu level", "meu nível"]):
            return self._handle_sao_status()

        # 2. Quick intent interception for direct task queries
        if any(kw in low for kw in ["tarefas pendentes", "o que tenho que fazer", "quais minhas tarefas", "minhas pendências"]):
            return self._handle_pending_tasks_query()

        if any(kw in low for kw in ["status do sistema", "resumo do cofre", "estatísticas do cofre"]):
            return self._handle_system_stats_query()

        # 2. Knowledge Retrieval (RAG)
        search_results = self.retriever.search(clean_input, limit=settings.max_search_results)
        sources = list(dict.fromkeys(r.note_path for r in search_results))

        # 3. Assemble Dynamic Context
        context_blocks = []
        if search_results:
            context_blocks.append("--- CONTEXTO RECUPERADO DO COFRE OBSIDIAN ---")
            for res in search_results:
                context_blocks.append(
                    f"Origem: [[{res.title}]] (Arquivo: {res.note_path})\n"
                    f"Seção: {res.heading}\n"
                    f"Conteúdo:\n{res.content}\n"
                )
            context_blocks.append("--- FIM DO CONTEXTO ---")

        # 4. Check if relevant tasks match the topic
        task_matches = self.retriever.get_tasks(completed=False, search=clean_input, limit=5)
        if task_matches:
            context_blocks.append("\n--- TAREFAS PENDENTES RELACIONADAS ---")
            for t in task_matches:
                context_blocks.append(f"- [ ] {t['description']} (em [[{t['note_path']}]])")

        assembled_context = "\n".join(context_blocks)

        prompt_with_context = clean_input
        if assembled_context:
            prompt_with_context = (
                f"{clean_input}\n\n"
                f"[DADOS DO SEU COFRE DISPONÍVEIS PARA ESSA CONSULTA]:\n{assembled_context}"
            )

        # 5. Memory Management
        self.memory.add_user_message(clean_input)
        messages_for_llm = self.memory.get_messages(system_prompt=SYSTEM_PROMPT)

        # Replace last user message with augmented prompt
        messages_for_llm[-1].content = prompt_with_context

        # 6. LLM Generation
        response = self.provider.generate(messages_for_llm)
        self.memory.add_assistant_message(response.content)

        latency = time.time() - start_time
        logger.info(
            f"Query processed in {latency:.2f}s | Provider: {response.provider} | Sources: {len(sources)}"
        )

        return EngineResponse(
            reply=response.content,
            sources=sources,
            tasks_retrieved=len(task_matches),
            latency_seconds=round(latency, 3),
            model=response.model,
            provider=response.provider,
        )

    def _handle_pending_tasks_query(self) -> EngineResponse:
        """Direct query for pending tasks without calling external LLM."""
        start_time = time.time()
        tasks = self.retriever.get_tasks(completed=False, limit=20)
        stats = self.retriever.get_system_overview() if hasattr(self.retriever, "get_system_overview") else {}

        if not tasks:
            reply = "Nenhuma tarefa pendente registrada no cofre. O mural está limpo."
        else:
            lines = [
                f"### 📋 TAREFAS PENDENTES AUDITADAS (Total no cofre: {len(tasks)})",
                "",
            ]
            for t in tasks:
                due = f" (📅 Prazo: {t['due_date']})" if t.get("due_date") else ""
                priority = f" [{t['priority'].upper()}]" if t.get("priority") else ""
                lines.append(f"- [ ] **{t['description']}**{due}{priority} — em `[[{t['note_path']}]]`")

            lines.append("")
            lines.append("*Ação exigida: Escolha a prioridade de Rank A e execute sem procrastinação.*")
            reply = "\n".join(lines)

        self.memory.add_user_message("quais são minhas tarefas pendentes?")
        self.memory.add_assistant_message(reply)

        return EngineResponse(
            reply=reply,
            tasks_retrieved=len(tasks),
            latency_seconds=round(time.time() - start_time, 3),
            model="internal_sql_engine",
            provider="sqlite",
        )

    def _handle_system_stats_query(self) -> EngineResponse:
        """Return system inventory and health directly."""
        start_time = time.time()
        stats = self.retriever.get_summary_context()
        reply = (
            f"### 🛡️ STATUS DO SISTEMA SENTINELA / OBSIDIAN VAULT\n\n"
            f"- **Notas Mapeadas:** {stats['total_notes']}\n"
            f"- **Seções Indexadas (RAG):** {stats['total_sections']}\n"
            f"- **Tarefas Registradas:** {stats['total_tasks']} "
            f"({stats['completed_tasks']} concluídas ✅ | {stats['pending_tasks']} pendentes ⏳)\n"
            f"- **Conexões do Grafo:** {stats['total_links']} links\n"
            f"- **Provedor Ativo:** {self.provider.__class__.__name__}\n"
            f"- **Nível de Segurança:** {settings.security_level}\n\n"
            f"*O cofre está sincronizado e pronto para consulta.*"
        )
        self.memory.add_user_message("status do sistema")
        self.memory.add_assistant_message(reply)

        return EngineResponse(
            reply=reply,
            latency_seconds=round(time.time() - start_time, 3),
            model="internal_metrics",
            provider="sqlite",
        )

    def _handle_sao_status(self) -> EngineResponse:
        """Return player game status in the SAO system."""
        start_time = time.time()
        stats = self.sao.get_stats()

        reply = (
            f"### ⚔️ STATUS DO JOGADOR — SAO SYSTEM v2.0\n\n"
            f"- **Jogador:** {stats.name}\n"
            f"- **Título:** `{stats.title}`\n"
            f"- **Rank:** **{stats.rank}**\n"
            f"- **Nível Atual:** {stats.level}\n"
            f"- **XP Acumulado:** {stats.xp} / {stats.next_level_xp} XP\n"
            f"- **Tarefas Concluídas (Histórico):** {stats.tasks_completed_lifetime} ✅\n\n"
            f"*O Binário do Caráter:* Ou há Evidência (XP) ou há Ruído (Falha). Sem prova, o XP é negado."
        )

        self.memory.add_user_message("Sistema, mostre meu status atual.")
        self.memory.add_assistant_message(reply)

        return EngineResponse(
            reply=reply,
            latency_seconds=round(time.time() - start_time, 3),
            model="sao_engine",
            provider="sao",
        )

    def _handle_sao_process_daily(self) -> EngineResponse:
        """Process XP from completed tasks today."""
        start_time = time.time()
        res = self.sao.process_daily()

        level_msg = "🔥 **LEVEL UP! Novo nível alcançado!**\n" if res["leveled_up"] else ""

        reply = (
            f"### ⚔️ AUDITORIA DIÁRIA SAO SYSTEM PROCESSADA\n\n"
            f"{level_msg}"
            f"- **Data Auditada:** {res['date']}\n"
            f"- **Tarefas Validadas:** {res['tasks_count']} concluídas\n"
            f"- **XP Conquistado Hoje:** +{res['xp_earned']} XP\n"
            f"- **XP Total:** {res['total_xp']} XP\n"
            f"- **Nível:** {res['level']} ({res['rank']})\n\n"
            f"*Progresso registrado em `[[05 System/Player Stats.md]]`.*"
        )

        self.memory.add_user_message("Sistema, processe meu progresso de hoje.")
        self.memory.add_assistant_message(reply)

        return EngineResponse(
            reply=reply,
            latency_seconds=round(time.time() - start_time, 3),
            model="sao_engine",
            provider="sao",
        )
