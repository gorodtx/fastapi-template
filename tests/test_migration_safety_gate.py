from __future__ import annotations

import ast
from pathlib import Path

_VERSIONS_DIR = Path("migrations/versions")
_ALLOW_MARKER = "migration-lint: allow-nonconcurrent-index"


def _is_op_index_call(node: ast.Call) -> bool:
    func = node.func
    if not isinstance(func, ast.Attribute):
        return False
    if func.attr not in {"create_index", "drop_index"}:
        return False
    return isinstance(func.value, ast.Name) and func.value.id == "op"


def _has_concurrently_true(node: ast.Call) -> bool:
    for keyword in node.keywords:
        if keyword.arg != "postgresql_concurrently":
            continue
        value = keyword.value
        if isinstance(value, ast.Constant):
            return value.value is True
    return False


def test_non_bootstrap_index_ops_require_concurrently_flag() -> None:
    violations: list[str] = []
    for path in sorted(_VERSIONS_DIR.glob("*.py")):
        source = path.read_text(encoding="utf-8")
        if _ALLOW_MARKER in source:
            continue
        tree = ast.parse(source, filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            if not _is_op_index_call(node):
                continue
            if _has_concurrently_true(node):
                continue
            lineno = getattr(node, "lineno", 1)
            violations.append(
                f"{path}:{lineno} must set postgresql_concurrently=True"
            )

    assert not violations, "\n".join(violations)
