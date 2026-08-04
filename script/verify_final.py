# -*- coding: utf-8 -*-
"""整理后最终验证"""
import sqlite3

DB_PATH = r'e:\Project\Print_tool\temple-management\deploy\国庆寺\database\temple.db'

conn = sqlite3.connect(DB_PATH)
conn.row_factory = sqlite3.Row
cur = conn.cursor()

print("=== 整理结果汇总 ===")
cur.execute("SELECT COUNT(*) FROM fahui_users")
print(f"  施主总数: {cur.fetchone()[0]} (原 17365)")
cur.execute("SELECT COUNT(*) FROM fahui_users WHERE 施主姓名 IS NULL OR TRIM(施主姓名) = ''")
print(f"  空姓名: {cur.fetchone()[0]} (原 6459)")
cur.execute("SELECT COUNT(*) FROM fahui_records")
print(f"  法会记录: {cur.fetchone()[0]}")
cur.execute("""
    SELECT COUNT(*) FROM fahui_records r
    LEFT JOIN fahui_users u ON r.fahui_user_id = u.id
    WHERE r.fahui_user_id IS NOT NULL AND u.id IS NULL
""")
print(f"  孤立引用: {cur.fetchone()[0]} (应为 0)")

print("\n=== 冯煜验证 ===")
cur.execute("SELECT COUNT(*) FROM fahui_users WHERE 施主姓名 = '冯煜'")
print(f"  冯煜记录数: {cur.fetchone()[0]}")

print("\n=== 杨洁验证 ===")
cur.execute("SELECT COUNT(*) FROM fahui_users WHERE 施主姓名 = '杨洁'")
print(f"  杨洁记录数: {cur.fetchone()[0]}")

print("\n=== 空姓名记录（应只剩17条）===")
cur.execute("SELECT id, 施主编号, 阳上一, 佛光注照一, 佛光接引一 FROM fahui_users WHERE 施主姓名 IS NULL OR TRIM(施主姓名) = '' LIMIT 20")
for r in cur.fetchall():
    print(f"  id={r['id']}, 编号={r['施主编号']}, 阳上={r['阳上一']!r}, 注照={r['佛光注照一']!r}, 接引={r['佛光接引一']!r}")

conn.close()
