---
name: "build-exe"
description: "Builds the temple-management project into a standalone Windows exe. Invoke when user asks to '打包', '重新打包', 'build exe', or '代码有改动,重新打包'."
---

# Build EXE

This skill packages the temple-management project (Vue.js frontend + FastAPI backend) into a standalone Windows exe using PyInstaller.

## Project Location

- Project root: `E:\Project\Print_tool\temple-management`
- Frontend: `E:\Project\Print_tool\temple-management\frontend`
- Backend: `E:\Project\Print_tool\temple-management\backend`
- Spec file: `E:\Project\Print_tool\temple-management\temple_management.spec`
- Entry point: `E:\Project\Print_tool\temple-management\standalone_main.py`
- Icon: `E:\Project\Print_tool\yuantong_logo.ico`
- Output: `E:\Project\Print_tool\temple-management\dist\缘通寺院信息管理系统.exe`

## Environment

- Python: `C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe` (3.11.9)
- PyInstaller: 6.19.0 (installed globally in Python 3.11, NOT in a venv)
- Node.js: `C:\Program Files\nodejs\node.exe` (v24.11.1)
- All backend dependencies (fastapi, uvicorn, sqlalchemy, aiosqlite, pystray, Pillow, reportlab, PyMuPDF, openpyxl, pywin32, passlib, pydantic, pydantic-settings, python-jose, python-multipart, bcrypt) are pre-installed in Python 3.11
- Frontend `dist/` already exists from previous build; only rebuild if frontend code changed

## Build Steps

Execute the following steps in order:

### Step 1: Build Frontend (only if frontend code changed)

```powershell
cd "E:\Project\Print_tool\temple-management\frontend" ; npm run build
```

If the build fails with import errors (e.g., module not found), check the error message and fix the import path, then retry.

If only backend code changed, skip this step.

### Step 2: Stop Running Instances & Clean Build Artifacts & Run PyInstaller

```powershell
Get-Process | Where-Object { $_.ProcessName -like '*缘通*' } | Stop-Process -Force -ErrorAction SilentlyContinue; Start-Sleep -Seconds 2; Remove-Item -Recurse -Force "E:\Project\Print_tool\temple-management\build" -ErrorAction SilentlyContinue; Remove-Item -Force "E:\Project\Print_tool\temple-management\dist\缘通寺院信息管理系统.exe" -ErrorAction SilentlyContinue; cd "E:\Project\Print_tool\temple-management" ; & "C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe" -m PyInstaller "E:\Project\Print_tool\temple-management\temple_management.spec" --noconfirm
```

### Step 3: Verify Output

```powershell
Get-Item "E:\Project\Print_tool\temple-management\dist\缘通寺院信息管理系统.exe" | Select-Object Name, @{N='SizeMB';E={[math]::Round($_.Length/1MB,2)}}
```

Expected size: ~61 MB. If significantly larger (e.g., 141 MB), check that `uploads/templates` is NOT included in the spec file's `datas` section.

## Important Notes

- PyInstaller must be invoked via `C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe -m PyInstaller` because Python 3.11 is not on PATH; do NOT use Python 3.12 (which lacks the required packages)
- The spec file does NOT include `uploads/templates` in datas (those are user-generated files stored alongside the exe)
- The icon file `yuantong_logo.ico` is located at `E:\Project\Print_tool\yuantong_logo.ico` (parent of project root); the spec file references it via `os.path.dirname(os.path.abspath('.'))`
- The exe uses a named mutex (`Global\TempleManagement_SingleInstance`) for single-instance detection
- The database (`temple.db`) is stored at `dist\database\` alongside the exe, not bundled inside
- Always stop running exe instances before rebuilding, otherwise the dist directory may be locked
- The spec file uses single-exe mode (onefile: `EXE` with `a.zipfiles` + `a.datas` bundled into one exe)
- If pip mirror (tuna) returns 403, use official PyPI: `pip install -i https://pypi.org/simple/ <package>`
