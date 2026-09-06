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
import subprocess
import zipfile
import base64
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

def detect_running_from_zip():
    """检测程序是否直接从 ZIP 压缩包内启动。

    Windows 在 ZIP 内双击 exe 时，只会把 exe 解压到临时目录，
    路径形如 ...\\Temp\\Temp1_xxx.zip\\program.exe，
    路径中某一级目录名会以 ".zip" 结尾。
    返回命中的路径字符串，未命中返回 None。
    """
    candidates = []
    if getattr(sys, 'frozen', False):
        candidates.append(sys.executable)
        candidates.append(getattr(sys, '_MEIPASS', ''))
    if sys.argv:
        candidates.append(sys.argv[0])
    try:
        candidates.append(str(Path(__file__).resolve()))
    except Exception:
        pass
    try:
        candidates.append(str(get_data_path()))
        candidates.append(str(get_base_path()))
    except Exception:
        pass

    for p in candidates:
        if not p:
            continue
        try:
            abs_p = os.path.abspath(str(p))
        except Exception:
            abs_p = str(p)
        for part in abs_p.split(os.sep):
            if part.lower().endswith('.zip'):
                return abs_p
    return None

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

APP_ICON_FINGERPRINT_B64 = "bw5HfPUnRa5d3qAngr++us5Dm6e4+V96OXegycXz23zhwhqP3/ERavCX604yq5TiJPDAxhF6Yo+anDapUtrwtyYYakIpDhTEc+KEo7cfBquegyPCWZ8KvHx3h6deN7Y+2UNmykDZc3wsZv2KJp8e9jzyUi9STNl0bo21CzpU40DiAs4yOqkxo+B5+cMefrhzDoVCOG2Fpbz+6za9laSZElJPUnR4D5YqcRm8AlM+b9uKQFBQISkaWVugHaDcFZ+6QgYkUW57MIgEQi6NrpIvMuKmTWlXB9od4zMLjWvOgxffCbR8xGUrHAc+6fD+R8KllyXsO5Ry8kTKpxfHHBx17D6o9PUat2yEE+PKbw8Jqy8yOpnx5kHPNZ+NabQC2/d0uHiZUS05fvxaQj0V"

def _bytes_in_file(path, needle, chunk_size=2 * 1024 * 1024, overlap=512):
    n = len(needle)
    if n == 0:
        return True
    if n > chunk_size:
        chunk_size = n + 1024
    try:
        with open(path, "rb") as f:
            prev_tail = b""
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                if needle in (prev_tail + chunk):
                    return True
                if len(chunk) < chunk_size:
                    break
                prev_tail = chunk[-overlap:] if overlap > 0 else b""
        return False
    except Exception:
        return False

def validate_exe_identity(exe_path):
    """校验 exe 是否为本系统合法程序。返回 (level, reason)。
    level: 'ok' 全部通过；'warn' 硬性通过但图标指纹缺失；'fail' 硬性不通过。
    """
    try:
        size = os.path.getsize(exe_path)
    except Exception as e:
        return ("fail", f"无法读取文件: {e}")
    if size < 10 * 1024 * 1024:
        return ("fail", f"文件大小仅 {size // 1024} KB，不是本系统程序（正常约 60MB）。")
    try:
        with open(exe_path, "rb") as f:
            head = f.read(2)
    except Exception as e:
        return ("fail", f"读取文件失败: {e}")
    if head != b"MZ":
        return ("fail", "不是有效的 Windows 可执行文件（缺少 MZ 头）。")
    mei_magic = b'MEI\014\013\012\013\016'
    try:
        with open(exe_path, "rb") as f:
            f.seek(max(0, size - 65536))
            tail = f.read()
    except Exception:
        tail = b""
    if mei_magic not in tail:
        return ("fail", "不是 PyInstaller 打包的程序，无法自动升级。")
    try:
        fingerprint = base64.b64decode(APP_ICON_FINGERPRINT_B64)
    except Exception:
        fingerprint = b""
    if fingerprint and _bytes_in_file(exe_path, fingerprint):
        return ("ok", "身份校验通过")
    return ("warn", "未检测到本系统图标特征。这个文件可能不是缘通寺院信息管理系统，继续可能有风险。")

def _cleanup_upgrade_extract(extract_dir):
    try:
        if extract_dir and os.path.isdir(extract_dir):
            shutil.rmtree(extract_dir, ignore_errors=True)
    except Exception:
        pass

def _ask_overwrite_options(parent, has_config, has_db, has_uploads):
    """弹窗让用户选择是否覆盖 ZIP 内的附带文件。返回 dict(config/db/uploads) 或 None(取消)。"""
    import tkinter as tk

    dlg = tk.Toplevel(parent)
    dlg.title("选择覆盖内容")
    dlg.transient(parent)
    dlg.grab_set()
    dlg.resizable(False, False)

    result = {"ok": False, "config": False, "db": False, "uploads": False}

    tk.Label(
        dlg,
        text="ZIP 包含以下附带文件，是否覆盖当前对应文件？\n（默认不勾选，仅升级程序）",
        justify="left",
    ).pack(padx=12, pady=(10, 6))

    cfg_var = tk.BooleanVar(value=False)
    db_var = tk.BooleanVar(value=False)
    up_var = tk.BooleanVar(value=False)

    def add_row(has, label, var, warning=""):
        if not has:
            return
        row = tk.Frame(dlg)
        row.pack(fill="x", padx=12, pady=2)
        tk.Checkbutton(row, text=label, variable=var).pack(side="left")
        if warning:
            tk.Label(row, text=warning, fg="#c0392b").pack(side="left", padx=8)

    add_row(has_config, "覆盖 config.json（寺院配置/端口等）", cfg_var)
    add_row(has_db, "覆盖数据库 temple.db", db_var, "（会丢失现有数据，回滚不可恢复！）")
    add_row(has_uploads, "覆盖 uploads/（打印模板等上传文件）", up_var)

    btns = tk.Frame(dlg)
    btns.pack(pady=10)

    def on_ok():
        result["config"] = bool(cfg_var.get())
        result["db"] = bool(db_var.get())
        result["uploads"] = bool(up_var.get())
        result["ok"] = True
        dlg.destroy()

    def on_cancel():
        dlg.destroy()

    tk.Button(btns, text="取消", width=8, command=on_cancel).pack(side="left", padx=8)
    tk.Button(btns, text="确认", width=8, command=on_ok).pack(side="left", padx=8)
    dlg.protocol("WM_DELETE_WINDOW", on_cancel)
    parent.wait_window(dlg)
    if not result["ok"]:
        return None
    return result

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

    def upgrade_self():
        from tkinter import filedialog, messagebox

        current_exe = sys.executable if getattr(sys, "frozen", False) else None
        if not current_exe:
            messagebox.showerror("升级", "非打包模式，无法升级。请直接替换源码文件。")
            return

        exe_dir = os.path.dirname(current_exe)
        exe_name = os.path.basename(current_exe)

        src_path = filedialog.askopenfilename(
            title=f"选择新版 {exe_name}",
            initialdir=exe_dir,
            filetypes=[("程序/压缩包", "*.exe *.zip"), ("可执行文件", "*.exe"), ("压缩包", "*.zip"), ("所有文件", "*.*")],
        )
        if not src_path:
            return

        if os.path.normpath(src_path) == os.path.normpath(current_exe):
            messagebox.showwarning("升级", "选中的文件就是当前正在运行的程序，请选择新版本。")
            return

        extract_dir = ""
        ov_config = "0"
        ov_db = "0"
        ov_uploads = "0"

        lower = src_path.lower()
        if lower.endswith(".zip"):
            extract_dir = os.path.join(exe_dir, "_upgrade_extract")
            try:
                if os.path.exists(extract_dir):
                    shutil.rmtree(extract_dir, ignore_errors=True)
                os.makedirs(extract_dir, exist_ok=True)
                with zipfile.ZipFile(src_path, "r") as zf:
                    zf.extractall(extract_dir)
            except Exception as e:
                messagebox.showerror("升级", f"解压 ZIP 失败: {e}")
                _cleanup_upgrade_extract(extract_dir)
                return

            found_exes = []
            for root_w, _dirs, files in os.walk(extract_dir):
                for fn in files:
                    if fn.lower().endswith(".exe"):
                        found_exes.append(os.path.join(root_w, fn))
            if not found_exes:
                messagebox.showerror("升级", "ZIP 内未找到可执行文件（.exe）。")
                _cleanup_upgrade_extract(extract_dir)
                return

            if len(found_exes) == 1:
                chosen = found_exes[0]
            else:
                chosen = None
                for p in found_exes:
                    if os.path.basename(p) == exe_name:
                        chosen = p
                        break
                if not chosen:
                    for p in found_exes:
                        if os.path.basename(p) == "缘通寺院信息管理系统.exe":
                            chosen = p
                            break
                if not chosen:
                    chosen = max(found_exes, key=lambda p: os.path.getsize(p))
                if not messagebox.askyesno(
                    "升级",
                    f"ZIP 内找到 {len(found_exes)} 个 exe，已选中：\n{os.path.basename(chosen)}\n\n用这个进行升级吗？",
                ):
                    _cleanup_upgrade_extract(extract_dir)
                    return
            src_path = chosen

            level, reason = validate_exe_identity(src_path)
            if level == "fail":
                messagebox.showerror("升级", f"文件校验失败：{reason}")
                _cleanup_upgrade_extract(extract_dir)
                return
            if level == "warn":
                if not messagebox.askyesno("升级警告", f"{reason}\n\n仍要继续升级吗？"):
                    _cleanup_upgrade_extract(extract_dir)
                    return

            has_config = os.path.isfile(os.path.join(extract_dir, "config.json"))
            has_db = os.path.isfile(os.path.join(extract_dir, "database", "temple.db"))
            has_uploads = os.path.isdir(os.path.join(extract_dir, "uploads"))
            if has_config or has_db or has_uploads:
                sel = _ask_overwrite_options(root, has_config, has_db, has_uploads)
                if sel is None:
                    _cleanup_upgrade_extract(extract_dir)
                    return
                ov_config = "1" if sel["config"] else "0"
                ov_db = "1" if sel["db"] else "0"
                ov_uploads = "1" if sel["uploads"] else "0"
        elif lower.endswith(".exe"):
            level, reason = validate_exe_identity(src_path)
            if level == "fail":
                messagebox.showerror("升级", f"文件校验失败：{reason}")
                return
            if level == "warn":
                if not messagebox.askyesno("升级警告", f"{reason}\n\n仍要继续升级吗？"):
                    return
        else:
            messagebox.showerror("升级", "请选择 .exe 或 .zip 文件。")
            return

        version_display = BUILD_VERSION or "未知"
        if extract_dir:
            parts = []
            if ov_config == "1":
                parts.append("config.json")
            if ov_db == "1":
                parts.append("数据库")
            if ov_uploads == "1":
                parts.append("uploads")
            if parts:
                extras_desc = "\n\n额外覆盖：" + "、".join(parts) + "\n（数据库覆盖不可随程序回滚恢复）"
            else:
                extras_desc = "\n\n仅升级程序，不覆盖其他文件。"
        else:
            extras_desc = ""
        will_overwrite = ov_config == "1" or ov_db == "1" or ov_uploads == "1"
        if not messagebox.askyesno(
            "确认升级",
            f"当前版本: {version_display}\n\n"
            "升级将执行以下操作：\n\n"
            "1. 同步并备份当前数据（数据库和上传文件）\n"
            "2. 关闭当前程序\n"
            "3. 备份旧程序并替换为新版本\n"
            "4. 启动新版本验证\n"
            "5. 新版本启动失败时自动回滚到旧版本\n"
            + ("数据库和上传文件不会被覆盖，升级后数据保留。" if not will_overwrite else "按你的选择，部分附带文件也会被覆盖。")
            + extras_desc + "\n\n确认要升级吗？",
        ):
            if extract_dir:
                _cleanup_upgrade_extract(extract_dir)
            return

        ps1_path = os.path.join(exe_dir, "_upgrade.ps1")
        ps1_template = r'''$ErrorActionPreference = 'Stop'
$exeDir = '__EXE_DIR__'
$exeName = '__EXE_NAME__'
$srcPath = '__SRC_PATH__'
$extractDir = '__EXTRACT_DIR__'
$ovConfig = '__OV_CONFIG__'
$ovDb = '__OV_DB__'
$ovUploads = '__OV_UPLOADS__'
$exeFullName = Join-Path $exeDir $exeName
$procName = [System.IO.Path]::GetFileNameWithoutExtension($exeName)

Set-Location $exeDir

Write-Host '[1/5] 等待旧进程退出（含 bootloader，最多 60 秒）...'
$waitCount = 0
$found = $true
while ($waitCount -lt 60) {
    $p = Get-Process -Name $procName -ErrorAction SilentlyContinue
    if (-not $p) { $found = $false; break }
    Start-Sleep -Seconds 1
    $waitCount++
}
if ($found) {
    Write-Host '[WARN] 旧进程 60 秒未自然退出，强制终止...'
    Get-Process -Name $procName -ErrorAction SilentlyContinue | Stop-Process -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 5
}

Write-Host '[2/5] 清理残留文件...'
Remove-Item -LiteralPath (Join-Path $exeDir "$exeName.failed") -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath (Join-Path $exeDir "$exeName.bak") -Force -ErrorAction SilentlyContinue

Write-Host '[3/5] 备份旧程序并替换为新版本...'
try {
    Move-Item -LiteralPath $exeFullName -Destination (Join-Path $exeDir "$exeName.bak") -Force
    Copy-Item -LiteralPath $srcPath -Destination $exeFullName -Force
} catch {
    Write-Host "[ERROR] 替换失败: $($_.Exception.Message)"
    Write-Host '正在回滚...'
    try {
        Move-Item -LiteralPath (Join-Path $exeDir "$exeName.bak") -Destination $exeFullName -Force
    } catch {
        Write-Host "[ERROR] 回滚也失败: $($_.Exception.Message)"
    }
    Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue
    if ($extractDir -ne '') { Remove-Item -LiteralPath $extractDir -Recurse -Force -ErrorAction SilentlyContinue }
    Read-Host '按回车退出'
    exit 1
}

Write-Host '[3.5/5] 复制选中的附带文件...'
if ($ovConfig -eq '1' -and $extractDir -ne '') {
    try {
        $cfgSrc = Join-Path $extractDir 'config.json'
        if (Test-Path -LiteralPath $cfgSrc) { Copy-Item -LiteralPath $cfgSrc -Destination (Join-Path $exeDir 'config.json') -Force }
    } catch { Write-Host "[WARN] 覆盖 config.json 失败: $($_.Exception.Message)" }
}
if ($ovDb -eq '1' -and $extractDir -ne '') {
    try {
        $dbSrc = Join-Path $extractDir 'database\temple.db'
        if (Test-Path -LiteralPath $dbSrc) {
            $dbDstDir = Join-Path $exeDir 'database'
            if (-not (Test-Path -LiteralPath $dbDstDir)) { New-Item -ItemType Directory -Path $dbDstDir -Force | Out-Null }
            Copy-Item -LiteralPath $dbSrc -Destination (Join-Path $dbDstDir 'temple.db') -Force
        }
    } catch { Write-Host "[WARN] 覆盖数据库失败: $($_.Exception.Message)" }
}
if ($ovUploads -eq '1' -and $extractDir -ne '') {
    try {
        $upSrc = Join-Path $extractDir 'uploads'
        if (Test-Path -LiteralPath $upSrc) { Copy-Item -LiteralPath $upSrc -Destination (Join-Path $exeDir 'uploads') -Force -Recurse }
    } catch { Write-Host "[WARN] 覆盖 uploads 失败: $($_.Exception.Message)" }
}

try { Unblock-File -Path $exeFullName -ErrorAction SilentlyContinue } catch {}
Start-Sleep -Seconds 3

Write-Host "[4/5] 启动新 $exeName 验证..."
Start-Process -FilePath $exeFullName
Start-Sleep -Seconds 10

Write-Host '[5/5] 检测新进程是否存活...'
$checkCount = 0
$ok = $false
while ($checkCount -lt 15) {
    $p = Get-Process -Name $procName -ErrorAction SilentlyContinue
    if ($p) { $ok = $true; break }
    Start-Sleep -Seconds 1
    $checkCount++
}

if (-not $ok) {
    Write-Host '[ERROR] 新程序启动失败！正在回滚...'
    $bakPath = Join-Path $exeDir "$exeName.bak"
    if (Test-Path -LiteralPath $bakPath) {
        try {
            Move-Item -LiteralPath $exeFullName -Destination (Join-Path $exeDir "$exeName.failed") -Force -ErrorAction SilentlyContinue
        } catch {}
        Move-Item -LiteralPath $bakPath -Destination $exeFullName -Force
        Start-Process -FilePath $exeFullName
        Write-Host '已回滚到旧版本'
    } else {
        Write-Host '没有备份可回滚，请手动检查'
    }
    Remove-Item -LiteralPath (Join-Path $exeDir "$exeName.failed") -Force -ErrorAction SilentlyContinue
    Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue
    if ($extractDir -ne '') { Remove-Item -LiteralPath $extractDir -Recurse -Force -ErrorAction SilentlyContinue }
    Read-Host '按回车退出'
    exit 1
}

Write-Host '升级成功！'
Remove-Item -LiteralPath (Join-Path $exeDir "$exeName.bak") -Force -ErrorAction SilentlyContinue
Remove-Item -LiteralPath $PSCommandPath -Force -ErrorAction SilentlyContinue
if ($extractDir -ne '') { Remove-Item -LiteralPath $extractDir -Recurse -Force -ErrorAction SilentlyContinue }
exit 0
'''
        ps1_content = (ps1_template
                        .replace('__EXE_DIR__', exe_dir)
                        .replace('__EXE_NAME__', exe_name)
                        .replace('__SRC_PATH__', src_path)
                        .replace('__EXTRACT_DIR__', extract_dir)
                        .replace('__OV_CONFIG__', ov_config)
                        .replace('__OV_DB__', ov_db)
                        .replace('__OV_UPLOADS__', ov_uploads))
        try:
            with open(ps1_path, "w", encoding="utf-8-sig") as f:
                f.write(ps1_content)
        except Exception as e:
            messagebox.showerror("升级", f"生成升级脚本失败: {e}")
            return

        log_message(f"升级: 已生成升级脚本 {ps1_path}，即将退出当前程序")
        try:
            clean_env = os.environ.copy()
            for k in list(clean_env.keys()):
                if k.startswith("_MEI") or k.startswith("_PYI") or k.startswith("PYINSTALLER"):
                    del clean_env[k]
            subprocess.Popen(
                ["powershell", "-ExecutionPolicy", "Bypass", "-NoProfile", "-File", ps1_path],
                creationflags=subprocess.CREATE_NEW_CONSOLE,
                cwd=exe_dir,
                env=clean_env,
            )
        except Exception as e:
            messagebox.showerror("升级", f"启动升级脚本失败: {e}")
            return

        def _upgrade_watchdog():
            time.sleep(15)
            os._exit(0)

        threading.Thread(target=_upgrade_watchdog, daemon=True).start()

        def _do_upgrade_quit():
            log_message("升级: 退出当前程序以完成升级")
            final_sync()
            if tray_icon:
                tray_icon.stop()
            os._exit(0)

        root.after(200, _do_upgrade_quit)

    btn_frame = tk.Frame(frame, bg="#f5f5f5")
    btn_frame.pack(pady=5)

    btn_row1 = tk.Frame(btn_frame, bg="#f5f5f5")
    btn_row1.pack(pady=(0, 5))
    ttk.Button(btn_row1, text="打开浏览器", command=open_browser).pack(side="left", padx=5)
    ttk.Button(btn_row1, text="升级", command=upgrade_self).pack(side="left", padx=5)

    btn_row2 = tk.Frame(btn_frame, bg="#f5f5f5")
    btn_row2.pack()
    ttk.Button(btn_row2, text="隐藏到托盘", command=hide_to_tray).pack(side="left", padx=5)
    ttk.Button(btn_row2, text="退出", command=exit_app).pack(side="left", padx=5)

    tray_icon = create_tray_icon(url, show_window, root)

    def on_close():
        from tkinter import messagebox
        if messagebox.askyesno("确认关闭", "确定要关闭程序吗？关闭后将停止服务。"):
            exit_app()

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
        # 启动前先检测是否直接从 ZIP 压缩包内运行：
        # Windows 在 ZIP 内双击 exe 只会解压 exe 本身，config.json / database / uploads
        # 等不会被解压，会导致数据无法保存、配置丢失，必须拒绝运行。
        zip_hit = detect_running_from_zip()
        if zip_hit:
            log_message(f"检测到从 ZIP 压缩包内启动，拒绝运行: {zip_hit}")
            msg = (
                "检测到程序正在从 ZIP 压缩包中直接运行。\n\n"
                f"检测路径：{zip_hit}\n\n"
                "请先将 ZIP 压缩包完整解压到一个文件夹中，然后再运行程序。\n"
                "直接在 ZIP 中运行会导致数据库无法保存、配置丢失等问题。"
            )
            ctypes.windll.user32.MessageBoxW(0, msg, "运行错误", 0x10)
            sys.exit(1)

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
