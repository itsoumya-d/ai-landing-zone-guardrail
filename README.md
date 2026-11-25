# AI Landing Zone Guardrail

Enterprise AI cloud landing zone policy validation, token budget enforcement, and semantic guardrail proxy built with FastAPI.

## Capabilities
- Enforces enterprise multi-tenant budget quotas across cloud landing zones.
- Automatic PII masking (emails, credit cards, SSNs/tax identifiers) prior to model dispatch.
- Detects prompt injection attempts (system override markers, delimiter jailbreaks).
- Token usage tracking, latency logging, and cost estimation per model provider.

## Testing
```bash
PYTHONPATH=. pytest -v
```
