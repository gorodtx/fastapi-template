from __future__ import annotations


def normalize_email(email: str) -> str:
    # Canonicalize for storage/lookup. This template treats email as
    # case-insensitive to avoid duplicate accounts differing only by case.
    return email.strip().lower()
