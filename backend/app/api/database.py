from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text, select
from ..core.database import get_db
from ..models.user import User
from ..models.fahui_user import FahuiUser
from ..models.fahui_record import FahuiRecord
from ..models.fahui_info import FahuiInfo
from .auth import get_current_user
import os
import shutil
import sqlite3
import tempfile
from datetime import datetime
from pathlib import Path

router = APIRouter(prefix="/api/database", tags=["数据库管理"])

DATABASE_PATH = Path(os.environ.get("TEMPLE_DB_PATH", str(Path(__file__).parent.parent.parent.parent / "database" / "temple.db")))
BACKUP_DIR = Path(os.environ.get("TEMPLE_BACKUP_DIR", str(Path(__file__).parent.parent.parent.parent / "backups")))

EXCLUDED_TABLES = ['users', 'permissions']


def _read_excel_file(filepath: Path):
    if filepath.suffix.lower() == '.xls':
        import xlrd
        wb = xlrd.open_workbook(str(filepath))
        sh = wb.sheet_by_index(0)
        headers = [sh.cell_value(0, j) for j in range(sh.ncols)]
        rows = []
        for i in range(1, sh.nrows):
            row = {}
            for j in range(sh.ncols):
                val = sh.cell_value(i, j)
                if isinstance(val, float) and val == int(val):
                    val = int(val)
                row[headers[j]] = val
            rows.append(row)
        return headers, rows
    elif filepath.suffix.lower() == '.xlsx':
        import openpyxl
        wb = openpyxl.load_workbook(str(filepath), read_only=True)
        ws = wb.active
        data = list(ws.iter_rows(values_only=True))
        wb.close()
        if not data:
            return [], []
        headers = [str(h) if h is not None else '' for h in data[0]]
        rows = []
        for row_data in data[1:]:
            row = {}
            for j, h in enumerate(headers):
                val = row_data[j] if j < len(row_data) else None
                if isinstance(val, float) and val == int(val):
                    val = int(val)
                row[h] = val
            rows.append(row)
        return headers, rows
    else:
        raise ValueError(f"不支持的文件格式: {filepath.suffix}")

@router.get("/info")
async def get_database_info(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != '管理员':
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        db_size = DATABASE_PATH.stat().st_size if DATABASE_PATH.exists() else 0
        
        tables = []
        result = await db.execute(text("SELECT name FROM sqlite_master WHERE type='table'"))
        table_names = [row[0] for row in result]
        
        for table_name in table_names:
            count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
            count = count_result.scalar()
            tables.append({"name": table_name, "count": count})
        
        return {
            "database_path": str(DATABASE_PATH),
            "database_size": db_size,
            "database_size_mb": round(db_size / (1024 * 1024), 2),
            "tables": tables,
            "backup_dir": str(BACKUP_DIR),
            "backup_exists": BACKUP_DIR.exists()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取数据库信息失败: {str(e)}")

@router.post("/backup")
async def backup_database(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != '管理员':
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        if not DATABASE_PATH.exists():
            raise HTTPException(status_code=404, detail="数据库文件不存在")
        
        BACKUP_DIR.mkdir(parents=True, exist_ok=True)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"temple_backup_{timestamp}.db"
        backup_path = BACKUP_DIR / backup_filename
        
        source_conn = sqlite3.connect(str(DATABASE_PATH))
        backup_conn = sqlite3.connect(str(backup_path))
        
        source_conn.backup(backup_conn)
        
        cursor = backup_conn.cursor()
        for table in EXCLUDED_TABLES:
            cursor.execute(f"DELETE FROM {table}")
        
        backup_conn.commit()
        backup_conn.close()
        source_conn.close()
        
        return {
            "success": True,
            "message": "数据库备份成功(已排除用户和权限表)",
            "backup_file": backup_filename,
            "backup_path": str(backup_path),
            "backup_size": backup_path.stat().st_size
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"备份失败: {str(e)}")

@router.get("/backups")
async def list_backups(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != '管理员':
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        if not BACKUP_DIR.exists():
            return {"backups": []}
        
        backups = []
        for backup_file in BACKUP_DIR.glob("temple_backup_*.db"):
            stat = backup_file.stat()
            backups.append({
                "filename": backup_file.name,
                "path": str(backup_file),
                "size": stat.st_size,
                "size_mb": round(stat.st_size / (1024 * 1024), 2),
                "created_at": datetime.fromtimestamp(stat.st_ctime).isoformat()
            })
        
        backups.sort(key=lambda x: x["created_at"], reverse=True)
        
        return {"backups": backups}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取备份列表失败: {str(e)}")

@router.post("/restore/{backup_filename}")
async def restore_database(
    backup_filename: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != '管理员':
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        backup_path = BACKUP_DIR / backup_filename
        
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="备份文件不存在")
        
        await db.close()
        
        current_conn = sqlite3.connect(str(DATABASE_PATH))
        current_cursor = current_conn.cursor()
        
        users_data = []
        permissions_data = []
        
        current_cursor.execute("SELECT * FROM users")
        users_data = current_cursor.fetchall()
        current_cursor.execute("PRAGMA table_info(users)")
        users_columns = [col[1] for col in current_cursor.fetchall()]
        
        current_cursor.execute("SELECT * FROM permissions")
        permissions_data = current_cursor.fetchall()
        current_cursor.execute("PRAGMA table_info(permissions)")
        permissions_columns = [col[1] for col in current_cursor.fetchall()]
        
        current_conn.close()
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        current_backup = DATABASE_PATH.parent / f"temple_before_restore_{timestamp}.db"
        shutil.copy2(DATABASE_PATH, current_backup)
        
        restore_conn = sqlite3.connect(str(backup_path))
        current_conn = sqlite3.connect(str(DATABASE_PATH))
        
        current_cursor = current_conn.cursor()
        current_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = current_cursor.fetchall()
        for (table_name,) in tables:
            if table_name != 'sqlite_sequence':
                current_cursor.execute(f"DROP TABLE IF EXISTS {table_name}")
        current_conn.commit()
        
        restore_conn.backup(current_conn)
        
        current_cursor = current_conn.cursor()
        
        if users_data:
            current_cursor.execute("DELETE FROM users")
            placeholders = ','.join(['?' for _ in users_columns])
            current_cursor.executemany(f"INSERT INTO users VALUES ({placeholders})", users_data)
        
        if permissions_data:
            current_cursor.execute("DELETE FROM permissions")
            placeholders = ','.join(['?' for _ in permissions_columns])
            current_cursor.executemany(f"INSERT INTO permissions VALUES ({placeholders})", permissions_data)
        
        current_conn.commit()
        current_conn.close()
        restore_conn.close()
        
        return {
            "success": True,
            "message": "数据库恢复成功(已保留当前用户和权限数据)",
            "restored_from": backup_filename,
            "current_backup": current_backup.name,
            "preserved_users": len(users_data),
            "preserved_permissions": len(permissions_data)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"恢复失败: {str(e)}")

@router.delete("/backups/{backup_filename}")
async def delete_backup(
    backup_filename: str,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != '管理员':
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        backup_path = BACKUP_DIR / backup_filename
        
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="备份文件不存在")
        
        backup_path.unlink()
        
        return {
            "success": True,
            "message": f"备份文件 {backup_filename} 删除成功"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"删除失败: {str(e)}")

@router.post("/clear")
async def clear_database(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != '管理员':
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        tables_to_clear = [
            "fahui_records",
            "fahui_users",
            "system_logs"
        ]
        
        cleared_tables = []
        for table in tables_to_clear:
            result = await db.execute(text(f"DELETE FROM {table}"))
            cleared_tables.append({"table": table, "deleted_rows": result.rowcount})
        
        await db.commit()
        
        return {
            "success": True,
            "message": "数据库清空成功(已保留法会信息和打印模板)",
            "cleared_tables": cleared_tables
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")

@router.get("/download/{backup_filename}")
async def download_backup(
    backup_filename: str,
    current_user: User = Depends(get_current_user)
):
    if current_user.role != '管理员':
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        backup_path = BACKUP_DIR / backup_filename
        
        if not backup_path.exists():
            raise HTTPException(status_code=404, detail="备份文件不存在")
        
        return FileResponse(
            path=str(backup_path),
            filename=backup_filename,
            media_type='application/octet-stream'
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"下载失败: {str(e)}")

CLEARABLE_TABLES = {
    'fahui_records': '法会记录',
    'fahui_users': '施主信息',
    'fahui_info': '法会信息',
    'printer_templates': '打印模板',
    'system_logs': '系统日志'
}

@router.get("/clearable-tables")
async def get_clearable_tables(
    current_user: User = Depends(get_current_user)
):
    if current_user.role != '管理员':
        raise HTTPException(status_code=403, detail="权限不足")
    
    return {"tables": CLEARABLE_TABLES}

@router.post("/clear-table/{table_name}")
async def clear_specific_table(
    table_name: str,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != '管理员':
        raise HTTPException(status_code=403, detail="权限不足")
    
    if table_name not in CLEARABLE_TABLES:
        raise HTTPException(status_code=400, detail=f"不允许清空表: {table_name}")
    
    try:
        count_result = await db.execute(text(f"SELECT COUNT(*) FROM {table_name}"))
        count_before = count_result.scalar()
        
        result = await db.execute(text(f"DELETE FROM {table_name}"))
        await db.commit()
        
        return {
            "success": True,
            "message": f"表 {CLEARABLE_TABLES[table_name]} 清空成功",
            "table_name": table_name,
            "table_display_name": CLEARABLE_TABLES[table_name],
            "deleted_rows": count_before
        }
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"清空失败: {str(e)}")

@router.post("/init")
async def init_database(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != '管理员':
        raise HTTPException(status_code=403, detail="权限不足")
    
    try:
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = DATABASE_PATH.parent / f"temple_before_init_{timestamp}.db"
        shutil.copy2(DATABASE_PATH, backup_path)
        
        await db.close()
        
        conn = sqlite3.connect(str(DATABASE_PATH))
        cursor = conn.cursor()
        
        cleared_tables = []
        for table_name in CLEARABLE_TABLES.keys():
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            count = cursor.fetchone()[0]
            cursor.execute(f"DELETE FROM {table_name}")
            cleared_tables.append({
                "table": table_name,
                "display_name": CLEARABLE_TABLES[table_name],
                "deleted_rows": count
            })
        
        cursor.execute("DELETE FROM sqlite_sequence")
        
        default_templates = [
            ('延生大牌模板', '延生牌位', '大牌', 1),
            ('延生中牌模板', '延生牌位', '中牌', 1),
            ('延生小牌模板', '延生牌位', '小牌', 1),
            ('往生大牌模板', '往生牌位', '大牌', 1),
            ('往生中牌模板', '往生牌位', '中牌', 1),
            ('往生小牌模板', '往生牌位', '小牌', 1),
        ]
        
        now = datetime.now().isoformat()
        for name, type_, paiwei, is_default in default_templates:
            cursor.execute('''
                INSERT INTO printer_templates (模板名称, 模板类型, 牌位类型, 是否启用, 是否默认, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (name, type_, paiwei, 1, is_default, now, now))
        
        conn.commit()
        conn.close()
        
        return {
            "success": True,
            "message": "数据库初始化成功",
            "backup_file": backup_path.name,
            "cleared_tables": cleared_tables,
            "init_templates": len(default_templates)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"初始化失败: {str(e)}")


@router.post("/excel-preview")
async def preview_excel(
    file: UploadFile = File(...),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != '管理员':
        raise HTTPException(status_code=403, detail="权限不足")

    suffix = Path(file.filename).suffix.lower() if file.filename else ''
    if suffix not in ('.xls', '.xlsx'):
        raise HTTPException(status_code=400, detail="仅支持 .xls 和 .xlsx 格式文件")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = Path(tmp.name)

        headers, rows = _read_excel_file(tmp_path)
        preview_rows = rows[:5]

        COLUMN_MAPPING = {
            '施主编号': '施主编号 → FahuiUser.施主编号, FahuiRecord.施主编号',
            '施主姓名': '施主姓名 → FahuiUser.施主姓名, FahuiRecord.施主姓名',
            '座次': '座次 → FahuiRecord.座次',
            '往生/延生': '往生/延生 → FahuiRecord.yanwang (延生=0,往生=1)',
            '已打印': '已打印 → FahuiRecord.prt (是=1,否=0)',
            '电话': '电话 → FahuiUser.电话',
            '佛光接引一': '佛光接引一 → FahuiUser.佛光接引一, 延生→xm1, 往生→xm1',
            '佛光接引二': '佛光接引二 → FahuiUser.佛光接引二, 延生→xm2, 往生→xm2',
            '佛光接引三': '佛光接引三 → FahuiUser.佛光接引三, 延生→xm3, 往生→xm3',
            '佛光接引四': '佛光接引四 → FahuiUser.佛光接引四, 延生→xm4, 往生→xm4',
            '阳上一': '阳上一 → FahuiUser.阳上一, 往生→xm5',
            '阳上二': '阳上二 → FahuiUser.阳上二, 往生→xm6',
            '阳上三': '阳上三 → FahuiUser.阳上三, 往生→xm7',
            '阳上四': '阳上四 → FahuiUser.阳上四, 往生→xm8',
            '阳上五': '阳上五 → FahuiUser.阳上五, 往生→xm9',
            '阳上六': '阳上六 → FahuiUser.阳上六, 往生→xm10',
            '佛光注照一': '佛光注照一 → FahuiUser.佛光注照一, 延生→xm1',
            '佛光注照二': '佛光注照二 → FahuiUser.佛光注照二, 延生→xm2',
            '佛光注照三': '佛光注照三 → FahuiUser.佛光注照三, 延生→xm3',
            '佛光注照四': '佛光注照四 → FahuiUser.佛光注照四, 延生→xm4',
            '登记人': '登记人 → FahuiUser.登记人, FahuiRecord.经办人',
            '登记时间': '登记时间 → FahuiUser.登记时间, FahuiRecord.djdate',
            '年份': '年份 → FahuiRecord.remarks',
            '创建人': '❌ 无对应字段 (对应用户username)',
            '创建时间': '❌ 无对应字段 (数据库自动管理)',
            '修改人': '❌ 无对应字段 (数据库自动管理)',
            '修改时间': '❌ 无对应字段 (数据库自动管理)',
        }

        column_mapping = {}
        for h in headers:
            if h in COLUMN_MAPPING:
                column_mapping[h] = COLUMN_MAPPING[h]
            else:
                column_mapping[h] = '❌ 无对应字段'

        return {
            "filename": file.filename,
            "headers": headers,
            "total_rows": len(rows),
            "preview_rows": preview_rows,
            "column_mapping": column_mapping
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预览Excel文件失败: {str(e)}")
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()


@router.post("/import-excel")
async def import_excel(
    file: UploadFile = File(...),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if current_user.role != '管理员':
        raise HTTPException(status_code=403, detail="权限不足")

    if not file.filename:
        raise HTTPException(status_code=400, detail="文件名不能为空")

    fahui_name = "历史法会"
    excel_filename = file.filename
    temple_id = current_user.temple_id

    suffix = Path(file.filename).suffix.lower() if file.filename else ''
    if suffix not in ('.xls', '.xlsx'):
        raise HTTPException(status_code=400, detail="仅支持 .xls 和 .xlsx 格式文件")

    tmp_path = None
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
            shutil.copyfileobj(file.file, tmp)
            tmp_path = Path(tmp.name)

        headers, rows = _read_excel_file(tmp_path)
        if not rows:
            raise HTTPException(status_code=400, detail="Excel文件中没有数据行")

        fahui_result = await db.execute(
            select(FahuiInfo).where(FahuiInfo.法会名称 == fahui_name, FahuiInfo.temple_id == temple_id)
        )
        fahui = fahui_result.scalar_one_or_none()
        fahui_created = False

        if fahui:
            fahui_id = fahui.id
            existing_remark = fahui.备注 or ''
            if excel_filename not in existing_remark:
                imported_files = [f.strip() for f in existing_remark.split(',') if f.strip()]
                imported_files.append(excel_filename)
                fahui.备注 = ','.join(imported_files)
        else:
            new_fahui = FahuiInfo(法会名称=fahui_name, 备注=excel_filename, temple_id=temple_id)
            db.add(new_fahui)
            await db.flush()
            fahui_id = new_fahui.id
            fahui_created = True

        result_all = await db.execute(select(FahuiUser))
        all_users = result_all.scalars().all()
        user_map = {}
        for u in all_users:
            if u.施主编号:
                user_map[u.施主编号] = u

        success_count = 0
        fail_count = 0
        reuse_count = 0
        new_user_count = 0
        errors = []

        for idx, row in enumerate(rows, start=2):
            try:
                shizhu_bianhao = str(row.get('施主编号', '')).strip() if row.get('施主编号') else ''
                if not shizhu_bianhao:
                    errors.append(f"第{idx}行: 缺少施主编号，跳过")
                    fail_count += 1
                    continue

                shizhu_xingming = str(row.get('施主姓名', '')).strip() if row.get('施主姓名') else ''

                existing_user = user_map.get(shizhu_bianhao)

                if existing_user:
                    reuse_count += 1
                    update_fields = {
                        '电话': row.get('电话'),
                        '佛光接引一': row.get('佛光接引一'),
                        '佛光接引二': row.get('佛光接引二'),
                        '佛光接引三': row.get('佛光接引三'),
                        '佛光接引四': row.get('佛光接引四'),
                        '阳上一': row.get('阳上一'),
                        '阳上二': row.get('阳上二'),
                        '阳上三': row.get('阳上三'),
                        '阳上四': row.get('阳上四'),
                        '阳上五': row.get('阳上五'),
                        '阳上六': row.get('阳上六'),
                        '佛光注照一': row.get('佛光注照一'),
                        '佛光注照二': row.get('佛光注照二'),
                        '佛光注照三': row.get('佛光注照三'),
                        '佛光注照四': row.get('佛光注照四'),
                    }
                    for field_name, value in update_fields.items():
                        if value:
                            setattr(existing_user, field_name, str(value).strip())
                    if shizhu_xingming and not existing_user.施主姓名:
                        existing_user.施主姓名 = shizhu_xingming
                    fahui_user_id = existing_user.id
                else:
                    new_user = FahuiUser(
                        施主编号=shizhu_bianhao,
                        施主姓名=shizhu_xingming,
                        电话=str(row.get('电话', '')).strip() if row.get('电话') else None,
                        佛光接引一=str(row.get('佛光接引一', '')).strip() if row.get('佛光接引一') else None,
                        佛光接引二=str(row.get('佛光接引二', '')).strip() if row.get('佛光接引二') else None,
                        佛光接引三=str(row.get('佛光接引三', '')).strip() if row.get('佛光接引三') else None,
                        佛光接引四=str(row.get('佛光接引四', '')).strip() if row.get('佛光接引四') else None,
                        阳上一=str(row.get('阳上一', '')).strip() if row.get('阳上一') else None,
                        阳上二=str(row.get('阳上二', '')).strip() if row.get('阳上二') else None,
                        阳上三=str(row.get('阳上三', '')).strip() if row.get('阳上三') else None,
                        阳上四=str(row.get('阳上四', '')).strip() if row.get('阳上四') else None,
                        阳上五=str(row.get('阳上五', '')).strip() if row.get('阳上五') else None,
                        阳上六=str(row.get('阳上六', '')).strip() if row.get('阳上六') else None,
                        佛光注照一=str(row.get('佛光注照一', '')).strip() if row.get('佛光注照一') else None,
                        佛光注照二=str(row.get('佛光注照二', '')).strip() if row.get('佛光注照二') else None,
                        佛光注照三=str(row.get('佛光注照三', '')).strip() if row.get('佛光注照三') else None,
                        佛光注照四=str(row.get('佛光注照四', '')).strip() if row.get('佛光注照四') else None,
                        登记人=str(row.get('登记人', '')).strip() if row.get('登记人') else None,
                        登记时间=str(row.get('登记时间', '')).strip() if row.get('登记时间') else None,
                        temple_id=temple_id,
                    )
                    db.add(new_user)
                    await db.flush()
                    user_map[shizhu_bianhao] = new_user
                    fahui_user_id = new_user.id
                    new_user_count += 1

                yanwang_val = row.get('往生/延生', '')
                yanwang = 1 if str(yanwang_val).strip() == '往生' else 0

                prt_val = row.get('已打印', '')
                prt_str = str(prt_val).strip() if prt_val else ''
                if prt_str == '否':
                    prt = 0
                else:
                    prt = 1

                djdate_val = row.get('登记时间', '')
                djdate_str = str(djdate_val).strip() if djdate_val else None

                xm_fields = {}
                if yanwang == 0:
                    xm_fields['xm1'] = row.get('佛光注照一')
                    xm_fields['xm2'] = row.get('佛光注照二')
                    xm_fields['xm3'] = row.get('佛光注照三')
                    xm_fields['xm4'] = row.get('佛光注照四')
                    xm_fields['xm'] = '佛光注照'
                else:
                    xm_fields['xm1'] = row.get('佛光接引一')
                    xm_fields['xm2'] = row.get('佛光接引二')
                    xm_fields['xm3'] = row.get('佛光接引三')
                    xm_fields['xm4'] = row.get('佛光接引四')
                    xm_fields['xm5'] = row.get('阳上一')
                    xm_fields['xm6'] = row.get('阳上二')
                    xm_fields['xm7'] = row.get('阳上三')
                    xm_fields['xm8'] = row.get('阳上四')
                    xm_fields['xm9'] = row.get('阳上五')
                    xm_fields['xm10'] = row.get('阳上六')
                    xm_fields['xm'] = '佛光接引'

                for k in list(xm_fields.keys()):
                    if k == 'xm':
                        continue
                    if xm_fields[k]:
                        xm_fields[k] = str(xm_fields[k]).strip()

                nianfen = str(row.get('年份', '')).strip() if row.get('年份') else ''
                remarks_val = f'年份:{nianfen}' if nianfen else None

                record = FahuiRecord(
                    fahui_user_id=fahui_user_id,
                    fahui_id=fahui_id,
                    fahui_name=fahui_name,
                    座次=str(row.get('座次', '')).strip() if row.get('座次') else None,
                    yanwang=yanwang,
                    prt=prt,
                    djdate=djdate_str,
                    经办人=str(row.get('登记人', '')).strip() if row.get('登记人') else None,
                    施主姓名=shizhu_xingming,
                    施主编号=shizhu_bianhao,
                    xm1=xm_fields.get('xm1'),
                    xm2=xm_fields.get('xm2'),
                    xm3=xm_fields.get('xm3'),
                    xm4=xm_fields.get('xm4'),
                    xm5=xm_fields.get('xm5'),
                    xm6=xm_fields.get('xm6'),
                    xm7=xm_fields.get('xm7'),
                    xm8=xm_fields.get('xm8'),
                    xm9=xm_fields.get('xm9'),
                    xm10=xm_fields.get('xm10'),
                    xm=xm_fields.get('xm'),
                    remarks=remarks_val,
                    temple_id=temple_id,
                )
                db.add(record)
                success_count += 1

            except Exception as e:
                errors.append(f"第{idx}行: {str(e)}")
                fail_count += 1

        await db.commit()

        return {
            "success": True,
            "message": f"导入完成: 成功{success_count}条, 失败{fail_count}条",
            "total_rows": len(rows),
            "success_count": success_count,
            "fail_count": fail_count,
            "new_user_count": new_user_count,
            "reuse_user_count": reuse_count,
            "fahui_id": fahui_id,
            "fahui_name": fahui_name,
            "fahui_created": fahui_created,
            "errors": errors[:20]
        }
    except HTTPException:
        raise
    except Exception as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"导入Excel失败: {str(e)}")
    finally:
        if tmp_path and tmp_path.exists():
            tmp_path.unlink()
