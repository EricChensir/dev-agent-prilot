from __future__ import annotations

from fastapi import FastAPI, HTTPException

from issuefix_agent.agent import IssueFixAgent
from issuefix_agent.config import get_settings
from issuefix_agent.models import AgentRequest, AgentResult
from issuefix_agent.repo import RepoError

app = FastAPI(title="Dev Agent Prilot", version="0.1.0")


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/analyze", response_model=AgentResult)
def analyze(request: AgentRequest) -> AgentResult:
    try:
        agent = IssueFixAgent(get_settings())
        return agent.analyze(
            repo_path=request.repo_path,
            issue_text=request.issue_text,
            apply_patch=request.apply_patch,
            test_command=request.test_command,
        )
    except RepoError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    except RuntimeError as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
