from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
from .core.database import init_db
from .api import (
    auth_router,
    temples_router,
    fahui_users_router,
    fahui_records_router,
    fahui_info_router,
    printer_templates_router,
    permissions_router,
    system_logs_router,
    database_router
)
from .api.silent_print import router as silent_print_router
from .api.scanner import router as scanner_router
from .middleware.log_middleware import LogMiddleware

app = FastAPI(
    title="寺院信息管理系统",
    description="寺院信息管理系统后端API",
    version="1.0.0"
)

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    print(f"验证错误详情: {exc.errors()}")
    print(f"请求体: {exc.body}")
    return JSONResponse(
        status_code=422,
        content={"detail": exc.errors()}
    )

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_middleware(LogMiddleware)

app.include_router(auth_router)
app.include_router(temples_router)
app.include_router(fahui_users_router)
app.include_router(fahui_records_router)
app.include_router(fahui_info_router)
app.include_router(printer_templates_router)
app.include_router(permissions_router)
app.include_router(system_logs_router)
app.include_router(database_router)
app.include_router(silent_print_router)
app.include_router(scanner_router)

UPLOAD_DIR = os.environ.get("TEMPLE_UPLOAD_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "uploads"))
os.makedirs(os.path.join(UPLOAD_DIR, "templates"), exist_ok=True)
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

FRONTEND_DIST = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "frontend", "dist")
if os.path.isdir(FRONTEND_DIST):
    app.mount("/assets", StaticFiles(directory=os.path.join(FRONTEND_DIST, "assets")), name="frontend-assets")

@app.on_event("startup")
async def startup():
    await init_db()

@app.get("/")
async def root():
    return {"message": "寺院信息管理系统API", "version": "1.0.0"}

@app.get("/health")
async def health():
    return {"status": "ok"}

if os.path.isdir(FRONTEND_DIST):
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        file_path = os.path.join(FRONTEND_DIST, full_path)
        if full_path and os.path.isfile(file_path):
            return FileResponse(file_path)
        return FileResponse(os.path.join(FRONTEND_DIST, "index.html"))
