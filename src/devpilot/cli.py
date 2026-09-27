"""DevPilot CLI — entry point for all commands."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Annotated

import typer

app = typer.Typer(
    name="devpilot",
    help="Turn an unfamiliar repository into a verified onboarding kit.",
    add_completion=False,
)


@app.command()
def scan(  # noqa: B008
    repo: Annotated[Path, typer.Argument(help="Path to the repository to scan")],
    output: Annotated[Path | None, typer.Option("-o", "--output", help="Output directory (default: <repo>/.devpilot)")] = None,
) -> None:
    """Scan a repository and write facts.json + findings.json."""
    from devpilot._scan import run_scan

    out_dir = output or (repo / ".devpilot")
    out_dir.mkdir(parents=True, exist_ok=True)
    facts, findings = run_scan(repo)

    import dataclasses

    (out_dir / "facts.json").write_text(
        json.dumps(dataclasses.asdict(facts), indent=2, default=str), encoding="utf-8"
    )
    (out_dir / "findings.json").write_text(
        json.dumps([dataclasses.asdict(f) for f in findings], indent=2), encoding="utf-8"
    )
    typer.echo(f"✓ Wrote {out_dir / 'facts.json'} and {out_dir / 'findings.json'}")


@app.command()
def verify(  # noqa: B008
    repo: Annotated[Path, typer.Argument(help="Path to the repository to verify")],
    output: Annotated[Path | None, typer.Option("-o", "--output", help="Output directory (default: <repo>/.devpilot)")] = None,
    timeout: Annotated[int, typer.Option(help="Per-step timeout in seconds")] = 300,
) -> None:
    """Run setup and test commands in an isolated venv and record results."""
    from devpilot._verify import run_verify

    out_dir = output or (repo / ".devpilot")
    facts_path = out_dir / "facts.json"
    if not facts_path.exists():
        typer.echo("Run 'devpilot scan' first to generate facts.json", err=True)
        raise typer.Exit(1)

    import dataclasses

    steps = run_verify(repo, facts_path, timeout_s=timeout)
    (out_dir / "verify.json").write_text(
        json.dumps([dataclasses.asdict(s) for s in steps], indent=2), encoding="utf-8"
    )
    passed = sum(1 for s in steps if s.passed)
    typer.echo(f"✓ {passed}/{len(steps)} steps passed — wrote {out_dir / 'verify.json'}")


@app.command()
def ask(  # noqa: B008
    repo: Annotated[Path, typer.Argument(help="Path to the repository to search")],
    question: Annotated[str, typer.Argument(help="Question to answer")],
    top: Annotated[int, typer.Option(help="Number of results to return")] = 5,
) -> None:
    """Answer an onboarding question using BM25 search over code and docs."""
    from devpilot._search import answer

    results = answer(repo, question, top_k=top)
    if not results:
        typer.echo("No results found.")
        return
    for i, (chunk, score) in enumerate(results, 1):
        typer.echo(f"\n[{i}] {chunk.header}  (score={score:.3f})")
        typer.echo(f"    {chunk.snippet[:200]}")


@app.command()
def report(  # noqa: B008
    repo: Annotated[Path, typer.Argument(help="Path to the repository")],
    output: Annotated[Path | None, typer.Option("-o", "--output", help="Output directory (default: <repo>/.devpilot)")] = None,
) -> None:
    """Generate report.html and ONBOARDING.md skeleton from scan + verify results."""
    from devpilot._report import render_report

    out_dir = output or (repo / ".devpilot")
    html_path, md_path = render_report(repo, out_dir)
    typer.echo(f"✓ Wrote {html_path} and {md_path}")
