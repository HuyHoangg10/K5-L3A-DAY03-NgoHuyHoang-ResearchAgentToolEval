from __future__ import annotations

from typing import Any
from urllib.parse import urlparse


SHORTENER_DOMAINS = {"bit.ly", "tinyurl.com", "t.co", "goo.gl", "ow.ly"}


def inspect_source(url: str = "") -> dict[str, Any]:
    """Inspect URL metadata and obvious risk signals without fetching the page."""
    if not isinstance(url, str) or not url.strip():
        return {
            "tool": "inspect_source",
            "error": "invalid_input",
            "message": "url must be a non-empty string",
        }

    normalized = url.strip()
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        return {
            "tool": "inspect_source",
            "error": "invalid_url",
            "message": "url must be an absolute http or https URL",
        }

    domain = parsed.hostname.lower().removeprefix("www.")
    flags: list[str] = []
    if parsed.scheme != "https":
        flags.append("unencrypted_http")
    if domain in SHORTENER_DOMAINS:
        flags.append("shortened_url_hides_destination")
    if parsed.username or parsed.password:
        flags.append("credentials_embedded_in_url")

    if domain.endswith(".gov") or ".gov." in domain:
        source_type = "government"
    elif domain.endswith(".edu") or ".edu." in domain:
        source_type = "education"
    elif domain == "arxiv.org" or domain.endswith(".arxiv.org"):
        source_type = "academic_repository"
    else:
        source_type = "general_web"

    return {
        "tool": "inspect_source",
        "url": normalized,
        "domain": domain,
        "uses_https": parsed.scheme == "https",
        "source_type": source_type,
        "risk_flags": flags,
        "note": "Metadata and red flags only; this is not a factuality verdict.",
    }
