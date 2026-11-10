---
name: inspect_source
track: core
kind: local_knowledge
provider: local URL rules
requires_env: []
inputs: [url]
outputs: [domain, uses_https, source_type, risk_flags, note]
side_effect: false
---
# inspect_source

Inspects the structure of one URL without fetching it. It reports the domain,
HTTPS status, a broad source type, and obvious URL-level warning signals.

This is a preliminary source check, not a fact-checker and not proof that the
page is trustworthy. Use `fetch` when the user wants the page content.
