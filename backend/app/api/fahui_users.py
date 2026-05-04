from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from typing import List, Optional
from datetime import datetime
from ..core.database import get_db
from ..models.user import User
from ..models.fahui_user import FahuiUser
from ..models.system_log import SystemLog
from ..schemas.fahui_user import FahuiUserCreate, FahuiUserUpdate, FahuiUserResponse
from .auth import get_current_user

router = APIRouter(prefix="/api/fahui-users", tags=["施主管理"])

@router.get("", response_model=List[FahuiUserResponse])
async def get_fahui_users(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    limit: int = Query(50, description="返回数量限制", ge=1, le=500),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(FahuiUser).where(FahuiUser.temple_id == current_user.temple_id)
    
    if keyword:
        query = query.where(
            or_(
                FahuiUser.施主姓名.contains(keyword),
                FahuiUser.施主编号.contains(keyword),
                FahuiUser.电话.contains(keyword)
            )
        )
    
    query = query.order_by(FahuiUser.id.desc()).limit(limit)
    result = await db.execute(query)
    users = result.scalars().all()
    return users

@router.get("/generate-code")
async def generate_code(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(FahuiUser).where(FahuiUser.temple_id == current_user.temple_id).order_by(FahuiUser.id.desc()).limit(1))
    last_user = result.scalar_one_or_none()
    
    if last_user:
        try:
            last_num = int(last_user.施主编号.replace("FH", ""))
            new_num = last_num + 1
        except:
            new_num = 1
    else:
        new_num = 1
    
    code = f"FH{new_num:08d}"
    return {"code": code}

@router.get("/{user_id}", response_model=FahuiUserResponse)
async def get_fahui_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(FahuiUser).where(FahuiUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="施主不存在")
    return user

@router.post("", response_model=FahuiUserResponse)
async def create_fahui_user(
    user_data: FahuiUserCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    user = FahuiUser(**user_data.dict())
    user.登记人 = current_user.username
    user.登记时间 = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if current_user.temple_id:
        user.temple_id = current_user.temple_id
    
    db.add(user)
    await db.commit()
    await db.refresh(user)
    
    log = SystemLog(
        用户名=current_user.username,
        操作类型="新增",
        操作内容=f"新增施主：{user.施主姓名}（{user.施主编号}）",
        created_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    
    return user

@router.put("/{user_id}", response_model=FahuiUserResponse)
async def update_fahui_user(
    user_id: int,
    user_data: FahuiUserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(FahuiUser).where(FahuiUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="施主不存在")
    
    for key, value in user_data.dict(exclude_unset=True).items():
        setattr(user, key, value)
    
    await db.commit()
    await db.refresh(user)
    
    log = SystemLog(
        用户名=current_user.username,
        操作类型="修改",
        操作内容=f"修改施主：{user.施主姓名}（{user.施主编号}）",
        created_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    
    return user

@router.delete("/{user_id}")
async def delete_fahui_user(
    user_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(FahuiUser).where(FahuiUser.id == user_id))
    user = result.scalar_one_or_none()
    if not user:
        raise HTTPException(status_code=404, detail="施主不存在")
    
    shizhu_name = user.施主姓名
    shizhu_code = user.施主编号
    
    await db.delete(user)
    await db.commit()
    
    log = SystemLog(
        用户名=current_user.username,
        操作类型="删除",
        操作内容=f"删除施主：{shizhu_name}（{shizhu_code}）",
        created_at=datetime.utcnow()
    )
    db.add(log)
    await db.commit()
    
    return {"message": "删除成功"}
