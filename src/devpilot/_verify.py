"""Run CI install/test commands in an isolated venv and capture results."""
from __future__ import annotations

import json
import platform
import shutil
import subprocess
import tempfile
import time
from pathlib import Path

from devpilot.models import VerifyStep

_DENY_LIST = [
    "sudo",
    "rm -rf /",
    "curl | sh",
    "curl|sh",
    "wget | sh",
    "wget|sh",
    "bash <(",
    "eval $(",
    ":(){",
    "mkfs",
    "/dev/",
    "shutdown",
    "reboot",
]

_INSTALL_KEYWORDS = ("pip install", "npm install", "yarn install", "pnpm install", "poetry install")
_TEST_KEYWORDS = ("pytest", "npm test", "npm run test", "yarn test", "jest", "vitest")


def _is_relevant(cmd: str) -> bool:
    lower = cmd.lower()
    return any(k in lower for k in _INSTALL_KEYWORDS + _TEST_KEYWORDS)


def _is_denied(cmd: str) -> bool:
    lower = cmd.lower()
    return any(pattern.lower() in lower for pattern in _DENY_LIST)


def run_verify(repo: Path, facts_path: Path, timeout_s: int = 300) -> list[VerifyStep]:
    """Execute install and test commands from facts.json in a temporary venv."""
    data = json.loads(facts_path.read_text(encoding="utf-8"))
    ci_commands: list[dict] = data.get("ci_commands", [])

    # Filter to relevant steps
    relevant = [c for c in ci_commands if _is_relevant(c.get("run", ""))]

    tmpdir = tempfile.mkdtemp(prefix="devpilot_verify_")
    try:
        # Create isolated venv
        venv_dir = Path(tmpdir) / "venv"
        subprocess.run(
            ["python", "-m", "venv", str(venv_dir)],
            check=True,
            timeout=60,
            capture_output=True,
        )

        is_windows = platform.system() == "Windows"
        if is_windows:
            activate = f"{venv_dir / 'Scripts' / 'activate'}"
            activate_prefix = f"{activate} && "
        else:
            activate_prefix = f"source {venv_dir / 'bin' / 'activate'} && "

        steps: list[VerifyStep] = []

        for cmd_dict in relevant:
            cmd = cmd_dict.get("run", "").strip()

            if _is_denied(cmd):
                steps.append(
                    VerifyStep(
                        command=cmd,
                        exit_code=-1,
                        duration_s=0.0,
                        output_tail="[BLOCKED by deny-list]",
                        passed=False,
                    )
                )
                continue

            full_cmd = activate_prefix + cmd
            t0 = time.perf_counter()
            try:
                result = subprocess.run(
                    full_cmd,
                    shell=True,
                    cwd=repo,
                    capture_output=True,
                    text=True,
                    timeout=timeout_s,
                )
                exit_code = result.returncode
                combined = result.stdout + result.stderr
            except subprocess.TimeoutExpired as exc:
                exit_code = -1
                combined = f"[TIMEOUT after {timeout_s}s]\n" + (
                    (exc.stdout or "") + (exc.stderr or "")
                    if exc.stdout or exc.stderr
                    else ""
                )

            duration = time.perf_counter() - t0
            tail_lines = combined.splitlines()[-40:]
            output_tail = "\n".join(tail_lines)

            steps.append(
                VerifyStep(
                    command=cmd,
                    exit_code=exit_code,
                    duration_s=duration,
                    output_tail=output_tail,
                    passed=(exit_code == 0),
                )
            )

        return steps
    finally:
        shutil.rmtree(tmpdir, ignore_errors=True)
