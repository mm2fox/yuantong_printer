import sqlite3

conn = sqlite3.connect(r'E:\Project\Print_tool\temple-management\database\temple.db')
cursor = conn.cursor()

print('=== fahui_users 表结构 ===')
cursor.execute('PRAGMA table_info(fahui_users)')
for col in cursor.fetchall():
    print(f'{col[1]}: {col[2]}')

print('\n=== fahui_records 表结构 ===')
cursor.execute('PRAGMA table_info(fahui_records)')
for col in cursor.fetchall():
    print(f'{col[1]}: {col[2]}')

conn.close()
