from __future__ import annotations

import sys
from pathlib import Path


def pytest_configure() -> None:
    # Project uses a src/ layout and is not installed as a package.
    # Add src/ to sys.path so tests can import `backend.*`.
    src_dir = Path(__file__).resolve().parent.parent / "src"
    sys.path.insert(0, str(src_dir))
