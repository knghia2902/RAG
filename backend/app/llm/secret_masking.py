import re

# Compiled regular expressions for egress secret redaction per SYS-03
PATTERNS = [
    # OpenAI API keys (standard and project-scoped)
    (re.compile(r"sk-[a-zA-Z0-9_\-]{20,}"), "sk-[REDACTED]"),
    # Bearer tokens
    (re.compile(r"(?i)\bBearer\s+[a-zA-Z0-9_\-\.]{16,}\b"), "Bearer [REDACTED]"),
    # Assignment of API keys, tokens, secrets, passwords
    (
        re.compile(
            r"(?i)\b(api[_\-]?key|secret|token|password|passwd|pwd|access[_\-]?key|private[_\-]?key)\s*[:=]\s*['\"]?([^\s'\";,]{8,})['\"]?"
        ),
        r"\1=[REDACTED]",
    ),
    # GitHub personal access tokens
    (re.compile(r"\b(ghp|gho|ghu|ghs|ghr)_[a-zA-Z0-9]{36}\b"), "[REDACTED_GITHUB_TOKEN]"),
    # Private key blocks
    (
        re.compile(r"-----BEGIN [A-Z ]+ PRIVATE KEY-----[\s\S]*?-----END [A-Z ]+ PRIVATE KEY-----"),
        "[REDACTED_PRIVATE_KEY]",
    ),
    # Database connection URIs with embedded credentials (e.g. postgresql://user:password@host)
    (
        re.compile(r"\b(postgresql(?:\+psycopg)?|mysql|mongodb|redis):\/\/([^:]+):([^@]+)@"),
        r"\1://\2:[REDACTED]@",
    ),
]


def mask_secrets(text: str) -> str:
    """Sanitizes sensitive tokens, credentials, and API keys before external API egress.
    Preserves text structure and technical identifiers like UUIDs and Order IDs (e.g., DH001).
    """
    if not text:
        return ""

    sanitized = text
    for pattern, replacement in PATTERNS:
        sanitized = pattern.sub(replacement, sanitized)

    return sanitized
