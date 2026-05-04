from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func, and_
from datetime import datetime
from typing import List, Optional
from ..core.database import get_db
from ..models.user import User
from ..models.system_log import SystemLog
from ..schemas.system_log import SystemLogCreate, SystemLogResponse, SystemLogDelete
from .auth import get_current_user

router = APIRouter(prefix="/api/system-logs", tags=["系统日志"])

@router.get("", response_model=List[SystemLogResponse])
async def get_system_logs(
    start_date: Optional[str] = Query(None, description="开始日期 yyyy-MM-dd"),
    end_date: Optional[str] = Query(None, description="结束日期 yyyy-MM-dd"),
    用户名: Optional[str] = Query(None, description="用户名"),
    操作类型: Optional[str] = Query(None, description="操作类型"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(SystemLog)
    
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.where(SystemLog.created_at >= start)
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用 yyyy-MM-dd 格式")
    
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
            query = query.where(SystemLog.created_at <= end)
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用 yyyy-MM-dd 格式")
    
    if 用户名 and 用户名.strip():
        query = query.where(SystemLog.用户名.contains(用户名.strip()))
    
    if 操作类型 and 操作类型.strip():
        query = query.where(SystemLog.操作类型 == 操作类型.strip())
    
    query = query.order_by(SystemLog.created_at.desc())
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return logs

@router.get("/count")
async def get_system_log_count(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    用户名: Optional[str] = Query(None),
    操作类型: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(func.count()).select_from(SystemLog)
    
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.where(SystemLog.created_at >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
            query = query.where(SystemLog.created_at <= end)
        except ValueError:
            pass
    
    if 用户名 and 用户名.strip():
        query = query.where(SystemLog.用户名.contains(用户名.strip()))
    
    if 操作类型 and 操作类型.strip():
        query = query.where(SystemLog.操作类型 == 操作类型.strip())
    
    result = await db.execute(query)
    count = result.scalar()
    
    return {"count": count}

@router.post("", response_model=SystemLogResponse)
async def create_system_log(
    log_data: SystemLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    log = SystemLog(**log_data.dict())
    if current_user.temple_id:
        log.temple_id = current_user.temple_id
    
    db.add(log)
    await db.commit()
    await db.refresh(log)
    
    return log

@router.delete("")
async def delete_system_logs(
    delete_data: SystemLogDelete,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != '管理员':
        raise HTTPException(
            status_code=403,
            detail="权限不足，只有管理员可以删除日志"
        )
    
    try:
        start = datetime.strptime(delete_data.start_date, "%Y-%m-%d")
        end = datetime.strptime(delete_data.end_date, "%Y-%m-%d")
        end = end.replace(hour=23, minute=59, second=59)
        
        conditions = [SystemLog.created_at >= start, SystemLog.created_at <= end]
        
        if delete_data.用户名 and delete_data.用户名.strip():
            conditions.append(SystemLog.用户名.contains(delete_data.用户名.strip()))
        
        if delete_data.操作类型 and delete_data.操作类型.strip():
            conditions.append(SystemLog.操作类型 == delete_data.操作类型.strip())
        
        stmt = delete(SystemLog).where(and_(*conditions))
        result = await db.execute(stmt)
        await db.commit()
        
        deleted_count = result.rowcount
        
        return {
            "success": True,
            "message": f"成功删除 {deleted_count} 条日志记录",
            "deleted_count": deleted_count
        }
        
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")


@router.get("/my-logs", response_model=List[SystemLogResponse])
async def get_my_logs(
    start_date: Optional[str] = Query(None, description="开始日期 yyyy-MM-dd"),
    end_date: Optional[str] = Query(None, description="结束日期 yyyy-MM-dd"),
    操作类型: Optional[str] = Query(None, description="操作类型"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(SystemLog).where(SystemLog.用户名 == current_user.username)
    
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.where(SystemLog.created_at >= start)
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用 yyyy-MM-dd 格式")
    
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
            query = query.where(SystemLog.created_at <= end)
        except ValueError:
            raise HTTPException(status_code=400, detail="日期格式错误，请使用 yyyy-MM-dd 格式")
    
    if 操作类型 and 操作类型.strip():
        query = query.where(SystemLog.操作类型 == 操作类型.strip())
    
    query = query.order_by(SystemLog.created_at.desc())
    result = await db.execute(query)
    logs = result.scalars().all()
    
    return logs


@router.get("/my-logs/count")
async def get_my_log_count(
    start_date: Optional[str] = Query(None),
    end_date: Optional[str] = Query(None),
    操作类型: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(func.count()).select_from(SystemLog).where(SystemLog.用户名 == current_user.username)
    
    if start_date:
        try:
            start = datetime.strptime(start_date, "%Y-%m-%d")
            query = query.where(SystemLog.created_at >= start)
        except ValueError:
            pass
    
    if end_date:
        try:
            end = datetime.strptime(end_date, "%Y-%m-%d")
            end = end.replace(hour=23, minute=59, second=59)
            query = query.where(SystemLog.created_at <= end)
        except ValueError:
            pass
    
    if 操作类型 and 操作类型.strip():
        query = query.where(SystemLog.操作类型 == 操作类型.strip())
    
    result = await db.execute(query)
    count = result.scalar()
    
    return {"count": count}
