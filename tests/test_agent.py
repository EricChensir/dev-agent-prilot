from __future__ import annotations

from pathlib import Path

from issuefix_agent.agent import IssueFixAgent
from issuefix_agent.config import Settings
from issuefix_agent.models import PatchProposal


class FakeLLM:
    def generate_patch_proposal(self, *, issue_text: str, repo_context: str) -> tuple[PatchProposal, str]:
        return (
            PatchProposal(
                summary="No-op proposal",
                plan=["Inspect context"],
                patch="",
                tests=["pytest"],
                risks=["fake response"],
                pr_title="No-op",
                pr_body="No-op body",
            ),
            '{"summary":"No-op proposal"}',
        )


def test_agent_with_fake_llm(tmp_path: Path) -> None:
    (tmp_path / "app.py").write_text("print('hello')\n", encoding="utf-8")
    settings = Settings(OPENAI_API_KEY="fake")
    agent = IssueFixAgent(settings, llm_client=FakeLLM())
    result = agent.analyze(repo_path=str(tmp_path), issue_text="hello app")
    assert result.proposal.summary == "No-op proposal"
    assert result.patch_applied is False
