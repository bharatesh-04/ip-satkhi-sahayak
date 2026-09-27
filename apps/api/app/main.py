from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.api.routes import router
from app.core.config import settings

app = FastAPI(title="IP-SAKTI Sahayak API", version=settings.app_version)
allowed_origins = ["http://localhost:3000", "http://127.0.0.1:3000"]
if settings.frontend_url:
    allowed_origins.append(settings.frontend_url.rstrip("/"))

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(router)


@app.get("/")
def root():
    return {
        "name": "IP-SAKTI Sahayak",
        "version": settings.app_version,
        "demo_mode": settings.demo_mode,
        "disclaimer": "Information only; not legal advice.",
    }
