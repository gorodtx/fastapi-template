from __future__ import annotations

import re


class RawPasswordValidator:
    @staticmethod
    def validate(raw_password: str) -> None:
        """Validate raw password against OWASP/NIST requirements.

        Raises ValueError with descriptive message if invalid.
        """
        if len(raw_password) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(raw_password) > 128:
            raise ValueError("Password too long (max 128 characters)")

        if not re.search(r"[A-Z]", raw_password):
            raise ValueError("Password must include at least one uppercase letter")
        if not re.search(r"[a-z]", raw_password):
            raise ValueError("Password must include at least one lowercase letter")
        if not re.search(r"\d", raw_password):
            raise ValueError("Password must include at least one digit")
        if not re.search(r"[^A-Za-z0-9]", raw_password):
            raise ValueError("Password must include at least one special character")
        if re.search(r"(.)\1{2,}", raw_password):
            raise ValueError("Password contains too many repeated characters")
