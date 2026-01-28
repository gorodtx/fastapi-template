from __future__ import annotations

from backend.presentation.di.container import setup_di
from backend.presentation.di.require_auth import require_auth
from backend.presentation.di.startup_checks import assert_closed_by_default

__all__: list[str] = ["assert_closed_by_default", "require_auth", "setup_di"]
