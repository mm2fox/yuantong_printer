from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List
from pydantic import BaseModel
from ..core.database import get_db
from ..models.user import User, Permission
from .auth import get_current_user

router = APIRouter(prefix="/api/permissions", tags=["权限管理"])

class PermissionResponse(BaseModel):
    id: int
    name: str
    display_name: str
    description: str = None
    
    class Config:
        from_attributes = True

class UserPermissionsUpdate(BaseModel):
    permissions: List[str]

@router.get("", response_model=List[PermissionResponse])
async def get_permissions(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取所有权限列表"""
    if current_user.role != "管理员":
        raise HTTPException(status_code=403, detail="无权限操作")
    
    result = await db.execute(select(Permission))
    permissions = result.scalars().all()
    return permissions

@router.get("/user/{user_id}")
async def get_user_permissions(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """获取用户权限"""
    if current_user.role != "管理员":
        raise HTTPException(status_code=403, detail="无权限操作")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    permissions = []
    if user.permissions:
        permissions = user.permissions.split(",")
    
    return {"user_id": user_id, "permissions": permissions}

@router.put("/user/{user_id}")
async def update_user_permissions(
    user_id: int,
    data: UserPermissionsUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """更新用户权限"""
    if current_user.role != "管理员":
        raise HTTPException(status_code=403, detail="无权限操作")
    
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="用户不存在")
    
    user.permissions = ",".join(data.permissions) if data.permissions else ""
    await db.commit()
    
    return {"message": "权限更新成功", "permissions": data.permissions}
