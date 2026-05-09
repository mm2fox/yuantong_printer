import json
import os
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import List
from ..core.database import get_db
from ..models.user import User
from ..models.version_info import VersionInfo
from ..schemas.version_info import VersionInfoCreate, VersionInfoResponse
from .auth import get_current_user

router = APIRouter(prefix="/api/version-info", tags=["版本信息"])

@router.get("", response_model=List[VersionInfoResponse])
async def get_version_list(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(VersionInfo).order_by(VersionInfo.created_at.desc())
    result = await db.execute(query)
    versions = result.scalars().all()
    return versions

@router.get("/latest", response_model=VersionInfoResponse)
async def get_latest_version(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(VersionInfo).order_by(VersionInfo.created_at.desc()).limit(1)
    result = await db.execute(query)
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="暂无版本信息")
    return version

@router.get("/count")
async def get_version_count(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(func.count()).select_from(VersionInfo)
    result = await db.execute(query)
    count = result.scalar()
    return {"count": count}

@router.post("", response_model=VersionInfoResponse)
async def create_version(
    version_data: VersionInfoCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != '管理员':
        raise HTTPException(status_code=403, detail="权限不足，只有管理员可以创建版本信息")

    version = VersionInfo(**version_data.dict())
    db.add(version)
    await db.commit()
    await db.refresh(version)
    return version

@router.post("/import-build-info")
async def import_build_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != '管理员':
        raise HTTPException(status_code=403, detail="权限不足")

    build_info_path = os.environ.get("TEMPLE_BUILD_INFO")
    if not build_info_path:
        for candidate in [
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "build_info.json"),
            os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "database", "build_info.json"),
        ]:
            if os.path.exists(candidate):
                build_info_path = candidate
                break

    if not build_info_path or not os.path.exists(build_info_path):
        raise HTTPException(status_code=404, detail="未找到构建信息文件")

    try:
        with open(build_info_path, 'r', encoding='utf-8') as f:
            build_data = json.load(f)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"读取构建信息失败: {str(e)}")

    git_commit = build_data.get("git_commit", "")
    query = select(VersionInfo).where(VersionInfo.git_commit == git_commit)
    result = await db.execute(query)
    existing = result.scalar_one_or_none()
    if existing:
        return {"message": "该版本信息已存在", "version": VersionInfoResponse.model_validate(existing).model_dump()}

    version = VersionInfo(
        version=build_data.get("version", ""),
        git_commit=git_commit,
        git_branch=build_data.get("git_branch", ""),
        git_author=build_data.get("git_author", ""),
        git_message=build_data.get("git_message", ""),
        git_date=build_data.get("git_date", ""),
        change_summary=build_data.get("change_summary", ""),
    )
    db.add(version)
    await db.commit()
    await db.refresh(version)

    return {"message": "版本信息导入成功", "version": VersionInfoResponse.model_validate(version).model_dump()}

@router.delete("/{version_id}")
async def delete_version(
    version_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != '管理员':
        raise HTTPException(status_code=403, detail="权限不足，只有管理员可以删除版本信息")

    query = select(VersionInfo).where(VersionInfo.id == version_id)
    result = await db.execute(query)
    version = result.scalar_one_or_none()
    if not version:
        raise HTTPException(status_code=404, detail="版本信息不存在")

    await db.delete(version)
    await db.commit()
    return {"success": True, "message": "版本信息已删除"}
