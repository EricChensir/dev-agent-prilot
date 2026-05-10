from __future__ import annotations

SYSTEM_INSTRUCTIONS = """You are a senior software engineer acting as a code repair agent.
Your job is to inspect the given issue and repository context, then produce a safe, reviewable patch.
Be conservative. Do not invent files that are not implied by the context unless necessary.
Prefer small, testable changes. If context is insufficient, say so in risks.
Return only valid JSON. Do not wrap it in markdown fences.
"""


def build_repair_prompt(issue_text: str, repo_context: str) -> str:
    return f"""
Given the following issue and repository context, produce a code repair proposal.

The JSON response must match exactly this shape:
{{
  "summary": "one paragraph summary",
  "plan": ["step 1", "step 2"],
  "patch": "unified diff patch generated with git diff style paths",
  "tests": ["test command or test case to run"],
  "risks": ["risk or uncertainty"],
  "pr_title": "short PR title",
  "pr_body": "PR body with summary and test notes"
}}

Patch requirements:
- Use a valid unified diff.
- Use paths relative to the repository root.
- Do not include destructive changes.
- Keep the patch minimal.
- Include tests when the context shows a test structure.

Issue:
{issue_text}

Repository context:
{repo_context}
""".strip()
