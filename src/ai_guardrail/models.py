from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel, Field

def utc_now() -> datetime:
    return datetime.now(timezone.utc)

class TenantQuota(BaseModel):
    tenant_id: str
    monthly_budget_usd: float = Field(default=100.0, ge=0.0)
    used_budget_usd: float = Field(default=0.0, ge=0.0)
    max_tokens_per_request: int = Field(default=4096, ge=1)

class InferenceRequest(BaseModel):
    tenant_id: str
    model: str = "gpt-4o"
    prompt: str = Field(..., min_length=1)
    max_tokens: int = Field(default=512, ge=1, le=8192)
    temperature: float = Field(default=0.7, ge=0.0, le=2.0)

class InferenceResponse(BaseModel):
    request_id: str
    tenant_id: str
    model: str
    sanitized_prompt: str
    response_text: str
    prompt_tokens: int
    completion_tokens: int
    estimated_cost_usd: float
    policy_passed: bool
    created_at: datetime = Field(default_factory=utc_now)

class PolicyViolationException(Exception):
    def __init__(self, message: str, pattern: Optional[str] = None):
        super().__init__(message)
        self.message = message
        self.pattern = pattern

class QuotaExceededException(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message
