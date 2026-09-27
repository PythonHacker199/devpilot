"""Self-contained BM25 search over a repository's source files."""
from __future__ import annotations

import ast
import math
import re
from dataclasses import dataclass
from pathlib import Path

# ---------------------------------------------------------------------------
# Public types
# ---------------------------------------------------------------------------

SKIP_DIRS = {
    ".git", "node_modules", ".venv", "venv", "__pycache__",
    ".devpilot", "dist", "build",
}


@dataclass
class Chunk:
    header: str   # "path:line — description"
    snippet: str  # first 300 chars of chunk text
    path: str     # repo-relative POSIX path
    line: int     # 1-based starting line


# ---------------------------------------------------------------------------
# Chunking helpers
# ---------------------------------------------------------------------------

def _posix(repo: Path, file: Path) -> str:
    return file.relative_to(repo).as_posix()


def _chunks_python(repo: Path, file: Path, text: str) -> list[Chunk]:
    try:
        tree = ast.parse(text, filename=str(file))
    except SyntaxError:
        return []

    lines = text.splitlines()
    chunks: list[Chunk] = []
    posix = _posix(repo, file)

    for node in ast.walk(tree):
        if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            continue
        start = node.lineno
        end = node.end_lineno or start
        snippet = "\n".join(lines[start - 1 : end])[:300]
        header = f"{posix}:{start} — {type(node).__name__} {node.name}"
        chunks.append(Chunk(header=header, snippet=snippet, path=posix, line=start))

    return chunks


def _chunks_markdown(repo: Path, file: Path, text: str) -> list[Chunk]:
    lines = text.splitlines()
    posix = _posix(repo, file)
    heading_pat = re.compile(r"^#{1,6}\s+(.+)")

    sections: list[tuple[int, str]] = []  # (1-based line, heading text)
    for i, line in enumerate(lines, start=1):
        m = heading_pat.match(line)
        if m:
            sections.append((i, m.group(1).strip()))

    if not sections:
        return _chunks_text(repo, file, text)

    chunks: list[Chunk] = []
    for idx, (line_no, heading) in enumerate(sections):
        next_line = sections[idx + 1][0] - 1 if idx + 1 < len(sections) else len(lines)
        body = "\n".join(lines[line_no - 1 : next_line])
        snippet = body[:300]
        header = f"{posix}:{line_no} — {heading}"
        chunks.append(Chunk(header=header, snippet=snippet, path=posix, line=line_no))

    return chunks


def _chunks_rst(repo: Path, file: Path, text: str) -> list[Chunk]:
    """RST: detect sections via underline characters (=, -, ~, ^, etc.)."""
    lines = text.splitlines()
    posix = _posix(repo, file)
    underline_chars = set("=-~^+`#'\"")

    section_starts: list[tuple[int, str]] = []  # (1-based line of heading, heading text)
    for i in range(len(lines)):
        line = lines[i]
        if (
            line.strip()
            and i + 1 < len(lines)
            and lines[i + 1].strip()
            and all(c in underline_chars for c in lines[i + 1].strip())
            and len(lines[i + 1].strip()) >= len(line.strip())
        ):
            section_starts.append((i + 1, line.strip()))  # 1-based

    if not section_starts:
        return _chunks_text(repo, file, text)

    chunks: list[Chunk] = []
    for idx, (line_no, heading) in enumerate(section_starts):
        next_line = section_starts[idx + 1][0] - 1 if idx + 1 < len(section_starts) else len(lines)
        body = "\n".join(lines[line_no - 1 : next_line])
        snippet = body[:300]
        header = f"{posix}:{line_no} — {heading}"
        chunks.append(Chunk(header=header, snippet=snippet, path=posix, line=line_no))

    return chunks


def _chunks_text(repo: Path, file: Path, text: str) -> list[Chunk]:
    """Split on blank lines into paragraphs of ≥ 3 lines."""
    lines = text.splitlines()
    posix = _posix(repo, file)
    chunks: list[Chunk] = []

    para_start: int | None = None
    para_lines: list[str] = []

    def flush(start: int, plines: list[str]) -> None:
        if len(plines) >= 3:
            body = "\n".join(plines)
            header = f"{posix}:{start} — (paragraph)"
            chunks.append(Chunk(header=header, snippet=body[:300], path=posix, line=start))

    for i, line in enumerate(lines, start=1):
        if line.strip() == "":
            if para_start is not None:
                flush(para_start, para_lines)
                para_start = None
                para_lines = []
        else:
            if para_start is None:
                para_start = i
            para_lines.append(line)

    if para_start is not None:
        flush(para_start, para_lines)

    return chunks


def _iter_files(repo: Path):
    for path in repo.rglob("*"):
        if not path.is_file():
            continue
        # skip unwanted directories
        if any(part in SKIP_DIRS for part in path.parts):
            continue
        yield path


def _collect_chunks(repo: Path) -> list[Chunk]:
    chunks: list[Chunk] = []
    for file in _iter_files(repo):
        try:
            text = file.read_text(encoding="utf-8")
        except (UnicodeDecodeError, PermissionError):
            continue

        suffix = file.suffix.lower()
        if suffix == ".py":
            py_chunks = _chunks_python(repo, file, text)
            if py_chunks:
                chunks.extend(py_chunks)
            else:
                # Plain-script files: emit the whole file as one chunk so
                # short scripts (no defs) are still searchable.
                posix = _posix(repo, file)
                stripped = text.strip()
                if stripped:
                    header = f"{posix}:1 — (module)"
                    chunks.append(Chunk(header=header, snippet=stripped[:300], path=posix, line=1))
        elif suffix == ".md":
            chunks.extend(_chunks_markdown(repo, file, text))
        elif suffix == ".rst":
            chunks.extend(_chunks_rst(repo, file, text))
        else:
            chunks.extend(_chunks_text(repo, file, text))

    return chunks


# ---------------------------------------------------------------------------
# BM25
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> list[str]:
    return [t for t in re.split(r"\W+", text.lower()) if t]


def answer(repo: Path, question: str, top_k: int = 5) -> list[tuple[Chunk, float]]:
    """Return top-k (Chunk, score) pairs for *question* over *repo*."""
    if not question.strip():
        return []

    chunks = _collect_chunks(repo)
    if not chunks:
        return []

    # Build BM25 index
    k1, b = 1.5, 0.75

    doc_tokens: list[list[str]] = [_tokenize(c.header + " " + c.snippet) for c in chunks]
    N = len(doc_tokens)
    avgdl = sum(len(d) for d in doc_tokens) / N

    # df per term
    df: dict[str, int] = {}
    for tokens in doc_tokens:
        for t in set(tokens):
            df[t] = df.get(t, 0) + 1

    query_terms = _tokenize(question)

    scores: list[float] = []
    for doc in doc_tokens:
        dl = len(doc)
        tf_map: dict[str, int] = {}
        for t in doc:
            tf_map[t] = tf_map.get(t, 0) + 1

        score = 0.0
        for t in query_terms:
            if t not in df:
                continue
            idf = math.log((N - df[t] + 0.5) / (df[t] + 0.5) + 1)
            tf = tf_map.get(t, 0)
            score += idf * tf * (k1 + 1) / (tf + k1 * (1 - b + b * dl / avgdl))
        scores.append(score)

    ranked = sorted(
        ((chunks[i], scores[i]) for i in range(N)),
        key=lambda x: x[1],
        reverse=True,
    )
    return ranked[:top_k]
