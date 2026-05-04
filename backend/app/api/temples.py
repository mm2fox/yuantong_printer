from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from ..core.database import get_db
from ..models.user import User, Temple
from ..schemas.temple import TempleCreate, TempleUpdate, TempleResponse
from .auth import get_current_user

router = APIRouter(prefix="/api/temples", tags=["寺庙管理"])

@router.get("")
async def get_temples(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(Temple))
    temples = result.scalars().all()
    
    temple_list = []
    for temple in temples:
        user_count_result = await db.execute(
            select(func.count(User.id)).where(User.temple_id == temple.id)
        )
        user_count = user_count_result.scalar()
        
        temple_dict = {
            "id": temple.id,
            "寺庙名称": temple.寺庙名称,
            "寺庙地址": temple.寺庙地址,
            "联系电话": temple.联系电话,
            "备注": temple.备注,
            "user_count": user_count,
            "created_at": temple.created_at.isoformat() if temple.created_at else None,
            "updated_at": temple.updated_at.isoformat() if temple.updated_at else None
        }
        temple_list.append(temple_dict)
    
    return temple_list

@router.post("", response_model=TempleResponse)
async def create_temple(
    temple_data: TempleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "管理员":
        raise HTTPException(status_code=403, detail="无权限操作")
    
    temple = Temple(**temple_data.dict())
    db.add(temple)
    await db.commit()
    await db.refresh(temple)
    return temple

@router.put("/{temple_id}", response_model=TempleResponse)
async def update_temple(
    temple_id: int,
    temple_data: TempleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "管理员":
        raise HTTPException(status_code=403, detail="无权限操作")
    
    result = await db.execute(select(Temple).where(Temple.id == temple_id))
    temple = result.scalar_one_or_none()
    if not temple:
        raise HTTPException(status_code=404, detail="寺庙不存在")
    
    for key, value in temple_data.dict(exclude_unset=True).items():
        setattr(temple, key, value)
    
    await db.commit()
    await db.refresh(temple)
    return temple

@router.delete("/{temple_id}")
async def delete_temple(
    temple_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != "管理员":
        raise HTTPException(status_code=403, detail="无权限操作")
    
    user_count_result = await db.execute(
        select(func.count(User.id)).where(User.temple_id == temple_id)
    )
    user_count = user_count_result.scalar()
    
    if user_count > 0:
        raise HTTPException(status_code=400, detail="该寺庙下有用户，无法删除")
    
    result = await db.execute(select(Temple).where(Temple.id == temple_id))
    temple = result.scalar_one_or_none()
    if not temple:
        raise HTTPException(status_code=404, detail="寺庙不存在")
    
    await db.delete(temple)
    await db.commit()
    return {"message": "删除成功"}
