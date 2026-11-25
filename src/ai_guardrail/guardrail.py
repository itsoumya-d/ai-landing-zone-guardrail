import re
from typing import Tuple, Optional
from .models import TenantQuota, PolicyViolationException, QuotaExceededException

PII_PATTERNS = [
    (r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b", "[EMAIL_REDACTED]"),
    (r"\b(?:\d{4}[- ]?){3}\d{4}\b", "[CARD_REDACTED]"),
    (r"\b\d{3}-\d{2}-\d{4}\b", "[SSN_REDACTED]"),
]

INJECTION_PATTERNS = [
    r"ignore\s+(all\s+)?previous\s+instructions",
    r"system\s+prompt\s+override",
    r"you\s+are\s+now\s+dan",
    r"disregard\s+(all\s+)?prior\s+rules",
    r"bypass\s+safety\s+filter",
]

def mask_pii(text: str) -> Tuple[str, int]:
    masked = text
    total_redactions = 0
    for pattern, replacement in PII_PATTERNS:
        matches = len(re.findall(pattern, masked))
        if matches > 0:
            total_redactions += matches
            masked = re.sub(pattern, replacement, masked)
    return masked, total_redactions

def validate_prompt_safety(text: str) -> None:
    lower = text.lower()
    for pattern in INJECTION_PATTERNS:
        if re.search(pattern, lower):
            raise PolicyViolationException(
                message=f"Prompt injection pattern detected: '{pattern}'",
                pattern=pattern
            )

class QuotaManager:
    def __init__(self):
        self._quotas: dict[str, TenantQuota] = {}

    def get_or_create(self, tenant_id: str, monthly_budget_usd: float = 100.0) -> TenantQuota:
        if tenant_id not in self._quotas:
            self._quotas[tenant_id] = TenantQuota(
                tenant_id=tenant_id,
                monthly_budget_usd=monthly_budget_usd,
                used_budget_usd=0.0
            )
        return self._quotas[tenant_id]

    def check_and_charge(self, tenant_id: str, estimated_cost: float, requested_tokens: int) -> None:
        quota = self.get_or_create(tenant_id)
        if requested_tokens > quota.max_tokens_per_request:
            raise QuotaExceededException(
                f"Requested tokens ({requested_tokens}) exceeds tenant limit ({quota.max_tokens_per_request})"
            )
        if quota.used_budget_usd + estimated_cost > quota.monthly_budget_usd:
            raise QuotaExceededException(
                f"Tenant {tenant_id} monthly budget exceeded: ${quota.used_budget_usd:.4f} + ${estimated_cost:.4f} > ${quota.monthly_budget_usd:.2f}"
            )
        quota.used_budget_usd += estimated_cost
