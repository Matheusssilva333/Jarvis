"""Interactive Terminal Interface (CLI) for JARVIS."""
from __future__ import annotations

import sys
from pathlib import Path

from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.prompt import Prompt
from rich.table import Table

from app.core.config import settings
from app.core.engine import JarvisEngine
from app.knowledge.indexer import VaultIndexer
from app.knowledge.storage import KnowledgeStorage


console = Console()


def print_banner() -> None:
    """Display the Sentinela / JARVIS initialization header."""
    banner = """
    ╔══════════════════════════════════════════════════════════════╗
    ║       J.A.R.V.I.S.  —  PROJETO SENTINELA CORE v2.0          ║
    ║        Assistente Local de IA & Inteligência Pessoal         ║
    ║             Fonte da Verdade: Obsidian Vault                 ║
    ╚══════════════════════════════════════════════════════════════╝
    """
    console.print(f"[bold cyan]{banner}[/bold cyan]")
    console.print(
        f"[dim]Cofre: {settings.vault_path} | "
        f"Segurança: Nível {settings.security_level} | "
        f"Provedor: {settings.default_llm_provider.upper()}[/dim]\n"
    )
    console.print("[yellow]Digite sua pergunta ou use [bold]/help[/bold] para comandos do sistema.[/yellow]\n")


def display_help() -> None:
    """Show available CLI shortcut commands."""
    table = Table(title="Comandos do Sistema JARVIS", show_header=True, header_style="bold magenta")
    table.add_column("Comando", style="cyan", width=15)
    table.add_column("Descrição")

    table.add_row("/status", "Exibe estatísticas do cofre, hardware e conexões")
    table.add_row("/tasks", "Lista as principais tarefas pendentes do cofre")
    table.add_row("/reindex", "Executa varredura incremental de novas notas no cofre")
    table.add_row("/supabase", "Sincroniza chunks e embeddings com o Supabase pgvector")
    table.add_row("/audit", "Processa tarefas de hoje e calcula XP no SAO System")
    table.add_row("/clear", "Limpa a memória da conversa atual")
    table.add_row("/export", "Exporta a conversa atual para o Diário do Herói")
    table.add_row("/help", "Exibe esta tabela de ajuda")
    table.add_row("/exit", "Encerra a sessão")
    console.print(table)


def run_cli() -> None:
    """Main CLI loop."""
    print_banner()

    storage = KnowledgeStorage()
    indexer = VaultIndexer(storage=storage)
    engine = JarvisEngine(retriever=None)

    # Initial quick incremental check
    report = indexer.scan_vault()
    if report.added or report.updated or report.deleted:
        console.print(
            f"[dim green]Sincronização: {report.added} adicionadas, {report.updated} atualizadas.[/dim green]"
        )

    while True:
        try:
            user_input = Prompt.ask("\n[bold green]Matheus[/bold green]")
            clean_input = user_input.strip()

            if not clean_input:
                continue

            if clean_input.lower() in ["/exit", "exit", "sair", "quit"]:
                console.print("[bold cyan]JARVIS:[/bold cyan] Sessão encerrada. O Sentinela permanece alerta no muro.")
                break

            if clean_input.lower() == "/help":
                display_help()
                continue

            if clean_input.lower() == "/clear":
                engine.memory.clear()
                console.print("[dim yellow]Memória da sessão limpa com sucesso.[/dim yellow]")
                continue

            if clean_input.lower() == "/reindex":
                with console.status("[bold cyan]Sincronizando cofre do Obsidian..."):
                    rep = indexer.scan_vault()
                console.print(
                    f"[green]Concluído em {rep.elapsed_seconds}s: "
                    f"{rep.added} adicionadas, {rep.updated} atualizadas, {rep.unchanged} inalteradas.[/green]"
                )
                continue

            if clean_input.lower() in ["/supabase", "/sync"]:
                from app.knowledge.supabase_sync import VaultKnowledgeSynchronizer
                with console.status("[bold cyan]Sincronizando com Supabase pgvector..."):
                    sync_res = VaultKnowledgeSynchronizer().sync_to_supabase()
                if sync_res.get("success"):
                    console.print(f"[bold green]✓ Supabase atualizado com sucesso: {sync_res.get('chunks_upserted')} chunks em {sync_res.get('elapsed_seconds')}s.[/bold green]")
                else:
                    console.print(f"[bold yellow]{sync_res.get('message', sync_res.get('error'))}[/bold yellow]")
                continue

            if clean_input.lower() == "/audit":
                from app.sao.manager import SAOSystemManager
                mgr = SAOSystemManager(storage=storage)
                res = mgr.process_daily()
                console.print(
                    f"[bold green]✓ Auditoria Concluída: +{res['xp_earned']} XP! Total: {res['total_xp']} XP (Nível {res['level']} - {res['rank']}).[/bold green]"
                )
                continue

            if clean_input.lower() == "/tasks":
                resp = engine.process("quais são minhas tarefas pendentes?")
                console.print(Markdown(resp.reply))
                continue

            if clean_input.lower() == "/status":
                resp = engine.process("status do sistema")
                console.print(Markdown(resp.reply))
                continue

            if clean_input.lower() == "/export":
                md_content = engine.memory.export_as_markdown()
                export_dir = settings.vault_path / "📜 Diário do Herói"
                export_dir.mkdir(parents=True, exist_ok=True)
                export_file = export_dir / "Sessao JARVIS - Registro.md"
                export_file.write_text(md_content, encoding="utf-8")
                console.print(f"[green]Conversa exportada com sucesso para: {export_file.name}[/green]")
                continue

            # Process regular query
            with console.status("[bold cyan]JARVIS consultando cofre e processando..."):
                response = engine.process(clean_input)

            console.print()
            console.print(Panel(Markdown(response.reply), title="[bold cyan]JARVIS[/bold cyan]", border_style="cyan"))

            # Print source metadata if notes were used
            if response.sources:
                sources_str = ", ".join(f"`[[{Path(s).stem}]]`" for s in response.sources[:4])
                console.print(
                    f"[dim]📚 Fontes consultadas: {sources_str} | "
                    f"Latência: {response.latency_seconds}s | Provedor: {response.provider}[/dim]"
                )

        except KeyboardInterrupt:
            console.print("\n[dim yellow]Operação cancelada pelo usuário.[/dim yellow]")
            break
        except Exception as e:
            console.print(f"[bold red]Erro operacional:[/bold red] {e}")


if __name__ == "__main__":
    run_cli()
