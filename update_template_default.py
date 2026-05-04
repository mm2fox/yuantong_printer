import sqlite3

conn = sqlite3.connect(r'E:\Project\Print_tool\temple-management\database\temple.db')
cursor = conn.cursor()

try:
    cursor.execute('ALTER TABLE printer_templates ADD COLUMN 是否默认 INTEGER DEFAULT 0')
    conn.commit()
    print('已添加 是否默认 列')
except Exception as e:
    if 'duplicate column name' in str(e).lower():
        print('列 是否默认 已存在')
    else:
        print(f'错误: {e}')

cursor.execute('UPDATE printer_templates SET 是否默认 = 1 WHERE 模板名称 LIKE "%模板" AND 模板名称 LIKE "%延生%" OR 模板名称 LIKE "%往生%"')
affected = cursor.rowcount
conn.commit()
print(f'已标记 {affected} 个模板为默认模板')

cursor.execute('SELECT id, 模板名称, 是否默认 FROM printer_templates')
rows = cursor.fetchall()
print('\n当前模板列表:')
for row in rows:
    print(f'  ID: {row[0]}, 名称: {row[1]}, 是否默认: {row[2]}')

conn.close()
