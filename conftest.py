"""Root conftest: add src/ to sys.path so devpilot is importable without install."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))
