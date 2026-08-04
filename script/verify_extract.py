# -*- coding: utf-8 -*-
"""验证姓名提取结果"""
import sqlite3

DB_PATH = r'e:\Project\Print_tool\temple-management\deploy\国庆寺\database\temple.db'

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== 验证冯煜 ===")
cur.execute("SELECT id, 施主编号, 施主姓名, 阳上一, 佛光注照一 FROM fahui_users WHERE 施主姓名 = '冯煜'")
for r in cur.fetchall():
    print(f"  id={r['id']}, 编号={r['施主编号']}, 姓名={r['施主姓名']}, 阳上一={r['阳上一']!r}, 佛光注照一={r['佛光注照一']!r}")

print("\n=== 空姓名记录（应只剩3条）===")
cur.execute("SELECT id, 施主编号, 阳上一, 佛光注照一, 佛光接引一 FROM fahui_users WHERE 施主姓名 IS NULL OR TRIM(施主姓名) = ''")
for r in cur.fetchall():
    print(f"  id={r['id']}, 编号={r['施主编号']}, 阳上={r['阳上一']!r}, 注照={r['佛光注照一']!r}, 接引={r['佛光接引一']!r}")

print("\n=== 统计 ===")
cur.execute("SELECT COUNT(*) FROM fahui_users")
print(f"  施主总数: {cur.fetchone()[0]}")
cur.execute("SELECT COUNT(*) FROM fahui_users WHERE 施主姓名 IS NULL OR TRIM(施主姓名) = ''")
print(f"  空姓名: {cur.fetchone()[0]}")

print("\n=== 抽样：奚玮 ===")
cur.execute("SELECT id, 施主姓名, 佛光注照一 FROM fahui_users WHERE 施主姓名 = '奚玮'")
for r in cur.fetchall():
    print(f"  id={r['id']}, 姓名={r['施主姓名']}, 注照={r['佛光注照一']!r}")

conn.close()
