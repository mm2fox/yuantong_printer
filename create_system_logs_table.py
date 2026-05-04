import sqlite3

conn = sqlite3.connect(r'E:\Project\Print_tool\temple-management\database\temple.db')
cursor = conn.cursor()

cursor.execute('''
    CREATE TABLE IF NOT EXISTS system_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        用户名 VARCHAR(50),
        操作类型 VARCHAR(20),
        操作内容 TEXT,
        created_at DATETIME DEFAULT CURRENT_TIMESTAMP
    )
''')
conn.commit()
print('system_logs 表已创建或已存在')

cursor.execute('SELECT COUNT(*) FROM system_logs')
count = cursor.fetchone()[0]
print(f'当前日志数量: {count}')

conn.close()
