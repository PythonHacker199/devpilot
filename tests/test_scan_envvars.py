"""Tests for devpilot.scan.envvars."""
from pathlib import Path

from devpilot.scan.envvars import scan_envvars

TINY_REPO = Path(__file__).parent / "fixtures" / "tiny_repo"


def test_single_item_returned():
    result = scan_envvars(TINY_REPO)
    assert len(result) == 1


def test_name_is_secret_key():
    result = scan_envvars(TINY_REPO)
    assert result[0].name == "SECRET_KEY"


def test_read_at_contains_app_py_line():
    result = scan_envvars(TINY_REPO)
    # app.py line 3: SECRET_KEY = os.environ["SECRET_KEY"]
    assert "app.py:3" in result[0].read_at


def test_documented_in_empty_without_env_example():
    result = scan_envvars(TINY_REPO)
    assert result[0].documented_in == []


def test_documented_in_non_empty_with_env_example(tmp_path):
    # Mirror tiny_repo into tmp_path and add a .env.example
    import shutil
    shutil.copytree(TINY_REPO, tmp_path / "repo")
    env_example = tmp_path / "repo" / ".env.example"
    env_example.write_text("SECRET_KEY=\n")

    result = scan_envvars(tmp_path / "repo")
    secret = next(e for e in result if e.name == "SECRET_KEY")
    assert len(secret.documented_in) > 0
    assert ".env.example:1" in secret.documented_in
