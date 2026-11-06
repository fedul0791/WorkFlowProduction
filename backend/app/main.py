from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes.health import router as health_router
from app.api.routes.enterprise import router as enterprise_router
from app.api.routes.auth import auth_router, admin_router
from app.api.routes.workforce import router as workforce_router
from app.api.routes.setup import router as setup_router
from app.core.config import get_settings
settings=get_settings()
app=FastAPI(title=settings.app_name,version="0.3.0",description="Enterprise, workforce and access-control API.")
origins=[origin.strip() for origin in settings.cors_origins.split(",") if origin.strip()]
app.add_middleware(CORSMiddleware,allow_origins=origins,allow_credentials=True,allow_methods=["GET","POST","PATCH","PUT","OPTIONS"],allow_headers=["Content-Type","X-CSRF-Token"])
app.include_router(health_router,tags=["health"])
app.include_router(auth_router)
app.include_router(enterprise_router)
app.include_router(workforce_router)
app.include_router(admin_router)
app.include_router(setup_router)
