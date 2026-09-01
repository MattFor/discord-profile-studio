import re

MASK_CHAR = "*"
MASK_WIDTH = 8

SECRET_KEYS = (
    "access_token",
    "refresh_token",
    "client_secret",
    "passphrase",
    "password",
    "secret",
    "token",
    "code",
)
'''
This is pretty interesting (painful)
These are patterns used to find secrets to be redacted

1. match discord auth header
2. match secret assignments f.e token=xyz
3. math strings that *look like* discord tokens based on format

All patterns put the secret in cap group 1 so the redaction code then knows what should be replaced
'''
PATTERNS: tuple[tuple[re.Pattern[str], int], ...] = (
    (re.compile(r"\b(?:Bot|Bearer)\s+(\S+)", re.IGNORECASE), 1),
    (
        re.compile(
            rf"(?i)\b(?:{'|'.join(SECRET_KEYS)})\b[\"']?\s*[=:]\s*[\"']?([^\s\"',&}}]+)",
        ),
        1,
    ),
    (re.compile(r"\b([\w-]{24,28}\.[\w-]{6}\.[\w-]{27,})\b"), 1),
)


def mask(secret: str, visible: int = 4) -> str:
    if not secret:
        return ""

    tail = secret[-visible:] if 0 < visible < len(secret) else ""

    return MASK_CHAR * MASK_WIDTH + tail


def _redact(match: re.Match[str], group: int) -> str:
    text = match.group(0)
    secret = match.group(group)

    if not secret:
        return text

    offset = match.start()
    start, end = match.span(group)

    return text[:start - offset] + mask(secret) + text[end - offset:]


def scrub(text: str) -> str:
    result = text

    for pattern, group in PATTERNS:
        result = pattern.sub(lambda match, index=group: _redact(match, index),
                             result)

    return result
