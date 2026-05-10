from __future__ import annotations

import os
import re
import subprocess
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


IGNORE_DIRS = {
    ".git",
    ".hg",
    ".svn",
    ".venv",
    "venv",
    "env",
    "node_modules",
    "dist",
    "build",
    "target",
    ".next",
    ".nuxt",
    "coverage",
    "htmlcov",
    "__pycache__",
    ".pytest_cache",
    ".mypy_cache",
    ".ruff_cache",
}

TEXT_EXTENSIONS = {
    ".py",
    ".js",
    ".jsx",
    ".ts",
    ".tsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".c",
    ".h",
    ".cpp",
    ".hpp",
    ".cs",
    ".php",
    ".rb",
    ".swift",
    ".sql",
    ".yml",
    ".yaml",
    ".json",
    ".toml",
    ".ini",
    ".md",
    ".txt",
    ".env",
    ".example",
    ".dockerfile",
}


@dataclass(frozen=True)
class FileContext:
    path: str
    content: str
    score: int


class RepoError(RuntimeError):
    """Raised when repository operations fail."""


class RepoInspector:
    def __init__(
        self,
        repo_path: str | Path,
        *,
        max_file_chars: int = 12_000,
        max_context_chars: int = 45_000,
        max_files: int = 24,
    ) -> None:
        self.root = Path(repo_path).expanduser().resolve()
        self.max_file_chars = max_file_chars
        self.max_context_chars = max_context_chars
        self.max_files = max_files
        if not self.root.exists() or not self.root.is_dir():
            raise RepoError(f"Repository path does not exist or is not a directory: {self.root}")

    def list_files(self) -> list[str]:
        files: list[str] = []
        for path in self.root.rglob("*"):
            if self._should_skip(path):
                continue
            if path.is_file() and self._looks_textual(path):
                files.append(self._relative(path))
        return sorted(files)

    def tree(self, *, limit: int = 240) -> str:
        lines: list[str] = []
        for index, rel in enumerate(self.list_files()):
            if index >= limit:
                lines.append(f"... ({len(self.list_files()) - limit} more files)")
                break
            depth = rel.count(os.sep)
            lines.append(f"{'  ' * depth}- {Path(rel).name}")
        return "\n".join(lines)

    def read_file(self, relative_path: str) -> str:
        path = (self.root / relative_path).resolve()
        if not self._is_inside_root(path):
            raise RepoError(f"Refusing to read outside repo: {relative_path}")
        if not path.exists() or not path.is_file():
            raise RepoError(f"File does not exist: {relative_path}")
        return self._read_text(path)

    def search(self, query: str, *, limit: int = 20) -> list[FileContext]:
        keywords = extract_keywords(query)
        scored: list[FileContext] = []
        for rel in self.list_files():
            path = self.root / rel
            content = self._read_text(path)
            score = score_text(rel, content, keywords)
            if score > 0:
                scored.append(FileContext(path=rel, content=content[: self.max_file_chars], score=score))
        return sorted(scored, key=lambda item: (-item.score, item.path))[:limit]

    def collect_context(self, issue_text: str) -> tuple[str, list[FileContext]]:
        candidates = self.search(issue_text, limit=self.max_files)
        parts = ["# Repository tree", self.tree(), ""]
        used: list[FileContext] = []
        total = sum(len(part) for part in parts)
        for file_context in candidates:
            block = (
                f"\n# File: {file_context.path}\n"
                "```\n"
                f"{file_context.content}\n"
                "```\n"
            )
            if total + len(block) > self.max_context_chars:
                break
            parts.append(block)
            total += len(block)
            used.append(file_context)
        return "\n".join(parts), used

    def apply_patch_check(self, patch: str) -> subprocess.CompletedProcess[str]:
        return self._run(["git", "apply", "--check", "-"], input_text=patch)

    def apply_patch(self, patch: str) -> subprocess.CompletedProcess[str]:
        return self._run(["git", "apply", "-"], input_text=patch)

    def run_command(self, command: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            command,
            cwd=self.root,
            shell=True,
            text=True,
            capture_output=True,
            timeout=180,
            check=False,
        )

    def _run(self, args: list[str], *, input_text: str) -> subprocess.CompletedProcess[str]:
        return subprocess.run(
            args,
            cwd=self.root,
            input=input_text,
            text=True,
            capture_output=True,
            timeout=60,
            check=False,
        )

    def _should_skip(self, path: Path) -> bool:
        parts = set(path.relative_to(self.root).parts) if self._is_inside_root(path) else set()
        return bool(parts & IGNORE_DIRS)

    def _looks_textual(self, path: Path) -> bool:
        name = path.name.lower()
        if name in {"dockerfile", "makefile", "license"}:
            return True
        if path.suffix.lower() in TEXT_EXTENSIONS:
            return True
        try:
            chunk = path.read_bytes()[:2048]
        except OSError:
            return False
        return b"\x00" not in chunk

    def _read_text(self, path: Path) -> str:
        try:
            text = path.read_text(encoding="utf-8", errors="replace")
        except OSError as exc:
            raise RepoError(f"Unable to read {path}: {exc}") from exc
        if len(text) > self.max_file_chars:
            return text[: self.max_file_chars] + "\n... [truncated]\n"
        return text

    def _relative(self, path: Path) -> str:
        return str(path.relative_to(self.root))

    def _is_inside_root(self, path: Path) -> bool:
        try:
            path.resolve().relative_to(self.root)
            return True
        except ValueError:
            return False


def extract_keywords(text: str) -> list[str]:
    tokens = re.findall(r"[A-Za-z_][A-Za-z0-9_]{2,}|/[A-Za-z0-9_./-]+|[A-Z0-9_]{3,}", text)
    stopwords = {
        "the",
        "and",
        "for",
        "with",
        "that",
        "this",
        "from",
        "when",
        "then",
        "into",
        "return",
        "returns",
        "error",
        "issue",
        "bug",
    }
    normalized: list[str] = []
    seen: set[str] = set()
    for token in tokens:
        value = token.strip("/.").lower()
        if len(value) < 3 or value in stopwords or value in seen:
            continue
        seen.add(value)
        normalized.append(value)
    return normalized[:32]


def score_text(path: str, content: str, keywords: Iterable[str]) -> int:
    path_lower = path.lower()
    content_lower = content.lower()
    score = 0
    for keyword in keywords:
        if keyword in path_lower:
            score += 8
        count = content_lower.count(keyword)
        score += min(count, 12)
    if "test" in path_lower or "spec" in path_lower:
        score += 2
    return score
