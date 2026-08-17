from fastapi import APIRouter,Depends
from app.api.dependencies import require_admin
from app.models import User
router=APIRouter(prefix="/admin",tags=["admin"])
@router.get("/health")
def admin_health(admin:User=Depends(require_admin)): return {"status":"ok","admin":True,"components":{"connectors":"not_scheduled","workers":"not_configured"}}
