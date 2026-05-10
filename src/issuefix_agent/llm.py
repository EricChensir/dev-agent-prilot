from __future__ import annotations

import json
import re
from typing import Protocol


from issuefix_agent.config import Settings
from issuefix_agent.models import PatchProposal


class LLMClient(Protocol):
    def generate_patch_proposal(self, *, issue_text: str, repo_context: str) -> tuple[PatchProposal, str]:
        """Return a parsed patch proposal and the raw model output."""


class OpenAIResponsesClient:
    def __init__(self, settings: Settings) -> None:
        if not settings.openai_api_key:
            raise RuntimeError("OPENAI_API_KEY is required. Set it in your environment or .env file.")
        from openai import OpenAI

        self.settings = settings
        self.client = OpenAI(api_key=settings.openai_api_key)

    def generate_patch_proposal(self, *, issue_text: str, repo_context: str) -> tuple[PatchProposal, str]:
        from issuefix_agent.prompts import SYSTEM_INSTRUCTIONS, build_repair_prompt

        prompt = build_repair_prompt(issue_text=issue_text, repo_context=repo_context)
        response = self.client.responses.create(
            model=self.settings.openai_model,
            instructions=SYSTEM_INSTRUCTIONS,
            input=prompt,
        )
        raw = response.output_text
        data = extract_json_object(raw)
        return PatchProposal.model_validate(data), raw


def extract_json_object(text: str) -> dict[str, object]:
    """Extract JSON from a model response, accepting plain JSON or fenced JSON."""
    stripped = text.strip()
    if stripped.startswith("```"):
        match = re.search(r"```(?:json)?\s*(.*?)\s*```", stripped, flags=re.DOTALL)
        if match:
            stripped = match.group(1).strip()
    try:
        parsed = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        parsed = json.loads(stripped[start : end + 1])
    if not isinstance(parsed, dict):
        raise ValueError("Expected a JSON object from model output.")
    return parsed
