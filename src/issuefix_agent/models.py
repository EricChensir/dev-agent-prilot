from __future__ import annotations

from pydantic import BaseModel, Field


class AgentRequest(BaseModel):
    repo_path: str = Field(..., description="Path to the local repository to inspect.")
    issue_text: str = Field(..., min_length=1, description="Issue, bug report, or task text.")
    apply_patch: bool = Field(default=False, description="Whether to apply the generated patch.")
    test_command: str | None = Field(default=None, description="Optional command to run after patching.")


class PatchProposal(BaseModel):
    summary: str = ""
    plan: list[str] = Field(default_factory=list)
    patch: str = ""
    tests: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    pr_title: str = ""
    pr_body: str = ""


class CommandResult(BaseModel):
    command: str
    exit_code: int
    stdout: str = ""
    stderr: str = ""


class AgentResult(BaseModel):
    proposal: PatchProposal
    files_considered: list[str] = Field(default_factory=list)
    patch_applied: bool = False
    patch_check: CommandResult | None = None
    test_result: CommandResult | None = None
    raw_model_output: str = ""
