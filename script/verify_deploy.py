# -*- coding: utf-8 -*-
"""部署后最终验证"""
import sqlite3
import os

DB_PATH = r'e:\Project\Print_tool\temple-management\deploy\国庆寺\database\temple.db'

conn = sqlite3.connect(DB_PATH)
cur = conn.cursor()

cur.execute("SELECT COUNT(*) FROM fahui_users")
print(f"fahui_users 总数: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM fahui_records")
print(f"fahui_records 总数: {cur.fetchone()[0]}")

cur.execute("SELECT COUNT(*) FROM fahui_users WHERE 施主姓名 = '杨洁'")
print(f"杨洁 记录数: {cur.fetchone()[0]} (应为 9)")

cur.execute("""
    SELECT COUNT(*) FROM fahui_records r
    LEFT JOIN fahui_users u ON r.fahui_user_id = u.id
    WHERE r.fahui_user_id IS NOT NULL AND u.id IS NULL
""")
print(f"孤立引用数: {cur.fetchone()[0]} (应为 0)")

# 验证杨洁的记录都能通过编号找到对应的施主
cur.execute("""
    SELECT COUNT(*) FROM fahui_records r
    LEFT JOIN fahui_users u ON r.fahui_user_id = u.id
    WHERE r.施主姓名 = '杨洁' AND u.id IS NULL
""")
print(f"杨洁在 records 中孤立数: {cur.fetchone()[0]} (应为 0)")

conn.close()
print(f"\n数据库路径: {DB_PATH}")
print(f"数据库大小: {os.path.getsize(DB_PATH) / 1024 / 1024:.2f} MB")
