import os
import json
import tempfile
import platform
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from ..core.database import get_db
from ..models.user import User
from ..models.printer_template import PrinterTemplate
from .auth import get_current_user

UPLOAD_DIR = os.environ.get(
    "TEMPLE_UPLOAD_DIR",
    os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploads")
)

router = APIRouter(prefix="/api/silent-print", tags=["静默打印"])


class SilentPrintRecord(BaseModel):
    id: Optional[int] = None
    xm1: Optional[str] = None
    xm2: Optional[str] = None
    xm3: Optional[str] = None
    xm4: Optional[str] = None
    xm5: Optional[str] = None
    fahui_name: Optional[str] = None
    zuoweinum: Optional[str] = None
    paiwei_type: Optional[str] = None
    shizhu_name: Optional[str] = None


class SilentPrintRequest(BaseModel):
    template_id: int
    records: List[SilentPrintRecord]
    printer_name: Optional[str] = None


class GeneratePdfFromConfigRequest(BaseModel):
    config: dict
    records: List[SilentPrintRecord]
    filename: Optional[str] = "preview"


_registered_fonts = {}


def register_chinese_fonts():
    global _registered_fonts
    if _registered_fonts:
        return _registered_fonts

    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont

    font_specs = [
        ('STXingkai', ['STXINGKA.TTF', 'stxingka.ttf']),
        ('SimSun', ['simsun.ttc', 'SIMSUN.TTC']),
        ('SimHei', ['simhei.ttf', 'SIMHEI.TTF']),
        ('KaiTi', ['kaiti.ttf', 'KAITI.TTF']),
    ]

    for name, paths in font_specs:
        for path in paths:
            try:
                pdfmetrics.registerFont(TTFont(name, path))
                _registered_fonts[name] = True
                break
            except Exception:
                continue

    return _registered_fonts


def get_font_name(requested_font):
    registered = register_chinese_fonts()
    if requested_font in registered:
        return requested_font
    for fallback in ['STXingkai', 'SimHei', 'SimSun', 'KaiTi']:
        if fallback in registered:
            return fallback
    return 'Helvetica'


def px_to_pt(px):
    return px * 0.75


def resolve_image_path(url):
    if not url:
        return None
    clean_url = url.split('?')[0]
    if clean_url.startswith('/uploads/'):
        rel_path = clean_url.lstrip('/')
        return os.path.join(UPLOAD_DIR, rel_path.replace('uploads/', '', 1))
    return None


def draw_ruler(c, page_width, page_height, mm_unit):
    c.saveState()

    w_mm = int(page_width / mm_unit)
    h_mm = int(page_height / mm_unit)

    c.setStrokeColor((1, 0, 0))
    c.setLineWidth(0.5)
    for mm_val in range(0, w_mm + 1, 10):
        x = mm_val * mm_unit
        is_major = mm_val % 50 == 0
        tick_len = 20 if is_major else 10
        c.line(x, page_height, x, page_height - tick_len)
        if is_major:
            c.setFillColor((1, 0, 0))
            c.setFont('Helvetica', 8)
            c.drawCentredString(x, page_height - 30, f'{mm_val}')

    c.setStrokeColor((1, 0, 0))
    c.setLineWidth(0.5)
    for mm_val in range(0, h_mm + 1, 10):
        y = page_height - mm_val * mm_unit
        is_major = mm_val % 50 == 0
        tick_len = 20 if is_major else 10
        c.line(0, y, tick_len, y)
        if is_major:
            c.setFillColor((1, 0, 0))
            c.setFont('Helvetica', 8)
            c.drawString(30, y - 3, f'{mm_val}')

    c.setStrokeColor((0, 0.47, 1))
    c.setLineWidth(0.8)
    c.setDash(6, 4)

    for cm in range(1, w_mm // 10):
        x = cm * 10 * mm_unit
        c.line(x, 0, x, page_height)

    for cm in range(1, h_mm // 10):
        y = page_height - cm * 10 * mm_unit
        c.line(0, y, page_width, y)

    c.setDash()
    c.restoreState()


def draw_vertical_text(c, text, x, y, font_name, font_size_pt, line_height_factor=1.3):
    for ch in text:
        c.setFont(font_name, font_size_pt)
        c.drawCentredString(x, y, ch)
        y -= font_size_pt * line_height_factor
    return y


def split_name_suffix(name):
    if not name:
        return '', ''
    name = name.strip()
    # 用第一个空格分割：空格前为姓名（需对齐），空格后为后缀（如"阖家 长生"）
    first_space_idx = name.find(' ')
    if first_space_idx >= 0:
        name_part = name[:first_space_idx]
        # 后缀中的空格转为全角空格，在竖排时作为间隔
        suffix = name[first_space_idx + 1:].replace(' ', '\u3000')
        return name_part, suffix
    return name, ''


def pad_name_part(name_part, max_len):
    if len(name_part) >= max_len:
        return name_part
    padding = max_len - len(name_part)
    gaps = len(name_part) - 1
    if gaps <= 0:
        return name_part + '\u3000' * padding
    base = padding // gaps
    extra = padding % gaps
    result = ''
    for i, ch in enumerate(name_part):
        result += ch
        if i < gaps:
            spaces = base + (1 if i < extra else 0)
            result += '\u3000' * spaces
    return result


def generate_template_pdf(config: dict, records: list, output_path: str):
    from reportlab.pdfgen import canvas
    from reportlab.lib.units import mm

    layout = config.get('layout', {})
    display_items = config.get('displayItems', [])

    page_width = layout.get('pageWidth', 210) * mm
    page_height = layout.get('pageHeight', 297) * mm

    if layout.get('nameFontSize') is None and layout.get('nameFontSize1') is not None:
        layout['nameFontSize'] = layout.get('nameFontSize3', 44)
        layout['nameSpacing'] = layout.get('nameSpacing', 20)
        layout['namesTopPct'] = layout.get('namesTopPct', 25)
        layout['namesLeftPct'] = layout.get('namesLeftPct', 10)
        layout['namesWidthPct'] = layout.get('namesWidthPct', 80)
        layout['namesHeightPct'] = layout.get('namesHeightPct', 55)
        layout['yangshangSpacing'] = layout.get('yangshangSpacing', 5)

    requested_font = layout.get('fontFamily', 'STXingkai')
    font_name = get_font_name(requested_font)

    name_font_size_px = layout.get('nameFontSize', 52)
    name_font_size = px_to_pt(name_font_size_px)
    name_spacing_px = layout.get('nameSpacing', 20)
    name_spacing = px_to_pt(name_spacing_px)
    name_char_spacing_ratio = layout.get('nameCharSpacing', 1.3)

    names_top_pct = layout.get('namesTopPct', 25)
    names_left_pct = layout.get('namesLeftPct', 10)
    names_width_pct = layout.get('namesWidthPct', 80)
    names_height_pct = layout.get('namesHeightPct', 55)

    yangshang_font_size_px = layout.get('yangshangFontSize', 18)
    yangshang_font_size = px_to_pt(yangshang_font_size_px)
    yangshang_spacing_px = layout.get('yangshangSpacing', 5)
    yangshang_spacing = px_to_pt(yangshang_spacing_px)
    yangshang_top_pct = layout.get('yangshangTopPct', 25)
    yangshang_left_pct = layout.get('yangshangLeftPct', 2)
    yangshang_height_pct = layout.get('yangshangHeightPct', 55)

    seat_font_size_px = layout.get('seatFontSize', 24)
    seat_font_size = px_to_pt(seat_font_size_px)
    bottom_top_pct = layout.get('bottomTopPct', 90)
    bottom_left_pct = layout.get('bottomLeftPct', 50)

    template_type = config.get('_template_type', '延生牌位')
    is_wangsheng = template_type == '往生牌位'

    print_offset_mm = layout.get('printOffsetY', 0)
    print_offset_pt = print_offset_mm * mm

    print_background = layout.get('printBackground', False)
    background_image_url = layout.get('backgroundImage', '')
    background_opacity = layout.get('backgroundOpacity', 30) / 100.0
    print_ruler = layout.get('printRuler', False)

    c = canvas.Canvas(output_path, pagesize=(page_width, page_height))

    for record in records:
        if print_background and background_image_url:
            image_path = resolve_image_path(background_image_url)
            if image_path and os.path.exists(image_path):
                try:
                    from PIL import Image as PILImage
                    img = PILImage.open(image_path).convert('RGBA')
                    white_bg = PILImage.new('RGBA', img.size, (255, 255, 255, 255))
                    result = PILImage.blend(white_bg, img, background_opacity)
                    result = result.convert('RGB')
                    tmp_path = tempfile.mktemp(suffix='.png')
                    result.save(tmp_path, 'PNG')
                    c.drawImage(tmp_path, 0, 0, width=page_width, height=page_height,
                                preserveAspectRatio=True, anchor='c')
                    try:
                        os.unlink(tmp_path)
                    except Exception:
                        pass
                except Exception as e:
                    print(f"底图绘制失败: {e}")

        if print_ruler:
            draw_ruler(c, page_width, page_height, mm)

        names = []
        yangshang_names = []
        if is_wangsheng:
            names = [record.xm1, record.xm2, record.xm3]
            yangshang_names = [record.xm4, record.xm5]
        else:
            names = [record.xm1, record.xm2, record.xm3, record.xm4, record.xm5]

        names = [n for n in names if n]
        yangshang_names = [n for n in yangshang_names if n]
        name_count = len(names)

        area_left = page_width * names_left_pct / 100
        area_top = page_height * (1 - names_top_pct / 100) + print_offset_pt
        area_width = page_width * names_width_pct / 100
        area_height = page_height * names_height_pct / 100
        area_bottom = area_top - area_height

        if name_count > 0:
            total_name_width = name_count * name_font_size + (name_count - 1) * name_spacing
            if total_name_width > area_width:
                actual_spacing = (area_width - name_count * name_font_size) / max(name_count - 1, 1)
            else:
                actual_spacing = name_spacing

            total_used_width = name_count * name_font_size + (name_count - 1) * actual_spacing
            start_x = area_left + (area_width - total_used_width) / 2 + name_font_size / 2

            parsed_names = [split_name_suffix(n) for n in names]
            max_name_len = max((len(np) for np, sf in parsed_names), default=0)

            for i, (name_part, suffix) in enumerate(parsed_names):
                x = start_x + (name_count - 1 - i) * (name_font_size + actual_spacing)
                y = area_top - name_font_size * 0.75
                padded = pad_name_part(name_part, max_name_len)
                full_text = padded + suffix
                for ch in full_text:
                    if ch == '\u3000':
                        y -= name_font_size * name_char_spacing_ratio
                        continue
                    c.setFont(font_name, name_font_size)
                    c.drawCentredString(x, y, ch)
                    y -= name_font_size * name_char_spacing_ratio
                    if y < area_bottom:
                        break

        if is_wangsheng and yangshang_names and 'yangshang' in display_items:
            ys_area_top = page_height * (1 - yangshang_top_pct / 100) + print_offset_pt
            ys_area_left = page_width * yangshang_left_pct / 100
            ys_area_height = page_height * yangshang_height_pct / 100
            ys_area_bottom = ys_area_top - ys_area_height

            ys_start_x = ys_area_left + yangshang_font_size / 2
            ys_y = ys_area_top - yangshang_font_size * 0.75

            ys_y = draw_vertical_text(c, '阳上', ys_start_x, ys_y, font_name, yangshang_font_size)

            for name in yangshang_names:
                ys_x = ys_start_x + yangshang_font_size + yangshang_spacing
                ys_y = ys_area_top - yangshang_font_size * 0.75
                ys_y = draw_vertical_text(c, name, ys_x, ys_y, font_name, yangshang_font_size)
                ys_start_x = ys_x

        bottom_y = page_height * (1 - bottom_top_pct / 100) + print_offset_pt - seat_font_size * 0.75
        bottom_x = page_width * bottom_left_pct / 100
        bottom_text = ''
        if 'shizhu_name' in display_items and record.shizhu_name:
            bottom_text += record.shizhu_name + ' '
        if 'fahui_name' in display_items and record.fahui_name:
            bottom_text += record.fahui_name + ' '
        if 'seat' in display_items and record.zuoweinum:
            bottom_text += str(record.zuoweinum)
        if bottom_text:
            c.setFont(font_name, seat_font_size)
            c.drawCentredString(bottom_x, bottom_y, bottom_text)

        c.showPage()

    c.save()


def print_pdf_windows(pdf_path: str, printer_name: Optional[str] = None, page_width_mm: float = None, page_height_mm: float = None):
    if platform.system() != 'Windows':
        return False

    try:
        import win32print
        import win32con
        import win32ui
        import fitz
        from PIL import Image, ImageWin

        if not printer_name:
            printer_name = win32print.GetDefaultPrinter()

        printer_handle = win32print.OpenPrinter(printer_name)
        printer_info = win32print.GetPrinter(printer_handle, 2)
        original_devmode = printer_info['pDevMode']

        new_devmode = win32print.GetPrinter(printer_handle, 2)['pDevMode']
        if page_width_mm and page_height_mm:
            new_devmode.Fields = original_devmode.Fields | win32con.DM_PAPERSIZE | win32con.DM_PAPERLENGTH | win32con.DM_PAPERWIDTH
            new_devmode.PaperSize = 256
            new_devmode.PaperWidth = int(page_width_mm * 10)
            new_devmode.PaperLength = int(page_height_mm * 10)
        try:
            win32print.DocumentProperties(
                0, printer_handle, printer_name,
                new_devmode, new_devmode,
                win32con.DM_IN_BUFFER | win32con.DM_OUT_BUFFER
            )
        except Exception:
            pass

        hdc = win32ui.CreateDC()
        hdc.CreatePrinterDC(printer_name)

        printable_width = hdc.GetDeviceCaps(win32con.HORZRES)
        printable_height = hdc.GetDeviceCaps(win32con.VERTRES)
        offset_x = hdc.GetDeviceCaps(win32con.PHYSICALOFFSETX)
        offset_y = hdc.GetDeviceCaps(win32con.PHYSICALOFFSETY)
        hres = hdc.GetDeviceCaps(win32con.LOGPIXELSX)
        vres = hdc.GetDeviceCaps(win32con.LOGPIXELSY)

        doc = fitz.open(pdf_path)
        hdc.StartDoc(os.path.basename(pdf_path))

        for page in doc:
            page_rect = page.rect
            pdf_width_pt = page_rect.width
            pdf_height_pt = page_rect.height

            zoom = hres / 72
            mat = fitz.Matrix(zoom, zoom)
            pix = page.get_pixmap(matrix=mat, alpha=False)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            img_w, img_h = img.size

            scale_x = printable_width / img_w if img_w > 0 else 1.0
            scale_y = printable_height / img_h if img_h > 0 else 1.0
            scale = min(scale_x, scale_y, 1.0)

            draw_w = int(img_w * scale)
            draw_h = int(img_h * scale)
            draw_x = (printable_width - draw_w) // 2
            draw_y = (printable_height - draw_h) // 2

            hdc.StartPage()
            dib = ImageWin.Dib(img)
            dib.draw(hdc.GetHandleOutput(), (draw_x, draw_y, draw_x + draw_w, draw_y + draw_h))
            hdc.EndPage()

        hdc.EndDoc()
        hdc.DeleteDC()
        doc.close()

        try:
            printer_info = win32print.GetPrinter(printer_handle, 2)
            printer_info['pDevMode'] = original_devmode
            win32print.SetPrinter(printer_handle, 2, printer_info, 0)
        except Exception:
            pass

        try:
            win32print.ClosePrinter(printer_handle)
        except Exception:
            pass

        return True

    except Exception as e:
        print(f"打印失败: {e}")
        return False


@router.post("")
async def silent_print(
    req: SilentPrintRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if platform.system() != 'Windows':
        raise HTTPException(status_code=400, detail="静默打印仅支持Windows系统")

    result = await db.execute(select(PrinterTemplate).where(PrinterTemplate.id == req.template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    try:
        config = json.loads(template.布局配置) if template.布局配置 else {}
    except Exception:
        config = {}

    config['_template_type'] = template.模板类型

    layout = config.get('layout', {})
    page_width_mm = layout.get('pageWidth', 210)
    page_height_mm = layout.get('pageHeight', 297)

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_path = tmp_file.name

        generate_template_pdf(config, req.records, pdf_path)
        success = print_pdf_windows(pdf_path, req.printer_name, page_width_mm, page_height_mm)

        try:
            os.unlink(pdf_path)
        except Exception:
            pass

        if success:
            return {"message": f"已发送 {len(req.records)} 条打印任务"}
        else:
            raise HTTPException(status_code=500, detail="打印失败")

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"打印过程出错: {str(e)}")


@router.post("/generate-pdf")
async def generate_pdf(
    req: SilentPrintRequest,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    result = await db.execute(select(PrinterTemplate).where(PrinterTemplate.id == req.template_id))
    template = result.scalar_one_or_none()
    if not template:
        raise HTTPException(status_code=404, detail="模板不存在")

    try:
        config = json.loads(template.布局配置) if template.布局配置 else {}
    except Exception:
        config = {}

    config['_template_type'] = template.模板类型

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_path = tmp_file.name

        generate_template_pdf(config, req.records, pdf_path)

        return FileResponse(
            path=pdf_path,
            filename=f"print_{template.模板名称 or 'preview'}.pdf",
            media_type='application/pdf',
            background=None
        )

    except Exception as e:
        try:
            os.unlink(pdf_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"PDF生成失败: {str(e)}")


@router.post("/generate-pdf-from-config")
async def generate_pdf_from_config(
    req: GeneratePdfFromConfigRequest,
    current_user: User = Depends(get_current_user)
):
    config = req.config

    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_path = tmp_file.name

        generate_template_pdf(config, req.records, pdf_path)

        return FileResponse(
            path=pdf_path,
            filename=f"print_{req.filename}.pdf",
            media_type='application/pdf',
            background=None
        )

    except Exception as e:
        try:
            os.unlink(pdf_path)
        except Exception:
            pass
        raise HTTPException(status_code=500, detail=f"PDF生成失败: {str(e)}")
