import sqlite3
import shutil
from datetime import datetime

print('正在恢复数据...')

# 先备份当前数据库
current_db = r'E:\Project\Print_tool\temple-management\database\temple.db'
restore_db = r'E:\Project\Print_tool\temple-management\database\temple_before_restore_20260417_131400.db'

# 创建新的备份
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
shutil.copy2(current_db, f'E:\\Project\\Print_tool\\temple-management\\database\\temple_empty_{timestamp}.db')
print(f'已备份当前空数据库为: temple_empty_{timestamp}.db')

# 用恢复前的数据库替换当前数据库
shutil.copy2(restore_db, current_db)
print('已恢复数据!')

# 验证恢复结果
conn = sqlite3.connect(current_db)
cursor = conn.cursor()

print('\n=== 恢复后的数据库 ===')
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
tables = cursor.fetchall()

for table in tables:
    table_name = table[0]
    cursor.execute(f'SELECT COUNT(*) FROM {table_name}')
    count = cursor.fetchone()[0]
    print(f'  {table_name}: {count} 条记录')

conn.close()

print('\n数据恢复完成！请重新启动后端服务。')
