import sqlite3

print('=== 当前数据库 ===')
conn = sqlite3.connect(r'E:\Project\Print_tool\temple-management\database\temple.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f'表: {[t[0] for t in tables]}')

for table in tables:
    table_name = table[0]
    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    count = cursor.fetchone()[0]
    print(f'  {table_name}: {count} 条记录')

conn.close()

print('\n=== 备份数据库 ===')
conn = sqlite3.connect(r'E:\Project\Print_tool\temple-management\backups\temple_backup_20260417_085126.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f'表: {[t[0] for t in tables]}')

for table in tables:
    table_name = table[0]
    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    count = cursor.fetchone()[0]
    print(f'  {table_name}: {count} 条记录')

conn.close()

print('\n=== 恢复前数据库 ===')
conn = sqlite3.connect(r'E:\Project\Print_tool\temple-management\database\temple_before_restore_20260417_131400.db')
cursor = conn.cursor()

cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()
print(f'表: {[t[0] for t in tables]}')

for table in tables:
    table_name = table[0]
    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    count = cursor.fetchone()[0]
    print(f'  {table_name}: {count} 条记录')

conn.close()
