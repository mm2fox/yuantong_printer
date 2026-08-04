# -*- coding: utf-8 -*-
"""检查所有数据库文件的状态"""
import sqlite3
import os
from datetime import datetime

DB_FILES = [
    r'e:\Project\Print_tool\temple-management\deploy\国庆寺\database\temple.db',
    r'e:\Project\Print_tool\temple-management\dist\database\temple.db',
    r'e:\Project\Print_tool\temple-management\database\temple.db',
    r'e:\Project\Print_tool\temple-management\dist\yanqingsi\database\temple.db',
    r'e:\Project\Print_tool\temple-management\dist\guoqingsi\database\temple.db',
    r'e:\Project\Print_tool\temple-management\database\temple_before_init_20260417_141042.db',
    r'e:\Project\Print_tool\temple-management\database\temple_empty_20260417_131740.db',
    r'e:\Project\Print_tool\temple-management\database\temple_before_restore_20260417_131400.db',
]

for db_path in DB_FILES:
    if not os.path.exists(db_path):
        continue
    mtime = datetime.fromtimestamp(os.path.getmtime(db_path)).strftime('%Y-%m-%d %H:%M:%S')
    size_mb = os.path.getsize(db_path) / 1024 / 1024
    try:
        conn = sqlite3.connect(db_path)
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) FROM fahui_users")
        total = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fahui_users WHERE 施主姓名 IS NULL OR TRIM(施主姓名) = ''")
        empty = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM fahui_records")
        records = cur.fetchone()[0]
        try:
            cur.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE '%temple%'")
            tables = [r[0] for r in cur.fetchall()]
            temple = '?'
            for t in tables:
                try:
                    cur.execute(f"SELECT * FROM {t} LIMIT 1")
                    row = cur.fetchone()
                    if row:
                        temple = str(row)
                        break
                except:
                    pass
        except:
            temple = '?'
        conn.close()
        print(f"{db_path}")
        print(f"  {size_mb:6.2f}MB | {mtime} | 施主:{total:6d} | 空姓名:{empty:5d} | 法会记录:{records:6d} | {temple[:60]}")
    except Exception as e:
        print(f"{os.path.basename(db_path):<50} | ERROR: {e}")
