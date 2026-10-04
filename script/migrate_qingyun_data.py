# -*- coding: utf-8 -*-
"""
庆云寺数据迁移脚本
用法:
  python migrate_qingyun_data.py <旧数据库路径> <新数据库路径>

示例:
  python migrate_qingyun_data.py "deploy\庆云寺\database\temple.db" "deploy\庆云寺_new\database\temple.db"
"""
import sqlite3
import sys
from pathlib import Path

def migrate(old_db_path: str, new_db_path: str):
    old = Path(old_db_path)
    new = Path(new_db_path)

    if not old.exists():
        print(f"旧数据库不存在: {old}")
        sys.exit(1)
    if not new.exists():
        print(f"新数据库不存在: {new}，请先启动一次程序让它自动建表")
        sys.exit(1)

    src = sqlite3.connect(str(old))
    dst = sqlite3.connect(str(new))
    src.row_factory = sqlite3.Row
    dst.row_factory = sqlite3.Row
    sc = src.cursor()
    dc = dst.cursor()

    # 1. 确认新库的 temples.id 和 admin.temple_id
    dc.execute("SELECT id FROM temples LIMIT 1")
    row = dc.fetchone()
    if not row:
        print("新库 temples 表为空，请先启动一次程序")
        sys.exit(1)
    target_temple_id = row[0]
    print(f"目标 temple_id: {target_temple_id}")

    # 2. 获取旧库的三张业务表数据
    sc.execute("SELECT * FROM fahui_info")
    fahui_info_rows = sc.fetchall()
    sc.execute("SELECT * FROM fahui_users")
    fahui_users_rows = sc.fetchall()
    sc.execute("SELECT * FROM fahui_records")
    fahui_records_rows = sc.fetchall()

    print(f"旧库数据: fahui_info={len(fahui_info_rows)}, fahui_users={len(fahui_users_rows)}, fahui_records={len(fahui_records_rows)}")

    if not fahui_records_rows:
        print("旧库法会记录为空，无需迁移")
        sys.exit(0)

    # 3. 清空新库的业务数据（保留 users/temples/permissions/打印模板）
    for t in ['fahui_records', 'fahui_users', 'fahui_info', 'system_logs']:
        dc.execute(f"DELETE FROM {t}")
    try:
        dc.execute("DELETE FROM sqlite_sequence WHERE name IN ('fahui_records','fahui_users','fahui_info','system_logs')")
    except sqlite3.OperationalError:
        pass
    print("已清空新库业务数据")

    # 4. 迁移 fahui_info（法会信息）
    for row in fahui_info_rows:
        d = dict(row)
        d['temple_id'] = target_temple_id
        cols = list(d.keys())
        # 去掉 SQLite 自动生成的 id，让新库自增
        if 'id' in cols:
            cols.remove('id')
            del d['id']
        placeholders = ', '.join(['?' for _ in cols])
        sql = f"INSERT INTO fahui_info ({', '.join(cols)}) VALUES ({placeholders})"
        dc.execute(sql, [d[c] for c in cols])
    print(f"已迁移 fahui_info: {len(fahui_info_rows)} 条")

    # 5. 迁移 fahui_users（施主），保留旧 id 映射关系
    old_user_id_map = {}
    for row in fahui_users_rows:
        d = dict(row)
        old_id = d['id']
        d['temple_id'] = target_temple_id
        cols = list(d.keys())
        cols.remove('id')
        del d['id']
        placeholders = ', '.join(['?' for _ in cols])
        sql = f"INSERT INTO fahui_users ({', '.join(cols)}) VALUES ({placeholders})"
        dc.execute(sql, [d[c] for c in cols])
        new_id = dc.lastrowid
        old_user_id_map[old_id] = new_id
    print(f"已迁移 fahui_users: {len(fahui_users_rows)} 条")

    # 6. 迁移 fahui_records（法会记录）
    migrated = 0
    for row in fahui_records_rows:
        d = dict(row)
        d['temple_id'] = target_temple_id
        # 映射 fahui_user_id
        old_uid = d.get('fahui_user_id')
        if old_uid is not None and old_uid in old_user_id_map:
            d['fahui_user_id'] = old_user_id_map[old_uid]
        else:
            d['fahui_user_id'] = None
        # 去掉 id 让新库自增
        cols = list(d.keys())
        if 'id' in cols:
            cols.remove('id')
            del d['id']
        placeholders = ', '.join(['?' for _ in cols])
        sql = f"INSERT INTO fahui_records ({', '.join(cols)}) VALUES ({placeholders})"
        dc.execute(sql, [d[c] for c in cols])
        migrated += 1
    print(f"已迁移 fahui_records: {migrated} 条")

    # 7. 迁移庆云寺特有用户（印持/耀智等）
    sc.execute("SELECT * FROM users WHERE username IN ('印持','耀智','演训')")
    special_users = sc.fetchall()
    for row in special_users:
        d = dict(row)
        uname = d['username']
        dc.execute("SELECT id FROM users WHERE username = ?", (uname,))
        if dc.fetchone():
            print(f"用户 {uname} 已存在，跳过")
            continue
        d['temple_id'] = target_temple_id
        # 去掉 id
        cols = list(d.keys())
        if 'id' in cols:
            cols.remove('id')
            del d['id']
        placeholders = ', '.join(['?' for _ in cols])
        sql = f"INSERT INTO users ({', '.join(cols)}) VALUES ({placeholders})"
        dc.execute(sql, [d[c] for c in cols])
        print(f"已迁移用户: {uname}")

    dst.commit()
    src.close()
    dst.close()
    print("\n迁移完成！")

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("用法: python migrate_qingyun_data.py <旧数据库> <新数据库>")
        sys.exit(1)
    migrate(sys.argv[1], sys.argv[2])
