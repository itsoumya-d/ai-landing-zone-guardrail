import uuid
from typing import Dict
from .models import InferenceRequest, InferenceResponse
from .guardrail import mask_pii, validate_prompt_safety, QuotaManager

# Base pricing per 1,000 tokens
MODEL_PRICING: Dict[str, Dict[str, float]] = {
    "gpt-4o": {"prompt": 0.005, "completion": 0.015},
    "claude-3-5-sonnet": {"prompt": 0.003, "completion": 0.015},
    "default": {"prompt": 0.002, "completion": 0.008},
}

class InferenceGateway:
    def __init__(self, quota_manager: QuotaManager):
        self.quota_manager = quota_manager

    def estimate_cost(self, model: str, prompt_tokens: int, completion_tokens: int) -> float:
        pricing = MODEL_PRICING.get(model, MODEL_PRICING["default"])
        cost = (prompt_tokens / 1000.0) * pricing["prompt"] + (completion_tokens / 1000.0) * pricing["completion"]
        return round(cost, 6)

    def dispatch(self, request: InferenceRequest) -> InferenceResponse:
        # 1. Semantic guardrail validation
        validate_prompt_safety(request.prompt)

        # 2. PII masking
        sanitized_prompt, _ = mask_pii(request.prompt)

        # 3. Rough token estimation (approx 4 chars per token)
        est_prompt_tokens = max(1, len(sanitized_prompt) // 4)
        est_completion_tokens = min(request.max_tokens, 128)
        estimated_cost = self.estimate_cost(request.model, est_prompt_tokens, est_completion_tokens)

        # 4. Quota check & deduction
        self.quota_manager.check_and_charge(request.tenant_id, estimated_cost, request.max_tokens)

        # 5. Model execution simulation
        req_id = f"inf-{uuid.uuid4().hex[:10]}"
        simulated_response = f"Processed response for [{request.model}] with prompt length {len(sanitized_prompt)} chars."

        return InferenceResponse(
            request_id=req_id,
            tenant_id=request.tenant_id,
            model=request.model,
            sanitized_prompt=sanitized_prompt,
            response_text=simulated_response,
            prompt_tokens=est_prompt_tokens,
            completion_tokens=est_completion_tokens,
            estimated_cost_usd=estimated_cost,
            policy_passed=True
        )
