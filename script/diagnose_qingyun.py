# -*- coding: utf-8 -*-
"""
庆云寺现场诊断脚本
用法：把此脚本放到和 exe 同级目录，运行
  python diagnose_qingyun.py
或直接双击运行（如果系统关联了 .py 文件）
"""
import sqlite3
import os
import sys
from pathlib import Path

# 尝试找到 database/temple.db
# 优先级：1. 同级目录  2. 脚本所在目录  3. 用户输入
candidates = []
if getattr(sys, 'frozen', False):
    base = Path(sys.executable).parent
else:
    base = Path(__file__).parent

candidates.append(base / "database" / "temple.db")
candidates.append(base.parent / "database" / "temple.db")

DB_PATH = None
for c in candidates:
    if c.exists():
        DB_PATH = c
        break

if DB_PATH is None:
    # 尝试在常见位置搜索
    for root, dirs, files in os.walk(base):
        if "temple.db" in files:
            DB_PATH = Path(root) / "temple.db"
            break

if DB_PATH is None or not DB_PATH.exists():
    print("未找到 temple.db 文件。请手动输入路径：")
    manual = input().strip().strip('"')
    DB_PATH = Path(manual)

print(f"诊断数据库: {DB_PATH}")
print(f"文件大小: {DB_PATH.stat().st_size / 1024:.1f} KB")
print("=" * 60)

conn = sqlite3.connect(str(DB_PATH))
conn.row_factory = sqlite3.Row
cur = conn.cursor()

# 1. 寺庙信息
print("\n【1. temples 表】")
cur.execute("SELECT id, 寺庙名称, 寺庙地址 FROM temples")
for row in cur.fetchall():
    print(f"  id={row['id']}, 名称={row['寺庙名称']}, 地址={row['寺庙地址']}")

# 2. 用户信息
print("\n【2. users 表】")
cur.execute("SELECT id, username, real_name, role, temple_id, is_active FROM users")
users = cur.fetchall()
for row in users:
    print(f"  id={row['id']}, 账号={row['username']}, 姓名={row['real_name']}, 角色={row['role']}, temple_id={row['temple_id']}, 启用={row['is_active']}")

# 3. 法会记录统计
print("\n【3. fahui_records 统计】")
cur.execute("SELECT COUNT(*) FROM fahui_records")
print(f"  总记录数: {cur.fetchone()[0]}")

# temple_id 分布
cur.execute("SELECT temple_id, COUNT(*) as cnt FROM fahui_records GROUP BY temple_id")
rows = cur.fetchall()
if rows:
    print("  按 temple_id 分布:")
    for row in rows:
        print(f"    temple_id={row['temple_id']}, 记录数={row['cnt']}")
else:
    print("  按 temple_id 分布: (无记录)")

# 4. 施主统计
print("\n【4. fahui_users 统计】")
cur.execute("SELECT COUNT(*) FROM fahui_users")
print(f"  总记录数: {cur.fetchone()[0]}")

# 5. 法会信息统计
print("\n【5. fahui_info 统计】")
cur.execute("SELECT COUNT(*) FROM fahui_info")
print(f"  总记录数: {cur.fetchone()[0]}")

# 6. 检查关键列是否存在
print("\n【6. fahui_records 表结构检查】")
cur.execute("PRAGMA table_info(fahui_records)")
cols = {r['name'] for r in cur.fetchall()}
required = {'xm', 'xm6', 'xm7', 'xm8', 'xm9', 'xm10', 'temple_id'}
missing = required - cols
if missing:
    print(f"  缺少列: {', '.join(missing)} ⚠️")
else:
    print("  关键列齐全 ✓")

# 7. 样本数据
print("\n【7. fahui_records 样本 (前3条)】")
cur.execute("SELECT id, fahui_name, 施主姓名, temple_id, yanwang, amount FROM fahui_records LIMIT 3")
rows = cur.fetchall()
if rows:
    for row in rows:
        print(f"  id={row['id']}, 法会={row['fahui_name']}, 施主={row['施主姓名']}, temple_id={row['temple_id']}, 类型={'往生' if row['yanwang']==1 else '延生'}, 金额={row['amount']}")
else:
    print("  (无记录)")

# 8. temple_id 匹配检查
print("\n【8. temple_id 匹配检查】")
user_temple_ids = {u['temple_id'] for u in users if u['temple_id'] is not None}
cur.execute("SELECT DISTINCT temple_id FROM fahui_records")
record_temple_ids = {r['temple_id'] for r in cur.fetchall()}
print(f"  用户拥有的 temple_id: {user_temple_ids}")
print(f"  法会记录拥有的 temple_id: {record_temple_ids}")
intersection = user_temple_ids & record_temple_ids
if intersection:
    print(f"  交集: {intersection} ✓ (有匹配的temple_id)")
else:
    if record_temple_ids:
        print(f"  交集为空 ⚠️ (没有匹配的temple_id，这就是查不到数据的直接原因！)")
    else:
        print("  法会记录表为空，无需匹配")

conn.close()
print("\n" + "=" * 60)
print("诊断完成。")
input("按回车键退出...")
