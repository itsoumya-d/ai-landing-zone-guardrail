from fastapi import FastAPI, HTTPException, status
from .models import InferenceRequest, InferenceResponse, TenantQuota, PolicyViolationException, QuotaExceededException
from .guardrail import QuotaManager
from .service import InferenceGateway

app = FastAPI(
    title="AI Landing Zone Guardrail",
    description="Enterprise policy validation, token budget enforcement, and semantic guardrail proxy",
    version="0.1.0"
)

quota_manager = QuotaManager()
gateway = InferenceGateway(quota_manager)

@app.get("/health")
def health_check():
    return {"status": "ok", "service": "ai-landing-zone-guardrail"}

@app.get("/api/v1/tenant/{tenant_id}/quota", response_model=TenantQuota)
def get_tenant_quota(tenant_id: str):
    return quota_manager.get_or_create(tenant_id)

@app.post("/api/v1/tenant/{tenant_id}/quota", response_model=TenantQuota)
def update_tenant_quota(tenant_id: str, monthly_budget_usd: float):
    quota = quota_manager.get_or_create(tenant_id, monthly_budget_usd=monthly_budget_usd)
    quota.monthly_budget_usd = monthly_budget_usd
    return quota

@app.post("/api/v1/inference/dispatch", response_model=InferenceResponse)
def dispatch_inference(request: InferenceRequest):
    try:
        return gateway.dispatch(request)
    except PolicyViolationException as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "POLICY_VIOLATION", "message": e.message}
        )
    except QuotaExceededException as e:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail={"error": "QUOTA_EXCEEDED", "message": e.message}
        )
