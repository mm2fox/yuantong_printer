from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
import os
import uuid
from ..core.database import get_db
from ..models.user import User
from ..models.printer_template import PrinterTemplate
from ..schemas.printer_template import PrinterTemplateCreate, PrinterTemplateUpdate, PrinterTemplateResponse
from .auth import get_current_user

def check_permission(user: User, permission: str) -> bool:
    if user.role == "管理员":
        return True
    if user.permissions:
        perms = [p.strip() for p in user.permissions.split(",")]
        return permission in perms
    return False

UPLOAD_DIR = os.environ.get("TEMPLE_UPLOAD_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploads"))
UPLOAD_DIR = os.path.join(UPLOAD_DIR, "templates")
os.makedirs(UPLOAD_DIR, exist_ok=True)

router = APIRouter(prefix="/api/printer-templates", tags=["打印模板"])

@router.get("", response_model=List[PrinterTemplateResponse])
async def get_templates(
    template_type: Optional[str] = Query(None, description="模板类型"),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    query = select(PrinterTemplate).where(PrinterTemplate.是否启用 == 1)
    
    if template_type:
        query = query.where(PrinterTemplate.模板类型 == template_type)
    
    result = await db.execute(query)
    templates = result.scalars().all()
    return templates

@router.post("/upload-image")
async def upload_template_image(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if not check_permission(current_user, "print_template"):
        raise HTTPException(status_code=403, detail="无权限操作")
    
    allowed_types = ["image/jpeg", "image/png", "image/gif", "image/bmp", "image/webp"]
    if file.content_type not in allowed_types:
        raise HTTPException(status_code=400, detail="仅支持图片文件(JPG/PNG/GIF/BMP/WEBP)")
    
    ext = os.path.splitext(file.filename)[1] or ".png"
    filename = f"{uuid.uuid4().hex}{ext}"
    filepath = os.path.join(UPLOAD_DIR, filename)
    
    content = await file.read()
    if len(content) > 10 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="图片大小不能超过10MB")
    
    with open(filepath, "wb") as f:
        f.write(content)

    from PIL import Image
    with Image.open(filepath) as img:
        pixel_width, pixel_height = img.size
        dpi = img.info.get('dpi', (200, 200))
        dpi_x = int(dpi[0]) if dpi else 200

    mm_width = round(pixel_width * 25.4 / dpi_x, 1)
    mm_height = round(pixel_height * 25.4 / dpi_x, 1)

    return {
        "url": f"/uploads/templates/{filename}",
        "filename": filename,
        "pixelWidth": pixel_width,
        "pixelHeight": pixel_height,
        "mmWidth": mm_width,
        "mmHeight": mm_height,
        "dpi": dpi_x
    }

@router.post("/rotate-image")
async def rotate_template_image(
    data: dict,
    current_user: User = Depends(get_current_user)
):
    if not check_permission(current_user, "print_template"):
        raise HTTPException(status_code=403, detail="无权限操作")

    image_url = data.get("url", "")
    angle = data.get("angle", 90)

    if not image_url:
        raise HTTPException(status_code=400, detail="缺少图片URL")

    clean_url = image_url.split("?")[0]
    filename = os.path.basename(clean_url)
    filepath = os.path.join(UPLOAD_DIR, filename)

    if not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="图片文件不存在")

    from PIL import Image

    with Image.open(filepath) as img:
        if angle == 90:
            rotated_img = img.transpose(Image.ROTATE_270)
        elif angle == -90:
            rotated_img = img.transpose(Image.ROTATE_90)
        elif angle == 180:
            rotated_img = img.transpose(Image.ROTATE_180)
        else:
            raise HTTPException(status_code=400, detail="仅支持90度旋转")

        rotated_img.save(filepath)

        pixel_width, pixel_height = rotated_img.size
        dpi = rotated_img.info.get('dpi', (200, 200))
        dpi_x = int(dpi[0]) if dpi else 200

    mm_width = round(pixel_width * 25.4 / dpi_x, 1)
    mm_height = round(pixel_height * 25.4 / dpi_x, 1)

    return {
        "url": clean_url,
        "filename": filename,
        "pixelWidth": pixel_width,
        "pixelHeight": pixel_height,
        "mmWidth": mm_width,
        "mmHeight": mm_height,
        "dpi": dpi_x
    }

@router.get("/{template_id}", response_model=PrinterTemplateResponse)
async def get_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(PrinterTemplate).where(PrinterTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    return template

@router.post("", response_model=PrinterTemplateResponse)
async def create_template(
    template_data: PrinterTemplateCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not check_permission(current_user, "print_template"):
        raise HTTPException(status_code=403, detail="无权限操作")
    
    template = PrinterTemplate(**template_data.dict())
    if current_user.temple_id:
        template.temple_id = current_user.temple_id
    
    db.add(template)
    await db.commit()
    await db.refresh(template)
    return template

@router.put("/{template_id}", response_model=PrinterTemplateResponse)
async def update_template(
    template_id: int,
    template_data: PrinterTemplateUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not check_permission(current_user, "print_template"):
        raise HTTPException(status_code=403, detail="无权限操作")
    
    result = await db.execute(select(PrinterTemplate).where(PrinterTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    for key, value in template_data.dict(exclude_unset=True).items():
        setattr(template, key, value)
    
    await db.commit()
    await db.refresh(template)
    return template

@router.delete("/{template_id}")
async def delete_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not check_permission(current_user, "print_template"):
        raise HTTPException(status_code=403, detail="无权限操作")
    
    result = await db.execute(select(PrinterTemplate).where(PrinterTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    await db.delete(template)
    await db.commit()
    return {"message": "删除成功"}

@router.put("/{template_id}/set-default")
async def set_default_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if not check_permission(current_user, "print_template"):
        raise HTTPException(status_code=403, detail="无权限操作")
    
    result = await db.execute(select(PrinterTemplate).where(PrinterTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    
    result = await db.execute(
        select(PrinterTemplate).where(PrinterTemplate.模板类型 == template.模板类型)
    )
    same_type_templates = result.scalars().all()
    for t in same_type_templates:
        t.是否默认 = 0
    
    template.是否默认 = 1
    await db.commit()
    return {"message": "已设为默认"}

@router.post("/cleanup-images")
async def cleanup_unused_images(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    if not check_permission(current_user, "print_template"):
        raise HTTPException(status_code=403, detail="无权限操作")

    import json
    result = await db.execute(select(PrinterTemplate))
    templates = result.scalars().all()

    used_images = set()
    for t in templates:
        if t.布局配置:
            try:
                config = json.loads(t.布局配置) if isinstance(t.布局配置, str) else t.布局配置
                bg = config.get("backgroundImage", "")
                if bg:
                    used_images.add(os.path.basename(bg.split("?")[0]))
            except:
                pass

    removed = []
    for f in os.listdir(UPLOAD_DIR):
        if f.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg')):
            if f not in used_images:
                os.remove(os.path.join(UPLOAD_DIR, f))
                removed.append(f)

    return {"removed": removed, "count": len(removed)}
