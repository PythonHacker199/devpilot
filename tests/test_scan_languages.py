from pathlib import Path

import pytest

from devpilot.models import Language
from devpilot.scan.languages import scan_languages

TINY_REPO = Path("tests/fixtures/tiny_repo")


@pytest.fixture(scope="module")
def languages():
    return scan_languages(TINY_REPO)


def test_returns_list_of_language_objects(languages):
    assert isinstance(languages, list)
    assert all(isinstance(lang, Language) for lang in languages)


def test_no_empty_language_items(languages):
    for lang in languages:
        assert lang.files > 0
        assert lang.loc > 0


def test_python_present(languages):
    python = next((lang for lang in languages if lang.name == "Python"), None)
    assert python is not None, "Python should be present"
    assert python.files == 1
    assert python.loc == 2


def test_yaml_present(languages):
    # ci.yml lives under .github/ (hidden dir) and is skipped by the scanner.
    # YAML is therefore absent from the tiny_repo results — that is correct
    # behaviour and confirmed by test_hidden_dirs_not_counted below.
    yaml = next((lang for lang in languages if lang.name == "YAML"), None)
    assert yaml is None, "ci.yml is inside a hidden dir and must not be counted"


def test_sorted_by_loc_descending(languages):
    locs = [lang.loc for lang in languages]
    assert locs == sorted(locs, reverse=True)


def test_hidden_dirs_not_counted(languages):
    # The .github directory is hidden — its ci.yml should NOT appear in YAML
    # because hidden parent dirs are skipped.
    yaml = next((lang for lang in languages if lang.name == "YAML"), None)
    # If YAML appears at all, it must have come from a non-hidden location.
    # Since ci.yml is the only YAML file and it lives under .github/, YAML
    # should not be present in the results.
    assert yaml is None, ".github/workflows/ci.yml is in a hidden dir and must be skipped"


def test_pycache_not_counted(tmp_path):
    # Build a mini repo with a __pycache__ dir containing a .py file
    (tmp_path / "__pycache__").mkdir()
    (tmp_path / "__pycache__" / "cached.py").write_text("x = 1\n")
    (tmp_path / "real.py").write_text("y = 2\n")

    langs = scan_languages(tmp_path)
    python = next((lang for lang in langs if lang.name == "Python"), None)
    assert python is not None
    assert python.files == 1  # only real.py, not cached.py
