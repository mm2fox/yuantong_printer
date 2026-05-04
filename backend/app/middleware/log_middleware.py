from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import AsyncSessionLocal
from ..models.system_log import SystemLog
from ..models.user import User
import json
from datetime import datetime

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
