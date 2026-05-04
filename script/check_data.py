#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查数据库数据
"""

import sqlite3
from pathlib import Path

DATABASE_PATH = Path(__file__).parent.parent / "database" / "temple.db"

def check_data():
    conn = sqlite3.connect(str(DATABASE_PATH))
    cursor = conn.cursor()
    
    print("=== 数据库统计 ===")
    
    cursor.execute("SELECT COUNT(*) FROM fahui_records")
    print(f"法会记录数量: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM fahui_users")
    print(f"施主数量: {cursor.fetchone()[0]}")
    
    cursor.execute("SELECT COUNT(*) FROM fahui_info")
    print(f"法会信息数量: {cursor.fetchone()[0]}")
    
    print("\n=== 法会记录样例 ===")
    cursor.execute("SELECT id, fahui_id, fahui_name, xm1, amount, temple_id FROM fahui_records LIMIT 5")
    for row in cursor.fetchall():
        print(row)
    
    print("\n=== 施主样例 ===")
    cursor.execute("SELECT id, 施主编号, 施主姓名, temple_id FROM fahui_users LIMIT 5")
    for row in cursor.fetchall():
        print(row)
    
    print("\n=== 寺庙信息 ===")
    cursor.execute("SELECT * FROM temples")
    for row in cursor.fetchall():
        print(row)
    
    print("\n=== 用户信息 ===")
    cursor.execute("SELECT id, username, temple_id FROM users")
    for row in cursor.fetchall():
        print(row)
    
    conn.close()

if __name__ == "__main__":
    check_data()
