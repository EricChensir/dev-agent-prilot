from __future__ import annotations

from issuefix_agent.config import Settings
from issuefix_agent.llm import LLMClient, OpenAIResponsesClient
from issuefix_agent.models import AgentResult, CommandResult
from issuefix_agent.repo import RepoInspector


class IssueFixAgent:
    def __init__(self, settings: Settings, llm_client: LLMClient | None = None) -> None:
        self.settings = settings
        self.llm_client = llm_client or OpenAIResponsesClient(settings)

    def analyze(
        self,
        *,
        repo_path: str,
        issue_text: str,
        apply_patch: bool = False,
        test_command: str | None = None,
    ) -> AgentResult:
        repo = RepoInspector(
            repo_path,
            max_file_chars=self.settings.max_file_chars,
            max_context_chars=self.settings.max_context_chars,
            max_files=self.settings.max_files,
        )
        repo_context, files = repo.collect_context(issue_text)
        proposal, raw = self.llm_client.generate_patch_proposal(
            issue_text=issue_text,
            repo_context=repo_context,
        )

        patch_check_result: CommandResult | None = None
        test_result: CommandResult | None = None
        patch_applied = False

        if proposal.patch.strip():
            checked = repo.apply_patch_check(proposal.patch)
            patch_check_result = CommandResult(
                command="git apply --check -",
                exit_code=checked.returncode,
                stdout=checked.stdout,
                stderr=checked.stderr,
            )
            if apply_patch and checked.returncode == 0:
                applied = repo.apply_patch(proposal.patch)
                patch_applied = applied.returncode == 0
                if applied.returncode != 0:
                    patch_check_result = CommandResult(
                        command="git apply -",
                        exit_code=applied.returncode,
                        stdout=applied.stdout,
                        stderr=applied.stderr,
                    )

        if test_command and (not apply_patch or patch_applied):
            tested = repo.run_command(test_command)
            test_result = CommandResult(
                command=test_command,
                exit_code=tested.returncode,
                stdout=tested.stdout[-12_000:],
                stderr=tested.stderr[-12_000:],
            )

        return AgentResult(
            proposal=proposal,
            files_considered=[file.path for file in files],
            patch_applied=patch_applied,
            patch_check=patch_check_result,
            test_result=test_result,
            raw_model_output=raw,
        )
