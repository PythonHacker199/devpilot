from pathlib import Path

from devpilot.models import Language

_EXT_MAP: dict[str, str] = {
    ".py": "Python",
    ".ts": "TypeScript",
    ".tsx": "TypeScript",
    ".js": "JavaScript",
    ".jsx": "JavaScript",
    ".go": "Go",
    ".rb": "Ruby",
    ".rs": "Rust",
    ".java": "Java",
    ".md": "Markdown",
    ".yml": "YAML",
    ".yaml": "YAML",
    ".json": "JSON",
    ".toml": "TOML",
    ".rst": "reStructuredText",
    ".sh": "Shell",
}

_SKIP_DIRS = {"__pycache__", "node_modules", ".venv", "venv"}


def scan_languages(repo: Path) -> list[Language]:
    files: dict[str, int] = {}   # name -> file count
    locs: dict[str, int] = {}    # name -> total loc

    for path in repo.rglob("*"):
        # Skip hidden dirs and known noise dirs
        if any(
            part.startswith(".") or part in _SKIP_DIRS
            for part in path.relative_to(repo).parts[:-1]
        ):
            continue
        if not path.is_file():
            continue

        lang = _EXT_MAP.get(path.suffix.lower(), "Other")

        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue

        loc = sum(1 for line in text.splitlines() if line.strip())

        files[lang] = files.get(lang, 0) + 1
        locs[lang] = locs.get(lang, 0) + loc

    result = [
        Language(name=name, files=files[name], loc=locs[name])
        for name in files
        if locs[name] > 0
    ]
    result.sort(key=lambda lang: lang.loc, reverse=True)
    return result
