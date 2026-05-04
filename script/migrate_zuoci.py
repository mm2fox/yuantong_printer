#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库迁移脚本 - 座次字段迁移
将座次字段从 fahui_users 表迁移到 fahui_records 表
"""

import sqlite3
import os

DATABASE_PATH = "../database/temple.db"

def migrate_database():
    """迁移数据库"""
    if not os.path.exists(DATABASE_PATH):
        print(f"数据库文件不存在: {DATABASE_PATH}")
        return
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    try:
        print("开始迁移座次字段...")
        
        cursor.execute("PRAGMA table_info(fahui_users)")
        fahui_users_columns = [column[1] for column in cursor.fetchall()]
        
        cursor.execute("PRAGMA table_info(fahui_records)")
        fahui_records_columns = [column[1] for column in cursor.fetchall()]
        
        if '座次' in fahui_users_columns:
            print("fahui_users 表中有座次字段，需要删除")
            
            cursor.execute("""
                CREATE TABLE fahui_users_new (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    施主编号 TEXT NOT NULL UNIQUE,
                    施主姓名 TEXT NOT NULL,
                    电话 TEXT,
                    地址 TEXT,
                    功德主 INTEGER DEFAULT 1,
                    佛光接引一 TEXT,
                    佛光接引二 TEXT,
                    佛光接引三 TEXT,
                    佛光接引四 TEXT,
                    阳上一 TEXT,
                    阳上二 TEXT,
                    阳上三 TEXT,
                    阳上四 TEXT,
                    阳上五 TEXT,
                    阳上六 TEXT,
                    佛光注照一 TEXT,
                    佛光注照二 TEXT,
                    佛光注照三 TEXT,
                    佛光注照四 TEXT,
                    登记人 TEXT,
                    登记时间 TEXT,
                    备注 TEXT,
                    temple_id INTEGER,
                    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (temple_id) REFERENCES temples(id)
                )
            """)
            
            cursor.execute("""
                INSERT INTO fahui_users_new 
                SELECT id, 施主编号, 施主姓名, 电话, 地址, 功德主, 
                       佛光接引一, 佛光接引二, 佛光接引三, 佛光接引四,
                       阳上一, 阳上二, 阳上三, 阳上四, 阳上五, 阳上六,
                       佛光注照一, 佛光注照二, 佛光注照三, 佛光注照四,
                       登记人, 登记时间, 备注, temple_id, created_at, updated_at
                FROM fahui_users
            """)
            
            cursor.execute("DROP TABLE fahui_users")
            cursor.execute("ALTER TABLE fahui_users_new RENAME TO fahui_users")
            
            print("fahui_users 表座次字段已删除")
        
        if '座次' not in fahui_records_columns:
            print("fahui_records 表中没有座次字段，需要添加")
            
            cursor.execute("ALTER TABLE fahui_records ADD COLUMN 座次 TEXT")
            
            print("fahui_records 表座次字段已添加")
        
        conn.commit()
        print("座次字段迁移完成！")
        
    except Exception as e:
        conn.rollback()
        print(f"迁移失败: {e}")
        raise
    finally:
        conn.close()

if __name__ == "__main__":
    migrate_database()
