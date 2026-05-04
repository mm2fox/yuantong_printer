import os
import uuid
import platform
import asyncio
from functools import partial
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional
from ..models.user import User
from .auth import get_current_user

router = APIRouter(prefix="/api/scanner", tags=["扫描仪"])

UPLOAD_DIR = os.environ.get("TEMPLE_UPLOAD_DIR", os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))), "uploads"))
UPLOAD_DIR = os.path.join(UPLOAD_DIR, "templates")
os.makedirs(UPLOAD_DIR, exist_ok=True)


class ScanRequest(BaseModel):
    device_id: Optional[str] = None
    resolution: int = 200
    color_mode: int = 1
    auto_rotate: bool = True


def _list_scanners():
    import win32com.client
    manager = win32com.client.Dispatch("WIA.DeviceManager")
    devices = []
    for device_info in manager.DeviceInfos:
        if device_info.Type == 1:
            device_id = device_info.DeviceID
            name = "未知设备"
            for prop in device_info.Properties:
                if prop.PropertyID == 7:
                    name = prop.Value
                    break
            devices.append({"id": device_id, "name": name})
    return devices


def _do_scan(device_id, resolution, color_mode, auto_rotate):
    import win32com.client
    from PIL import Image

    manager = win32com.client.Dispatch("WIA.DeviceManager")

    device = None
    if device_id:
        for device_info in manager.DeviceInfos:
            if device_info.DeviceID == device_id:
                device = device_info.Connect()
                break
    else:
        dialog = win32com.client.Dispatch("WIA.CommonDialog")
        device = dialog.ShowSelectDevice(
            TypeID=1,
            KeepConnected=True,
            CancelError=False
        )

    if not device:
        raise ValueError("未选择扫描仪或未找到设备")

    item = None
    for i in device.Items:
        item = i
        break

    if not item:
        raise ValueError("扫描仪无可用的扫描项")

    for prop in item.Properties:
        try:
            if prop.PropertyID == 6146:
                prop.Value = color_mode
            elif prop.PropertyID == 6147:
                prop.Value = resolution
        except:
            pass

    image = item.Transfer()

    filename = f"scan_{uuid.uuid4().hex}.png"
    filepath = os.path.join(UPLOAD_DIR, filename)

    image.SaveFile(filepath)

    with Image.open(filepath) as img:
        pixel_width, pixel_height = img.size

    mm_width = round(pixel_width * 25.4 / resolution, 1)
    mm_height = round(pixel_height * 25.4 / resolution, 1)

    return {
        "url": f"/uploads/templates/{filename}",
        "filename": filename,
        "pixelWidth": pixel_width,
        "pixelHeight": pixel_height,
        "mmWidth": mm_width,
        "mmHeight": mm_height,
        "dpi": resolution
    }


@router.get("/devices")
async def list_scanners(current_user: User = Depends(get_current_user)):
    if platform.system() != 'Windows':
        raise HTTPException(status_code=400, detail="扫描功能仅支持Windows系统")

    try:
        loop = asyncio.get_event_loop()
        devices = await loop.run_in_executor(None, _list_scanners)
        return devices
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取扫描仪列表失败: {str(e)}")


@router.post("/scan")
async def scan_document(
    req: ScanRequest,
    current_user: User = Depends(get_current_user)
):
    if platform.system() != 'Windows':
        raise HTTPException(status_code=400, detail="扫描功能仅支持Windows系统")

    try:
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            None,
            partial(_do_scan, req.device_id, req.resolution, req.color_mode, req.auto_rotate)
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        error_msg = str(e)
        if "没有注册类" in error_msg or "Class not registered" in error_msg:
            raise HTTPException(status_code=500, detail="系统未安装WIA组件，请确认已安装扫描仪驱动")
        if "被用户取消" in error_msg or "cancelled" in error_msg.lower():
            raise HTTPException(status_code=400, detail="扫描操作被取消")
        raise HTTPException(status_code=500, detail=f"扫描失败: {error_msg}")
