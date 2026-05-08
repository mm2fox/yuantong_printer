#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库初始化脚本
创建所有表并添加默认管理员用户
"""

import sqlite3
from datetime import datetime
import bcrypt

DATABASE_PATH = "../database/temple.db"

def get_password_hash(password: str) -> str:
    """生成密码哈希"""
    return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

def create_tables():
    """创建所有表"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS temples (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            寺庙名称 TEXT NOT NULL,
            寺庙地址 TEXT,
            联系电话 TEXT,
            备注 TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password_hash TEXT NOT NULL,
            real_name TEXT,
            role TEXT DEFAULT '普通用户',
            permissions TEXT,
            is_active INTEGER DEFAULT 1,
            temple_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (temple_id) REFERENCES temples(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS permissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL UNIQUE,
            display_name TEXT NOT NULL,
            description TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fahui_users (
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
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fahui_records (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fahui_user_id INTEGER,
            fahui_id INTEGER,
            fahui_name TEXT,
            座次 TEXT,
            amount REAL DEFAULT 0,
            paiwei_type TEXT,
            yanwang INTEGER DEFAULT 0,
            xm1 TEXT,
            xm2 TEXT,
            xm3 TEXT,
            xm4 TEXT,
            xm5 TEXT,
            djdate TEXT,
            经办人 TEXT,
            prt INTEGER DEFAULT 0,
            remarks TEXT,
            施主姓名 TEXT,
            施主编号 TEXT,
            temple_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (fahui_user_id) REFERENCES fahui_users(id) ON DELETE SET NULL,
            FOREIGN KEY (temple_id) REFERENCES temples(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS fahui_info (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            法会名称 TEXT NOT NULL,
            开始日期 TEXT,
            截止日期 TEXT,
            功德金中 TEXT,
            功德金小 TEXT,
            功德金大 TEXT,
            完成状态 TEXT,
            备注 TEXT,
            temple_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (temple_id) REFERENCES temples(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS printer_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            模板名称 TEXT NOT NULL,
            模板类型 TEXT NOT NULL,
            牌位类型 TEXT,
            布局配置 TEXT,
            默认参数 TEXT,
            是否启用 INTEGER DEFAULT 1,
            备注 TEXT,
            temple_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            updated_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (temple_id) REFERENCES temples(id)
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS system_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            用户名 TEXT,
            操作类型 TEXT,
            操作内容 TEXT,
            temple_id INTEGER,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (temple_id) REFERENCES temples(id)
        )
    ''')
    
    conn.commit()
    print("所有表创建成功")

def create_default_data():
    """创建默认数据"""
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM temples")
    if cursor.fetchone()[0] > 0:
        print("数据库已有数据，跳过默认数据创建")
        return
    
    cursor.execute('''
        INSERT INTO temples (寺庙名称, 寺庙地址, created_at, updated_at)
        VALUES (?, ?, ?, ?)
    ''', ('默认寺庙', '', datetime.now().isoformat(), datetime.now().isoformat()))
    temple_id = cursor.lastrowid
    
    password_hash = get_password_hash("admin123")
    cursor.execute('''
        INSERT INTO users (username, password_hash, real_name, role, is_active, temple_id, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    ''', ('admin', password_hash, '管理员', '管理员', 1, temple_id, datetime.now().isoformat(), datetime.now().isoformat()))
    
    default_permissions = [
        ('query', '查询', '查询法会和施主信息'),
        ('shizhu', '施主管理', '管理施主信息'),
        ('fahui', '法会管理', '管理法会信息和登记'),
        ('print', '打印管理', '打印牌位'),
        ('print_template', '打印模板', '管理打印模板'),
        ('system', '系统管理', '系统设置和用户管理')
    ]
    
    for name, display_name, description in default_permissions:
        cursor.execute('''
            INSERT INTO permissions (name, display_name, description, created_at)
            VALUES (?, ?, ?, ?)
        ''', (name, display_name, description, datetime.now().isoformat()))
    
    conn.commit()
    print("默认数据创建成功")
    print(f"默认寺庙ID: {temple_id}")
    print("默认管理员: admin / admin123")

def main():
    """主函数"""
    import os
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    print("开始初始化数据库...")
    create_tables()
    create_default_data()
    print("数据库初始化完成")

if __name__ == "__main__":
    main()
