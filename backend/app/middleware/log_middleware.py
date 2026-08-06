from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import AsyncSessionLocal
from ..models.system_log import SystemLog
from ..models.user import User
import json
import time
from datetime import datetime

# 写操作 HTTP 方法，触发系统目录镜像同步
WRITE_METHODS = {'POST', 'PUT', 'PATCH', 'DELETE'}

# 跳过同步触发的路径（高频但无业务数据变化的接口）
SYNC_SKIP_PATHS = {
    '/api/auth/login',
    '/api/auth/logout',
    '/api/system-logs',
}

def _mark_sync_dirty():
    """标记数据库有写入，待 watcher 线程 debounce 后增量同步到系统目录。

    temple_sync_state 模块在 standalone_main.py 启动时通过 sys.modules 注册，
    包含 dirty_time、last_sync_time、lock 三个属性。
    """
    try:
        import temple_sync_state
        with temple_sync_state.lock:
            temple_sync_state.dirty_time = time.time()
    except ImportError:
        # 开发模式下（python -m uvicorn）standalone_main.py 未运行，模块未注册，跳过
        pass
    except Exception:
        pass

class LogMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        if request.url.path.startswith('/api/') and request.url.path != '/api/auth/login':
            try:
                username = None
                auth_header = request.headers.get('Authorization')

                if auth_header and auth_header.startswith('Bearer '):
                    token = auth_header.split(' ')[1]
                    async with AsyncSessionLocal() as db:
                        result = await db.execute(
                            select(User).where(User.token == token)
                        )
                        user = result.scalar_one_or_none()
                        if user:
                            username = user.username

                if username:
                    operation_type = self.get_operation_type(request.method, request.url.path)
                    operation_content = self.get_operation_content(request.method, request.url.path)

                    if operation_type:
                        async with AsyncSessionLocal() as db:
                            log = SystemLog(
                                用户名=username,
                                操作类型=operation_type,
                                操作内容=operation_content,
                                created_at=datetime.utcnow()
                            )
                            db.add(log)
                            await db.commit()
            except Exception as e:
                print(f"记录日志失败: {e}")

        # 写操作且响应成功（2xx）时，标记需要增量同步
        if (request.method in WRITE_METHODS
                and request.url.path not in SYNC_SKIP_PATHS
                and 200 <= response.status_code < 300):
            _mark_sync_dirty()

        return response
    
    def get_operation_type(self, method: str, path: str) -> str:
        if '/login' in path:
            return '登录'
        elif '/logout' in path:
            return '登出'
        elif method == 'POST':
            return '新增'
        elif method == 'PUT' or method == 'PATCH':
            return '修改'
        elif method == 'DELETE':
            return '删除'
        elif method == 'GET' and ('print' in path.lower() or 'template' in path.lower()):
            return '打印'
        elif method == 'GET':
            return '查询'
        return ''
    
    def get_operation_content(self, method: str, path: str) -> str:
        path_parts = path.split('/')
        if len(path_parts) >= 3:
            module = path_parts[2]
            action_map = {
                'POST': '创建',
                'PUT': '更新',
                'DELETE': '删除',
                'GET': '查询'
            }
            action = action_map.get(method, '操作')
            return f"{action} {module} 数据"
        return f"{method} {path}"
