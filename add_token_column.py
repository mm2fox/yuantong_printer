import sqlite3

conn = sqlite3.connect(r'E:\Project\Print_tool\temple-management\database\temple.db')
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE users ADD COLUMN token VARCHAR(500)')
    conn.commit()
    print('已添加 token 列到 users 表')
except Exception as e:
    if 'duplicate column name' in str(e).lower():
        print('token 列已存在')
    else:
        print(f'错误: {e}')

conn.close()
