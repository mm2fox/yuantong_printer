import sqlite3

print('=== 原始数据库 cstemple.db ===')
conn = sqlite3.connect(r'E:\Project\Print_tool\cstemple.db')
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
