from fastapi import APIRouter
from app.api.routes import admin,auth,geography,health,sources,tenders,users
api_router=APIRouter(prefix="/api/v1")
for router in [health.router,auth.router,users.router,tenders.router,sources.router,geography.router,admin.router]: api_router.include_router(router)
