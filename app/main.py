from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.api.admin import router as admin_router
from app.api.orders import router as orders_router
from app.api.webhook import router as webhook_router
from app.core.config import get_settings
from app.db.session import Base, engine

settings = get_settings()
app = FastAPI(title=settings.app_name, debug=settings.debug)

Base.metadata.create_all(bind=engine)

app.include_router(webhook_router)
app.include_router(orders_router)
app.include_router(admin_router)
app.mount("/static", StaticFiles(directory="app/static"), name="static")
app.mount("/files", StaticFiles(directory=settings.storage_path), name="files")


@app.get("/health")
def health_check():
    return {"status": "ok"}
