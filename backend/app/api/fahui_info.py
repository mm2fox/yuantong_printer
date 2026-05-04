from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from ..core.database import get_db
from ..models.user import User
from ..models.fahui_info import FahuiInfo
from ..schemas.fahui_info import FahuiInfoCreate, FahuiInfoUpdate, FahuiInfoResponse
from .auth import get_current_user

router = APIRouter(prefix="/api/fahui-info", tags=["法会信息"])

@router.get("", response_model=List[FahuiInfoResponse])
async def get_fahui_info_list(
    keyword: Optional[str] = Query(None, description="搜索关键词"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(FahuiInfo).where(FahuiInfo.temple_id == current_user.temple_id)
    
    if keyword:
        query = query.where(FahuiInfo.法会名称.contains(keyword))
    
    result = await db.execute(query)
    info_list = result.scalars().all()
    return info_list

@router.get("/{info_id}", response_model=FahuiInfoResponse)
async def get_fahui_info(
    info_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(FahuiInfo).where(FahuiInfo.id == info_id))
    info = result.scalar_one_or_none()
    if not info:
        raise HTTPException(status_code=404, detail="法会信息不存在")
    return info

@router.post("", response_model=FahuiInfoResponse)
async def create_fahui_info(
    info_data: FahuiInfoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    info = FahuiInfo(**info_data.dict())
    if current_user.temple_id:
        info.temple_id = current_user.temple_id
    
    db.add(info)
    await db.commit()
    await db.refresh(info)
    return info

@router.put("/{info_id}", response_model=FahuiInfoResponse)
async def update_fahui_info(
    info_id: int,
    info_data: FahuiInfoUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(FahuiInfo).where(FahuiInfo.id == info_id))
    info = result.scalar_one_or_none()
    if not info:
        raise HTTPException(status_code=404, detail="法会信息不存在")
    
    for key, value in info_data.dict(exclude_unset=True).items():
        setattr(info, key, value)
    
    await db.commit()
    await db.refresh(info)
    return info

@router.delete("/{info_id}")
async def delete_fahui_info(
    info_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(FahuiInfo).where(FahuiInfo.id == info_id))
    info = result.scalar_one_or_none()
    if not info:
        raise HTTPException(status_code=404, detail="法会信息不存在")
    
    await db.delete(info)
    await db.commit()
    return {"message": "删除成功"}
