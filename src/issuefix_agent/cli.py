from __future__ import annotations

from pathlib import Path

import typer
from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from issuefix_agent.agent import IssueFixAgent
from issuefix_agent.config import get_settings
from issuefix_agent.repo import RepoInspector

app = typer.Typer(help="AI agent for turning issues into repair patches and PR drafts.")
console = Console()


@app.command()
def analyze(
    repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False, help="Repository path."),
    issue_file: Path | None = typer.Option(None, "--issue-file", exists=True, dir_okay=False),
    issue: str | None = typer.Option(None, "--issue", help="Issue text. Ignored if --issue-file is set."),
    apply: bool = typer.Option(False, "--apply", help="Apply generated patch after git apply --check."),
    test_command: str | None = typer.Option(None, "--test-command", help="Optional test command."),
) -> None:
    """Analyze an issue and produce a patch proposal."""
    issue_text = _load_issue(issue_file=issue_file, issue=issue)
    settings = get_settings()
    agent = IssueFixAgent(settings)
    result = agent.analyze(
        repo_path=str(repo),
        issue_text=issue_text,
        apply_patch=apply,
        test_command=test_command,
    )

    proposal = result.proposal
    console.print(Panel(proposal.summary or "No summary", title="Summary"))
    if proposal.plan:
        console.print(Panel("\n".join(f"- {item}" for item in proposal.plan), title="Plan"))
    if result.files_considered:
        console.print(Panel("\n".join(result.files_considered), title="Files considered"))
    if proposal.patch:
        console.print(Panel(Syntax(proposal.patch, "diff", word_wrap=True), title="Patch"))
    if proposal.tests:
        console.print(Panel("\n".join(f"- {item}" for item in proposal.tests), title="Tests"))
    if proposal.risks:
        console.print(Panel("\n".join(f"- {item}" for item in proposal.risks), title="Risks"))
    if proposal.pr_title or proposal.pr_body:
        console.print(Panel(f"{proposal.pr_title}\n\n{proposal.pr_body}", title="PR Draft"))
    if result.patch_check:
        console.print(
            Panel(
                f"exit_code={result.patch_check.exit_code}\n{result.patch_check.stderr or result.patch_check.stdout}",
                title="Patch check",
            )
        )
    if result.test_result:
        console.print(
            Panel(
                f"exit_code={result.test_result.exit_code}\n"
                f"STDOUT:\n{result.test_result.stdout}\n\nSTDERR:\n{result.test_result.stderr}",
                title="Test result",
            )
        )


@app.command()
def tree(repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False)) -> None:
    """Print an abbreviated repository tree."""
    inspector = RepoInspector(repo)
    console.print(inspector.tree())


@app.command()
def search(
    repo: Path = typer.Option(..., "--repo", exists=True, file_okay=False),
    query: str = typer.Option(..., "--query"),
) -> None:
    """Search likely relevant files for a query."""
    inspector = RepoInspector(repo)
    results = inspector.search(query)
    for item in results:
        console.print(f"[bold]{item.path}[/bold] score={item.score}")


def _load_issue(*, issue_file: Path | None, issue: str | None) -> str:
    if issue_file:
        return issue_file.read_text(encoding="utf-8")
    if issue:
        return issue
    raise typer.BadParameter("Provide --issue-file or --issue.")


if __name__ == "__main__":
    app()
