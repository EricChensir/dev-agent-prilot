from __future__ import annotations

from pathlib import Path

from issuefix_agent.repo import RepoInspector, extract_keywords, score_text


def test_extract_keywords_keeps_code_like_tokens() -> None:
    keywords = extract_keywords("/api/me returns TOKEN_EXPIRED from decode_token middleware")
    assert "api/me" in keywords
    assert "token_expired" in keywords
    assert "decode_token" in keywords
    assert "middleware" in keywords


def test_repo_inspector_search_scores_relevant_files(tmp_path: Path) -> None:
    (tmp_path / "auth.py").write_text(
        "def decode_token(token):\n    raise TokenExpiredError()\n",
        encoding="utf-8",
    )
    (tmp_path / "README.md").write_text("hello", encoding="utf-8")
    inspector = RepoInspector(tmp_path)
    results = inspector.search("decode_token token expired", limit=5)
    assert results
    assert results[0].path == "auth.py"


def test_collect_context_includes_tree_and_file_content(tmp_path: Path) -> None:
    (tmp_path / "auth.py").write_text("def decode_token(): pass", encoding="utf-8")
    inspector = RepoInspector(tmp_path)
    context, files = inspector.collect_context("decode_token fails")
    assert "# Repository tree" in context
    assert "# File: auth.py" in context
    assert files[0].path == "auth.py"


def test_score_text_prioritizes_path_match() -> None:
    assert score_text("src/auth/token.py", "nothing", ["token"]) >= 8
