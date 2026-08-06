import sys
import os
import time
import socket
import threading
import traceback
import webbrowser
import json
import asyncio
import shutil
from pathlib import Path
import ctypes
import tempfile

LOG_FILE = Path(tempfile.gettempdir()) / "temple_management.log"

def log_message(msg):
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} - {msg}\n")
            f.flush()
    except:
        pass

log_message("=" * 50)
log_message("程序启动")
log_message(f"sys.frozen: {getattr(sys, 'frozen', False)}")
log_message(f"sys._MEIPASS: {getattr(sys, '_MEIPASS', 'N/A')}")
log_message(f"sys.executable: {sys.executable}")
log_message(f"sys.argv: {sys.argv}")

def get_base_path():
    if getattr(sys, 'frozen', False):
        return Path(sys._MEIPASS)
    return Path(__file__).parent

def get_data_path():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    return Path(__file__).parent

def load_config():
    data_path = get_data_path()
    config_path = data_path / "config.json"
    default_config = {
        "temple_name": "默认寺院",
        "temple_address": "",
        "admin_username": "admin",
        "admin_password": "admin123",
        "admin_real_name": "管理员",
        "port": 8080
    }
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                custom_config = json.load(f)
            return {**default_config, **custom_config}
        except Exception as e:
            log_message(f"加载配置文件失败，使用默认配置: {e}")
    return default_config

BASE_PATH = get_base_path()
DATA_PATH = get_data_path()
CONFIG = load_config()
FRONTEND_DIST = BASE_PATH / "frontend" / "dist"
UPLOAD_DIR = DATA_PATH / "uploads"
DB_DIR = DATA_PATH / "database"
DB_PATH = DB_DIR / "temple.db"

def load_build_version():
    build_info_path = BASE_PATH / "build_info.json"
    if build_info_path.exists():
        try:
            with open(build_info_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            version = data.get("version", "")
            commit = data.get("git_commit", "")[:8]
            branch = data.get("git_branch", "")
            if version and commit:
                return f"v{version} ({commit}) [{branch}]"
            elif commit:
                return f"commit:{commit} [{branch}]"
        except Exception:
            pass
    return ""

BUILD_VERSION = load_build_version()

log_message(f"BASE_PATH: {BASE_PATH}")
log_message(f"DATA_PATH: {DATA_PATH}")
log_message(f"FRONTEND_DIST: {FRONTEND_DIST}")
log_message(f"UPLOAD_DIR: {UPLOAD_DIR}")
log_message(f"DB_PATH: {DB_PATH}")
log_message(f"配置信息 - 寺院名称: {CONFIG['temple_name']}")
log_message(f"配置信息 - 监听端口: {CONFIG['port']}")

DB_DIR.mkdir(parents=True, exist_ok=True)
os.makedirs(os.path.join(str(UPLOAD_DIR), "templates"), exist_ok=True)

BUILTIN_TEMPLATES = BASE_PATH / "uploads" / "templates"
EXTERNAL_TEMPLATES = UPLOAD_DIR / "templates"

os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{DB_PATH}"
os.environ["TEMPLE_UPLOAD_DIR"] = str(UPLOAD_DIR)
os.environ["TEMPLE_DB_PATH"] = str(DB_PATH)
os.environ["TEMPLE_BACKUP_DIR"] = str(DATA_PATH / "backups")

sys.path.insert(0, str(BASE_PATH / "backend"))

# 注册同步状态模块，供 backend/app/middleware/log_middleware.py 标记数据库写入
# 必须在 import FastAPI 模块之前注册，LogMiddleware 加载时才能 import 到
import types as _types
_sync_state = _types.ModuleType('temple_sync_state')
_sync_state.dirty_time = None        # 最后一次写操作时间戳
_sync_state.last_sync_time = 0.0    # 最后一次同步完成时间戳
_sync_state.lock = threading.Lock()
sys.modules['temple_sync_state'] = _sync_state
log_message("已注册 temple_sync_state 共享状态模块")

def _mark_dirty():
    """标记数据库有写入，待 watcher 线程 debounce 后同步"""
    with _sync_state.lock:
        _sync_state.dirty_time = time.time()

def _should_sync(debounce_sec=5):
    """判断是否需要同步：有写入标记且距最后一次写入超过 debounce_sec 秒"""
    with _sync_state.lock:
        if _sync_state.dirty_time is None:
            return False
        if time.time() - _sync_state.dirty_time < debounce_sec:
            return False
        if _sync_state.last_sync_time >= _sync_state.dirty_time:
            return False
        return True

def _mark_synced():
    with _sync_state.lock:
        _sync_state.last_sync_time = time.time()
        _sync_state.dirty_time = None

try:
    log_message("开始导入 FastAPI 模块...")

    from fastapi import FastAPI, Request
    from fastapi.middleware.cors import CORSMiddleware
    from fastapi.responses import Response, FileResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.exceptions import RequestValidationError
    from fastapi.responses import JSONResponse

    from app.core.database import init_db
    from app.api import (
        auth_router,
        temples_router,
        fahui_users_router,
        fahui_records_router,
        fahui_info_router,
        printer_templates_router,
        permissions_router,
        system_logs_router,
        database_router,
        version_info_router
    )
    from app.api.silent_print import router as silent_print_router
    from app.api.scanner import router as scanner_router
    from app.middleware.log_middleware import LogMiddleware

    log_message("FastAPI 模块加载完成")

    app = FastAPI(
        title="缘通寺院信息管理系统",
        version="1.0.0",
        docs_url=None,
        redoc_url=None
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
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
    app.include_router(version_info_router)
    app.include_router(silent_print_router)
    app.include_router(scanner_router)

    if FRONTEND_DIST.exists() and (FRONTEND_DIST / "assets").is_dir():
        try:
            app.mount("/assets", StaticFiles(directory=str(FRONTEND_DIST / "assets")), name="frontend-assets")
            log_message("前端静态资源挂载成功")
        except Exception as e:
            log_message(f"Warning: Could not mount assets: {e}")

    try:
        app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")
        log_message("uploads 目录挂载成功")
    except Exception as e:
        log_message(f"Warning: Could not mount uploads: {e}")

    log_message(f"Frontend exists: {FRONTEND_DIST.exists()}")

except Exception as e:
    log_message(f"初始化失败: {e}")
    traceback.print_exc()
    sys.exit(1)

def _try_read_file(path):
    try:
        with open(path, 'rb') as f:
            return f.read()
    except Exception:
        return None

def _serve_html(content):
    return Response(content=content, media_type="text/html; charset=utf-8")

def _serve_asset(path, content):
    if path.endswith('.js'):
        mt = "application/javascript; charset=utf-8"
    elif path.endswith('.css'):
        mt = "text/css; charset=utf-8"
    elif path.endswith('.html'):
        mt = "text/html; charset=utf-8"
    elif path.endswith('.svg'):
        mt = "image/svg+xml"
    elif path.endswith('.png'):
        mt = "image/png"
    elif path.endswith('.ico'):
        mt = "image/x-icon"
    elif path.endswith('.jpeg') or path.endswith('.jpg'):
        mt = "image/jpeg"
    else:
        mt = "application/octet-stream"
    return Response(content=content, media_type=mt)

@app.on_event("startup")
async def startup():
    await init_db()
    await _create_default_data()
    await _migrate_data()
    await _import_build_info()

async def _create_default_data():
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        import bcrypt

        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM temples"))
            count = result.scalar()
            if count > 0:
                log_message("数据库已有数据，跳过默认数据创建")
                return

            log_message("首次启动，创建默认数据...")

            from datetime import datetime
            now = datetime.now().isoformat()

            temple_name = CONFIG.get("temple_name", "默认寺庙")
            temple_address = CONFIG.get("temple_address", "")
            admin_username = CONFIG.get("admin_username", "admin")
            admin_password = CONFIG.get("admin_password", "")
            admin_real_name = CONFIG.get("admin_real_name", "管理员")

            if not admin_password:
                import secrets
                import string
                admin_password = ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(10))
                log_message(f"自动生成管理员密码: {admin_password} (请妥善保管，此信息仅出现在本次启动日志中)")
            else:
                log_message(f"使用配置文件中指定的管理员密码")

            await session.execute(text(
                "INSERT INTO temples (寺庙名称, 寺庙地址, created_at, updated_at) "
                "VALUES (:name, :address, :now, :now)"
            ), {"name": temple_name, "address": temple_address, "now": now})

            result = await session.execute(text("SELECT last_insert_rowid()"))
            temple_id = result.scalar()

            password_hash = bcrypt.hashpw(admin_password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
            await session.execute(text(
                "INSERT INTO users (username, password_hash, real_name, role, is_active, temple_id, created_at, updated_at) "
                "VALUES (:username, :pw, :real_name, '管理员', 1, :tid, :now, :now)"
            ), {"username": admin_username, "pw": password_hash, "real_name": admin_real_name, "tid": temple_id, "now": now})

            default_permissions = [
                ('query', '查询', '查询法会和施主信息'),
                ('shizhu', '施主管理', '管理施主信息'),
                ('fahui', '法会管理', '管理法会信息和登记'),
                ('print', '打印管理', '打印牌位'),
                ('print_template', '打印模板', '管理打印模板'),
                ('system', '系统管理', '系统设置和用户管理')
            ]
            for name, display_name, description in default_permissions:
                await session.execute(text(
                    "INSERT INTO permissions (name, display_name, description, created_at) "
                    "VALUES (:name, :display_name, :desc, :now)"
                ), {"name": name, "display_name": display_name, "desc": description, "now": now})

            await session.commit()
            log_message(f"默认数据创建成功 - 寺院: {temple_name}, 管理员: {admin_username}")
            _clear_config_password()
    except Exception as e:
        log_message(f"创建默认数据失败: {e}")
        traceback.print_exc()

def _clear_config_password():
    try:
        config_path = DATA_PATH / "config.json"
        if config_path.exists():
            with open(config_path, 'r', encoding='utf-8') as f:
                cfg = json.load(f)
            if cfg.get("admin_password"):
                cfg["admin_password"] = ""
                with open(config_path, 'w', encoding='utf-8') as f:
                    json.dump(cfg, f, ensure_ascii=False, indent=2)
                log_message("已清除 config.json 中的明文密码")
    except Exception as e:
        log_message(f"清除配置密码失败: {e}")

async def _migrate_data():
    try:
        from app.core.database import AsyncSessionLocal
        from sqlalchemy import text
        from datetime import datetime

        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT COUNT(*) FROM permissions WHERE name = 'print_template'"))
            if result.scalar() == 0:
                now = datetime.now().isoformat()
                await session.execute(text(
                    "INSERT INTO permissions (name, display_name, description, created_at) "
                    "VALUES ('print_template', '打印模板', '管理打印模板', :now)"
                ), {"now": now})
                await session.commit()
                log_message("已添加 print_template 权限")

            result = await session.execute(text(
                "SELECT id, permissions FROM users WHERE role = '普通用户' AND is_active = 1"
            ))
            users = result.fetchall()
            for user_id, perms in users:
                if not perms:
                    new_perms = "query,print_template"
                else:
                    perm_list = [p.strip() for p in perms.split(",") if p.strip()]
                    if "print_template" not in perm_list:
                        perm_list.append("print_template")
                    new_perms = ",".join(perm_list)
                await session.execute(text(
                    "UPDATE users SET permissions = :perms WHERE id = :uid"
                ), {"perms": new_perms, "uid": user_id})
            await session.commit()
            if users:
                log_message(f"已为 {len(users)} 个普通用户添加 print_template 权限")
    except Exception as e:
        log_message(f"数据迁移失败: {e}")
        traceback.print_exc()

async def _import_build_info():
    try:
        build_info_path = BASE_PATH / "build_info.json"
        if not build_info_path.exists():
            log_message("未找到 build_info.json，跳过版本信息导入")
            return

        with open(build_info_path, 'r', encoding='utf-8') as f:
            build_data = json.load(f)

        git_commit = build_data.get("git_commit", "")
        if not git_commit or git_commit == "unknown":
            log_message("构建信息中无有效 git commit，跳过版本信息导入")
            return

        from app.core.database import AsyncSessionLocal
        from app.models.version_info import VersionInfo
        from sqlalchemy import select

        async with AsyncSessionLocal() as session:
            result = await session.execute(
                select(VersionInfo).where(VersionInfo.git_commit == git_commit)
            )
            existing = result.scalar_one_or_none()
            if existing:
                log_message(f"版本信息已存在 (commit: {git_commit[:8]})，跳过导入")
                return

            version = VersionInfo(
                version=build_data.get("version", ""),
                git_commit=git_commit,
                git_branch=build_data.get("git_branch", ""),
                git_author=build_data.get("git_author", ""),
                git_message=build_data.get("git_message", ""),
                git_date=build_data.get("git_date", ""),
                change_summary=build_data.get("change_summary", ""),
            )
            session.add(version)
            await session.commit()
            log_message(f"版本信息导入成功: {build_data.get('version', '')} (commit: {git_commit[:8]})")
    except Exception as e:
        log_message(f"导入版本信息失败: {e}")
        traceback.print_exc()

@app.get("/")
async def serve_index():
    index_path = FRONTEND_DIST / "index.html"
    content = _try_read_file(index_path)
    if content is not None:
        return _serve_html(content)
    return {"message": "API running", "frontend_dist": str(FRONTEND_DIST), "exists": FRONTEND_DIST.exists()}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.api_route("/{path:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS", "HEAD"])
async def catch_all(request: Request, path: str):
    if path.startswith("api/"):
        return {"error": "API endpoint not found"}

    if path.startswith("uploads/"):
        file_path = UPLOAD_DIR / path[len("uploads/"):]
        if file_path.is_file():
            return FileResponse(str(file_path))

    file_path = FRONTEND_DIST / path
    content = _try_read_file(file_path)
    if content is not None:
        return _serve_asset(path, content)

    index_path = FRONTEND_DIST / "index.html"
    content = _try_read_file(index_path)
    if content is not None:
        return _serve_html(content)

    return {"error": "Not found", "path": path}

def find_free_port():
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('127.0.0.1', 0))
        return s.getsockname()[1]

def is_port_available(port):
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.bind(('0.0.0.0', port))
            return True
    except OSError:
        return False

def wait_for_server(url, timeout=60):
    import urllib.request
    start_time = time.time()
    while time.time() - start_time < timeout:
        try:
            urllib.request.urlopen(url, timeout=2)
            return True
        except Exception as e:
            log_message(f"等待服务器... {e}")
            time.sleep(0.5)
    return False

_server_started = threading.Event()
_server_error = [None]

_server_port = [CONFIG['port']]

def run_server():
    import uvicorn
    import logging

    try:
        if sys.platform == 'win32':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
            log_message("已设置 WindowsSelectorEventLoopPolicy")

        log_handler = logging.FileHandler(str(LOG_FILE), encoding='utf-8')
        log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        uvicorn_logger = logging.getLogger("uvicorn")
        uvicorn_logger.setLevel(logging.INFO)
        uvicorn_logger.addHandler(log_handler)

        uvicorn_error_logger = logging.getLogger("uvicorn.error")
        uvicorn_error_logger.setLevel(logging.INFO)
        uvicorn_error_logger.addHandler(log_handler)

        uvicorn_access_logger = logging.getLogger("uvicorn.access")
        uvicorn_access_logger.setLevel(logging.INFO)
        uvicorn_access_logger.addHandler(log_handler)

        port = _server_port[0]
        log_message(f"uvicorn.run 开始, host=0.0.0.0, port={port}, http=h11")
        uvicorn.run(
            app,
            host="0.0.0.0",
            port=port,
            log_level="info",
            log_config=None,
            http="h11",
        )
    except Exception as e:
        _server_error[0] = e
        log_message(f"uvicorn 运行错误: {e}")
        traceback.print_exc()
        _server_started.set()

def get_local_ip():
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(("8.8.8.8", 80))
            return s.getsockname()[0]
    except:
        return "127.0.0.1"

def create_tray_icon(url, show_window_callback, root):
    import pystray
    from PIL import Image

    def create_icon_image():
        icon_path = BASE_PATH / "yuantong_logo.ico"
        if icon_path.exists():
            try:
                img = Image.open(str(icon_path))
                img = img.convert('RGBA')
                img = img.resize((64, 64), Image.Resampling.LANCZOS)
                return img
            except Exception as e:
                log_message(f"加载托盘图标失败: {e}")
        from PIL import ImageDraw
        img = Image.new('RGBA', (64, 64), color=(0, 0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse([8, 8, 56, 56], fill='#4CAF50', outline='#2E7D32', width=2)
        return img

    def on_show(icon, item):
        root.after(0, show_window_callback)

    def on_open_browser(icon, item):
        webbrowser.open(url)

    def on_exit(icon, item):
        log_message("用户从托盘退出")
        final_sync()
        icon.stop()
        os._exit(0)

    tray_tooltip = "缘通寺院信息管理系统"
    if BUILD_VERSION:
        tray_tooltip = f"缘通寺院信息管理系统 {BUILD_VERSION}"

    icon = pystray.Icon(
        "temple_management",
        create_icon_image(),
        tray_tooltip,
        menu=pystray.Menu(
            pystray.MenuItem("显示窗口", on_show, default=True),
            pystray.MenuItem("打开浏览器", on_open_browser),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("退出", on_exit),
        )
    )
    return icon

def show_control_window(url):
    import tkinter as tk
    from tkinter import ttk
    import pystray

    root = tk.Tk()
    root.title("缘通寺院信息管理系统")
    root.geometry("360x250")
    root.resizable(False, False)
    root.configure(bg="#f5f5f5")

    try:
        icon_path = BASE_PATH / "yuantong_logo.ico"
        if icon_path.exists():
            root.iconbitmap(str(icon_path))
    except:
        pass

    frame = tk.Frame(root, bg="#f5f5f5", padx=20, pady=15)
    frame.pack(fill="both", expand=True)

    tk.Label(frame, text="缘通寺院信息管理系统", font=("Microsoft YaHei", 14, "bold"), bg="#f5f5f5", fg="#333").pack(pady=(0, 5))

    if BUILD_VERSION:
        tk.Label(frame, text=BUILD_VERSION, font=("Microsoft YaHei", 9), bg="#f5f5f5", fg="#999").pack(pady=(0, 5))

    tk.Label(frame, text=f"访问地址: {url}", font=("Microsoft YaHei", 9), bg="#f5f5f5", fg="#666").pack(pady=(2, 10))

    def open_browser():
        webbrowser.open(url)

    def exit_app():
        log_message("用户点击退出")
        final_sync()
        if tray_icon:
            tray_icon.stop()
        os._exit(0)

    def hide_to_tray():
        root.withdraw()
        if tray_icon and not tray_icon.visible:
            threading.Thread(target=tray_icon.run, daemon=True).start()

    def show_window():
        root.deiconify()

    btn_frame = tk.Frame(frame, bg="#f5f5f5")
    btn_frame.pack(pady=5)

    ttk.Button(btn_frame, text="打开浏览器", command=open_browser).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="隐藏到托盘", command=hide_to_tray).pack(side="left", padx=5)
    ttk.Button(btn_frame, text="退出", command=exit_app).pack(side="left", padx=5)

    tray_icon = create_tray_icon(url, show_window, root)

    def on_close():
        hide_to_tray()

    root.protocol("WM_DELETE_WINDOW", on_close)
    root.mainloop()

def _get_system_backup_root():
    """返回系统目录镜像备份根路径 (%LOCALAPPDATA%\\TempleManagement\\backup)。"""
    local_app_data = os.environ.get("LOCALAPPDATA")
    if not local_app_data:
        return None
    return Path(local_app_data) / "TempleManagement" / "backup"

def _restore_from_system_dir():
    """启动时若本地 database 或 uploads 缺失（升级覆盖/误删），从系统目录镜像恢复。

    - 仅当本地缺失时才恢复，不会覆盖已存在的本地文件
    - 数据库恢复后会继续走 init_db 流程（如果系统目录也没有备份，则首次启动初始化）
    - 在服务器线程启动之前调用，避免数据库并发访问
    返回 True 表示执行过恢复操作，False 表示未恢复。
    """
    try:
        backup_root = _get_system_backup_root()
        if not backup_root:
            log_message("未找到 LOCALAPPDATA 环境变量，跳过系统目录恢复检查")
            return False

        backup_db_path = backup_root / "database" / "temple.db"
        backup_uploads_dir = backup_root / "uploads"

        restored_something = False

        # 1. 数据库恢复：本地缺失但系统目录有备份
        if not DB_PATH.exists():
            if backup_db_path.exists():
                DB_DIR.mkdir(parents=True, exist_ok=True)
                shutil.copy2(backup_db_path, DB_PATH)
                log_message(f"⚠ 本地数据库缺失，已从系统目录恢复: {backup_db_path} → {DB_PATH}")
                restored_something = True
            else:
                log_message("本地数据库缺失，但系统目录无备份，将走首次启动初始化流程")
        else:
            log_message("本地数据库存在，跳过恢复检查")

        # 2. uploads 恢复：本地目录缺失或为空，但系统目录有备份
        local_uploads_empty = (not UPLOAD_DIR.exists()) or not any(UPLOAD_DIR.rglob("*"))
        backup_uploads_has_files = backup_uploads_dir.exists() and any(backup_uploads_dir.rglob("*"))

        if local_uploads_empty and backup_uploads_has_files:
            UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
            restored = 0
            for src_file in backup_uploads_dir.rglob("*"):
                if not src_file.is_file():
                    continue
                rel = src_file.relative_to(backup_uploads_dir)
                dst_file = UPLOAD_DIR / rel
                dst_file.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src_file, dst_file)
                restored += 1
            log_message(f"⚠ 本地 uploads 缺失，已从系统目录恢复 {restored} 个文件")
            restored_something = True
        elif local_uploads_empty:
            log_message("本地 uploads 缺失，但系统目录无备份，跳过恢复")
        else:
            log_message("本地 uploads 存在，跳过恢复检查")

        return restored_something
    except Exception as e:
        log_message(f"从系统目录恢复失败: {e}")
        traceback.print_exc()
        return False

def _backup_database_to(backup_db_path):
    """使用 sqlite3.backup() 在线热备份数据库，确保数据一致性。

    相比 shutil.copy2，sqlite3.backup() 能在数据库被 uvicorn 占用时安全复制，
    不会拿到中间状态的不一致快照。
    """
    import sqlite3
    backup_db_path.parent.mkdir(parents=True, exist_ok=True)
    source = sqlite3.connect(str(DB_PATH))
    try:
        dest = sqlite3.connect(str(backup_db_path))
        try:
            source.backup(dest)
        finally:
            dest.close()
    finally:
        source.close()

def _mirror_to_system_dir():
    """把本地 database 和 uploads 镜像备份到系统目录。

    - 数据库使用 sqlite3.backup() 在线热备份，运行时也安全
    - uploads 目录递归镜像，仅复制新增或修改过的文件
    """
    try:
        backup_root = _get_system_backup_root()
        if not backup_root:
            log_message("未找到 LOCALAPPDATA 环境变量，跳过系统目录镜像备份")
            return

        backup_db_dir = backup_root / "database"
        backup_uploads_dir = backup_root / "uploads"

        backup_root.mkdir(parents=True, exist_ok=True)
        backup_db_dir.mkdir(parents=True, exist_ok=True)

        # 1. 镜像数据库文件
        if DB_PATH.exists():
            backup_db_path = backup_db_dir / "temple.db"
            need_copy = True
            if backup_db_path.exists():
                if DB_PATH.stat().st_mtime <= backup_db_path.stat().st_mtime:
                    need_copy = False
            if need_copy:
                _backup_database_to(backup_db_path)
                log_message(f"数据库已镜像到系统目录: {backup_db_path}")
            else:
                log_message("数据库未变化，跳过系统目录镜像")
        else:
            log_message("数据库文件不存在，跳过镜像")

        # 2. 镜像 uploads 目录
        if UPLOAD_DIR.exists():
            backup_uploads_dir.mkdir(parents=True, exist_ok=True)
            copied = 0
            skipped = 0
            for src_file in UPLOAD_DIR.rglob("*"):
                if not src_file.is_file():
                    continue
                rel = src_file.relative_to(UPLOAD_DIR)
                dst_file = backup_uploads_dir / rel
                dst_file.parent.mkdir(parents=True, exist_ok=True)

                need_copy = True
                if dst_file.exists():
                    if src_file.stat().st_mtime <= dst_file.stat().st_mtime:
                        need_copy = False
                if need_copy:
                    shutil.copy2(src_file, dst_file)
                    copied += 1
                else:
                    skipped += 1
            log_message(f"uploads 镜像完成: 复制 {copied} 个文件, 跳过 {skipped} 个未变化文件")
        else:
            log_message("uploads 目录不存在，跳过镜像")

        log_message(f"系统目录镜像备份完成: {backup_root}")
    except Exception as e:
        log_message(f"系统目录镜像备份失败: {e}")
        traceback.print_exc()

def do_incremental_sync():
    """事件驱动的增量同步：数据库用 sqlite3.backup()，uploads 用 mtime 增量。

    与 _mirror_to_system_dir 的区别：
    - 数据库不做 mtime 检测，每次都执行 sqlite3.backup()（开销低，SQLite 官方推荐方式）
    - uploads 仍按 mtime 增量
    - 适用于运行中被 watcher 线程调用的场景

    返回 (db_synced: bool, uploads_copied: int)
    """
    backup_root = _get_system_backup_root()
    if not backup_root:
        return False, 0

    backup_db_dir = backup_root / "database"
    backup_db_path = backup_db_dir / "temple.db"
    backup_uploads_dir = backup_root / "uploads"

    backup_db_dir.mkdir(parents=True, exist_ok=True)

    db_synced = False
    uploads_copied = 0

    # 1. 数据库热备份
    try:
        if DB_PATH.exists():
            _backup_database_to(backup_db_path)
            db_synced = True
            log_message(f"数据库已增量同步到: {backup_db_path}")
    except Exception as e:
        log_message(f"数据库增量同步失败: {e}")

    # 2. uploads 增量
    try:
        if UPLOAD_DIR.exists():
            backup_uploads_dir.mkdir(parents=True, exist_ok=True)
            for src_file in UPLOAD_DIR.rglob("*"):
                if not src_file.is_file():
                    continue
                rel = src_file.relative_to(UPLOAD_DIR)
                dst_file = backup_uploads_dir / rel
                dst_file.parent.mkdir(parents=True, exist_ok=True)

                need_copy = True
                if dst_file.exists():
                    if src_file.stat().st_mtime <= dst_file.stat().st_mtime:
                        need_copy = False
                if need_copy:
                    shutil.copy2(src_file, dst_file)
                    uploads_copied += 1
    except Exception as e:
        log_message(f"uploads 增量同步失败: {e}")

    return db_synced, uploads_copied

def sync_watcher():
    """后台 watcher 线程：检测写操作并 debounce 60 秒后执行增量同步。

    - 每 30 秒检查一次 temple_sync_state.dirty_time
    - 距最后一次写入超过 60 秒才同步（debounce，避免连续写入时频繁同步）
    - 同步完成后清空 dirty_time 标记
    """
    log_message("数据同步 watcher 线程已启动 (debounce=60s, check_interval=30s)")
    while True:
        try:
            time.sleep(30)
            if _should_sync(debounce_sec=60):
                log_message("检测到数据变化，开始增量同步...")
                db_synced, uploads_copied = do_incremental_sync()
                _mark_synced()
                if db_synced or uploads_copied > 0:
                    log_message(f"增量同步完成: 数据库={db_synced}, uploads 新增 {uploads_copied} 个文件")
                else:
                    log_message("增量同步完成: 无变化")
        except Exception as e:
            log_message(f"sync_watcher 错误: {e}")

def final_sync():
    """程序退出前强制同步一次，确保最新数据已备份。

    即使 dirty_time 为 None 也执行（兜底）：可能有写入还没被中间件捕获到。
    """
    try:
        log_message("退出前执行最终同步...")
        db_synced, uploads_copied = do_incremental_sync()
        _mark_synced()
        log_message(f"最终同步完成: 数据库={db_synced}, uploads 新增 {uploads_copied} 个文件")
    except Exception as e:
        log_message(f"最终同步失败: {e}")
        traceback.print_exc()

def sync_with_system_dir():
    """启动时同步本地与系统目录：先恢复（本地缺失时），再镜像（保存当前状态）。

    完整流程：
    1. 若本地 database/uploads 缺失（升级覆盖/误删），从系统目录恢复
    2. 然后把当前本地状态镜像到系统目录（保证下次启动的备份是最新的）
    """
    log_message("开始系统目录同步...")
    restored = _restore_from_system_dir()
    if restored:
        log_message("已从系统目录恢复数据，跳过本次镜像（避免用刚恢复的内容覆盖备份的元信息）")
        # 恢复后不再立刻镜像回去：因为刚恢复的内容 mtime 可能比系统目录的旧，
        # 镜像逻辑会判定为"未变化"而跳过，但写入可能会更新 atime 等，造成混淆。
        # 下次正常启动时会自动镜像。
        return
    _mirror_to_system_dir()
    log_message("系统目录同步完成")

if __name__ == "__main__":
    try:
        MUTEX_NAME = "Global\\TempleManagement_SingleInstance"
        mutex = ctypes.windll.kernel32.CreateMutexW(None, True, MUTEX_NAME)
        last_error = ctypes.windll.kernel32.GetLastError()
        ALREADY_EXISTS = 183

        if last_error == ALREADY_EXISTS:
            log_message("检测到已有实例运行，打开浏览器后退出")
            local_ip = get_local_ip()
            for try_port in [8080, 8081, 8082, 8083, 8084, 8085]:
                url = f"http://{local_ip}:{try_port}"
                try:
                    import urllib.request
                    urllib.request.urlopen(f"http://127.0.0.1:{try_port}/health", timeout=2)
                    webbrowser.open(url)
                    log_message(f"已打开浏览器: {url}")
                    break
                except Exception:
                    continue
            sys.exit(0)

        log_message("缘通寺院信息管理系统 启动中...")

        # 在服务器启动前同步本地与系统目录：
        # - 若本地 database/uploads 缺失（升级覆盖/误删），从系统目录恢复
        # - 否则把本地最新状态镜像到系统目录
        sync_with_system_dir()

        server_port = CONFIG['port']
        if not is_port_available(server_port):
            log_message(f"端口 {server_port} 已被占用，正在寻找可用端口...")
            server_port = find_free_port()
            log_message(f"使用端口: {server_port}")

        _server_port[0] = server_port
        local_ip = get_local_ip()
        url = f"http://{local_ip}:{server_port}"

        server_thread = threading.Thread(target=run_server, daemon=True)
        server_thread.start()

        # 启动数据同步 watcher 线程（事件驱动增量同步到系统目录）
        sync_thread = threading.Thread(target=sync_watcher, daemon=True)
        sync_thread.start()

        log_message("服务器线程已启动, 等待HTTP响应...")

        if not wait_for_server(f"http://127.0.0.1:{server_port}"):
            if _server_error[0]:
                log_message(f"服务器启动错误: {_server_error[0]}")
            log_message("服务器启动失败!")
            os._exit(1)

        log_message(f"服务地址: {url}")
        log_message("正在打开浏览器...")

        time.sleep(1)
        webbrowser.open(url)
        log_message(f"已在浏览器中打开: {url}")

        show_control_window(url)

    except Exception as e:
        log_message(f"启动失败: {e}")
        traceback.print_exc()
