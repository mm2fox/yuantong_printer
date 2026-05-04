from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from typing import Optional, List
from datetime import datetime
from ..core.database import get_db
from ..core.security import verify_password, create_access_token, decode_token, get_password_hash
from ..models.user import User, Temple
from ..models.system_log import SystemLog
from ..schemas.user import UserLogin, Token, UserResponse, UserCreate, UserUpdate

router = APIRouter(prefix="/api/auth", tags=["认证"])

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login", auto_error=False)

async def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db)
) -> User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="无效的认证凭证",
        headers={"WWW-Authenticate": "Bearer"},
    )
    if token is None:
        raise credentials_exception
    payload = decode_token(token)
    if payload is None:
        raise credentials_exception
    username: str = payload.get("sub")
    if username is None:
        raise credentials_exception
    
    result = await db.execute(select(User).where(User.username == username))
    user = result.scalar_one_or_none()
    if user is None:
        raise credentials_exception
    return user

@router.get("/public-users", response_model=List[str])
async def get_public_users(
    db: AsyncSession = Depends(get_db)
):
    """获取用户名列表（公开接口，用于登录页面）"""
    result = await db.execute(select(User.username).where(User.is_active == True))
    users = result.scalars().all()
    return users

@router.get("/users")
async def get_users(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户列表"""
    if current_user.role != "管理员":
        raise HTTPException(status_code=403, detail="无权限操作")
    
    result = await db.execute(select(User).options(joinedload(User.temple)))
    users = result.scalars().unique().all()
    
    user_list = []
    for user in users:
        user_dict = {
            "id": user.id,
            "username": user.username,
            "real_name": user.real_name,
            "role": user.role,
            "permissions": user.permissions,
            "is_active": user.is_active,
            "temple_id": user.temple_id,
            "temple_name": user.temple.寺庙名称 if user.temple else None,
            "created_at": user.created_at.isoformat() if user.created_at else None,
            "updated_at": user.updated_at.isoformat() if user.updated_at else None
        }
        user_list.append(user_dict)
    
    return user_list

@router.post("/users", response_model=UserResponse)
async def create_user(
    user_data: UserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """创建用户"""
    if current_user.role != "管理员":
        raise HTTPException(status_code=403, detail="无权限操作")
    
    result = await db.execute(select(User).where(User.username == user_data.username))
    if result.scalar_one_or_none():
        raise HTTPException(status_code=400, detail="用户名已存在")
    
    user = User(
        username=user_data.username,
        password_hash=get_password_hash(user_data.password),
        real_name=user_data.real_name,
        role=user_data.role,
        is_active=user_data.is_active if user_data.is_active is not None else True,
        temple_id=user_data.temple_id
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user

@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    user_data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户"""
    if current_user.role != "管理员":
        raise HTTPException(status_code=403, detail="无权限操作")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user_data.real_name is not None:
        user.real_name = user_data.real_name
    if user_data.role is not None:
        user.role = user_data.role
    if user_data.is_active is not None:
        user.is_active = user_data.is_active
    if user_data.password:
        user.password_hash = get_password_hash(user_data.password)
    if user_data.temple_id is not None:
        user.temple_id = user_data.temple_id
    
    await db.commit()
    await db.refresh(user)
    return user

@router.delete("/users/{user_id}")
async def delete_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """删除用户"""
    if current_user.role != "管理员":
        raise HTTPException(status_code=403, detail="无权限操作")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    if user.username == "admin":
        raise HTTPException(status_code=400, detail="不能删除admin用户")
    
    await db.delete(user)
    await db.commit()
    return {"message": "删除成功"}

@router.get("/external-users", response_model=List[str])
async def get_external_users():
    """获取外服务器用户列表（暂时返回空列表）"""
    return []

@router.post("/login", response_model=Token)
async def login(user_login: UserLogin, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(User).where(User.username == user_login.username))
    user = result.scalar_one_or_none()
    
    if not user or not verify_password(user_login.password, user.password_hash):
        log = SystemLog(
            用户名=user_login.username,
            操作类型="登录失败",
            操作内容=f"用户 {user_login.username} 登录失败：用户名或密码错误",
            created_at=datetime.utcnow()
        )
        db.add(log)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="用户名或密码错误",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        log = SystemLog(
            用户名=user.username,
            操作类型="登录失败",
            操作内容=f"用户 {user.username} 登录失败：用户已被禁用",
            created_at=datetime.utcnow()
        )
        db.add(log)
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="用户已被禁用"
        )
    
    access_token = create_access_token(data={"sub": user.username})
    user.token = access_token
    await db.commit()
    
    log = SystemLog(
        用户名=user.username,
        操作类型="登录",
        操作内容=f"用户 {user.username} 登录系统",
        created_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    
    return Token(
        access_token=access_token,
        user=UserResponse.from_orm(user)
    )

@router.post("/logout")
async def logout(current_user: User = Depends(get_current_user), db: AsyncSession = Depends(get_db)):
    log = SystemLog(
        用户名=current_user.username,
        操作类型="登出",
        操作内容=f"用户 {current_user.username} 退出系统",
        created_at=datetime.utcnow()
    )
    db.add(log)
    current_user.token = None
    await db.commit()
    return {"message": "登出成功"}

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return UserResponse.from_orm(current_user)
