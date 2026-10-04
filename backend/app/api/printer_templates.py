from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File, Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from typing import List, Optional
from datetime import datetime
from urllib.parse import quote
import os
import uuid
import json
import base64
import re
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


# ====== 模板导出/导入功能 ======

# 从布局配置 JSON 中收集所有引用的图片文件名
def _collect_image_filenames(layout_config_str):
    """递归遍历布局配置 JSON(嵌套 dict/list 结构)收集所有引用的 uploads/templates/ 图片文件名"""
    if not layout_config_str:
        return []
    try:
        config = json.loads(layout_config_str) if isinstance(layout_config_str, str) else layout_config_str
    except Exception:
        return []

    filenames = []
    seen = set()  # 去重

    def walk(obj):
        if isinstance(obj, str):
            # 匹配 /uploads/templates/xxx.png 形式(可能带 ?t=xxx 时间戳后缀)
            for m in re.finditer(r'/uploads/templates/([^?/]+\.(?:png|jpg|jpeg|gif|bmp|webp|svg))', obj, re.IGNORECASE):
                fname = m.group(1)
                if fname not in seen:
                    seen.add(fname)
                    filenames.append(fname)
        elif isinstance(obj, dict):
            for v in obj.values():
                walk(v)
        elif isinstance(obj, list):
            for v in obj:
                walk(v)

    walk(config)
    return filenames


# 将图片文件转为 data URI
def _image_to_data_uri(filepath):
    if not os.path.exists(filepath):
        return None
    ext = os.path.splitext(filepath)[1].lower().lstrip('.')
    mime_map = {
        'png': 'image/png', 'jpg': 'image/jpeg', 'jpeg': 'image/jpeg',
        'gif': 'image/gif', 'bmp': 'image/bmp', 'webp': 'image/webp', 'svg': 'image/svg+xml'
    }
    mime = mime_map.get(ext, 'application/octet-stream')
    with open(filepath, 'rb') as f:
        data = base64.b64encode(f.read()).decode('ascii')
    return f"data:{mime};base64,{data}"


def _build_export_dict(templates):
    """构造导出 JSON 结构"""
    return {
        "version": "1.0",
        "exported_at": datetime.utcnow().isoformat() + "Z",
        "template_count": len(templates),
        "templates": [_build_template_export_dict(t) for t in templates]
    }


def _build_template_export_dict(template):
    """单个模板的导出结构"""
    layout = template.布局配置 or ""
    image_filenames = _collect_image_filenames(layout)
    images = {}
    for fname in image_filenames:
        filepath = os.path.join(UPLOAD_DIR, fname)
        data_uri = _image_to_data_uri(filepath)
        if data_uri:
            images[fname] = data_uri
    return {
        "模板名称": template.模板名称,
        "模板类型": template.模板类型,
        "牌位类型": template.牌位类型,
        "布局配置": layout,
        "默认参数": template.默认参数,
        "是否启用": template.是否启用 if template.是否启用 is not None else 1,
        "是否默认": 0,  # 导入后不强制为默认,由用户在新环境手动设置
        "备注": template.备注,
        "images": images
    }


@router.get("/export-all")
async def export_all_templates(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出所有启用的打印模板为 JSON 文件"""
    if not check_permission(current_user, "print_template"):
        raise HTTPException(status_code=403, detail="无权限操作")
    result = await db.execute(select(PrinterTemplate).where(PrinterTemplate.是否启用 == 1))
    templates = result.scalars().all()
    export_data = _build_export_dict(templates)
    content = json.dumps(export_data, ensure_ascii=False, indent=2)
    # 中文文件名用 RFC 5987 filename*=UTF-8'' 形式,避免 latin-1 编码失败
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    ascii_name = f"templates_export_{ts}.json"
    utf8_name = quote(f"打印模板_导出_{ts}.json")
    return Response(
        content=content.encode('utf-8'),
        media_type='application/json',
        headers={
            'Content-Disposition': f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{utf8_name}"
        }
    )


@router.get("/{template_id}/export")
async def export_template(
    template_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """导出单个打印模板为 JSON 文件"""
    if not check_permission(current_user, "print_template"):
        raise HTTPException(status_code=403, detail="无权限操作")
    result = await db.execute(select(PrinterTemplate).where(PrinterTemplate.id == template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")
    export_data = _build_export_dict([template])
    content = json.dumps(export_data, ensure_ascii=False, indent=2)
    # 文件名安全处理: 仅保留中文/字母/数字/下划线
    safe_name = re.sub(r'[^\w\u4e00-\u9fa5]', '_', template.模板名称 or "template")
    ts = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
    ascii_name = f"template_{template_id}_{ts}.json"
    # 中文文件名用 RFC 5987 filename*=UTF-8'' 形式,避免 latin-1 编码失败
    utf8_name = quote(f"打印模板_{safe_name}_{ts}.json")
    return Response(
        content=content.encode('utf-8'),
        media_type='application/json',
        headers={
            'Content-Disposition': f"attachment; filename=\"{ascii_name}\"; filename*=UTF-8''{utf8_name}"
        }
    )


@router.post("/import")
async def import_templates(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """从 JSON 文件导入打印模板"""
    if not check_permission(current_user, "print_template"):
        raise HTTPException(status_code=403, detail="无权限操作")

    if not file.filename or not file.filename.lower().endswith('.json'):
        raise HTTPException(status_code=400, detail="仅支持 .json 文件")

    content = await file.read()
    if len(content) > 50 * 1024 * 1024:
        raise HTTPException(status_code=400, detail="文件大小不能超过50MB")

    try:
        data = json.loads(content.decode('utf-8'))
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"JSON 解析失败: {str(e)}")

    if not isinstance(data, dict) or data.get("version") != "1.0":
        raise HTTPException(status_code=400, detail="无效的模板导出文件格式(缺少 version=1.0 标识)")

    templates_data = data.get("templates")
    if not isinstance(templates_data, list) or len(templates_data) == 0:
        raise HTTPException(status_code=400, detail="文件中没有可导入的模板")

    # 查询当前已存在的模板名,用于冲突检测
    existing_result = await db.execute(select(PrinterTemplate.模板名称))
    existing_names = set(r[0] for r in existing_result.fetchall())

    imported = []
    skipped = []
    for idx, tpl in enumerate(templates_data):
        if not isinstance(tpl, dict):
            skipped.append({"index": idx, "reason": "结构非法"})
            continue
        name = tpl.get("模板名称") or f"导入模板_{idx}"
        # 名称冲突: 自动加后缀
        final_name = name
        suffix_counter = 1
        while final_name in existing_names:
            final_name = f"{name}(导入{suffix_counter})"
            suffix_counter += 1
        existing_names.add(final_name)

        # 写入图片到 UPLOAD_DIR (生成新文件名避免覆盖现有文件)
        images_map = tpl.get("images") or {}
        # 旧文件名 -> 新 URL
        image_url_remap = {}
        for old_fname, data_uri in images_map.items():
            if not isinstance(data_uri, str) or not data_uri.startswith('data:'):
                continue
            # 解析 data URI: data:image/png;base64,xxxx
            m = re.match(r'data:([\w/\-+]+);base64,(.+)', data_uri, re.DOTALL)
            if not m:
                continue
            mime = m.group(1)
            b64data = m.group(2)
            ext_map = {
                'image/png': '.png', 'image/jpeg': '.jpg', 'image/jpg': '.jpg',
                'image/gif': '.gif', 'image/bmp': '.bmp',
                'image/webp': '.webp', 'image/svg+xml': '.svg'
            }
            ext = ext_map.get(mime, '.png')
            new_filename = f"{uuid.uuid4().hex}{ext}"
            new_filepath = os.path.join(UPLOAD_DIR, new_filename)
            try:
                with open(new_filepath, 'wb') as f:
                    f.write(base64.b64decode(b64data))
                image_url_remap[old_fname] = f"/uploads/templates/{new_filename}"
            except Exception as e:
                # 单张图片写入失败不阻断整个导入流程,只是跳过该图片
                continue

        # 更新布局配置中的图片 URL (旧 filename 替换为新 URL)
        layout = tpl.get("布局配置") or ""
        for old_fname, new_url in image_url_remap.items():
            # 替换字符串中所有 /uploads/templates/old_fname(可能带 ?v=...) 为新 URL
            layout = re.sub(
                r'/uploads/templates/' + re.escape(old_fname) + r'(\?[^"\s]*)?',
                new_url,
                layout
            )

        template = PrinterTemplate(
            模板名称=final_name,
            模板类型=tpl.get("模板类型") or "牌位",
            牌位类型=tpl.get("牌位类型"),
            布局配置=layout,
            默认参数=tpl.get("默认参数"),
            是否启用=tpl.get("是否启用", 1) if tpl.get("是否启用", 1) in (0, 1) else 1,
            是否默认=0,  # 导入后不设为默认,避免覆盖现有默认模板
            备注=tpl.get("备注"),
        )
        if current_user.temple_id:
            template.temple_id = current_user.temple_id
        db.add(template)
        imported.append({"模板名称": final_name, "原名称": name})

    await db.commit()
    return {
        "message": f"导入完成: 成功 {len(imported)} 个, 跳过 {len(skipped)} 个",
        "imported_count": len(imported),
        "skipped_count": len(skipped),
        "imported": imported,
        "skipped": skipped
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
