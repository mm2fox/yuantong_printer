# -*- coding: utf-8 -*-
"""诊断空施主姓名的记录"""
import sqlite3
import re
from collections import Counter

DB_PATH = r'e:\Project\Print_tool\temple-management\deploy\国庆寺\database\temple.db'

NAME_FIELDS = [
    '佛光接引一', '佛光接引二', '佛光接引三', '佛光接引四',
    '阳上一', '阳上二', '阳上三', '阳上四', '阳上五', '阳上六',
    '佛光注照一', '佛光注照二', '佛光注照三', '佛光注照四',
]

def normalize(v):
    if v is None:
        return ''
    return str(v).strip()

def main():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print("=" * 80)
    print("=== 1. 空 施主姓名 的记录数 ===")
    cur.execute("""
        SELECT COUNT(*) AS cnt FROM fahui_users
        WHERE 施主姓名 IS NULL OR TRIM(施主姓名) = ''
    """)
    print(f"  空 施主姓名 记录数: {cur.fetchone()['cnt']}")

    print("\n=== 2. 空 施主姓名 记录中，姓名n字段非空的情况 ===")
    cur.execute("""
        SELECT * FROM fahui_users
        WHERE 施主姓名 IS NULL OR TRIM(施主姓名) = ''
    """)
    rows = cur.fetchall()
    print(f"  共 {len(rows)} 条空姓名记录")

    # 统计每条空姓名记录里，姓名n字段都有哪些非空内容
    has_any_name = 0
    has_hejia = 0
    hejia_counter = Counter()  # 统计"XX合家"的内容
    sample_rows = []
    for r in rows:
        names = [normalize(r[f]) for f in NAME_FIELDS]
        names_nonempty = [n for n in names if n]
        if names_nonempty:
            has_any_name += 1
            # 检查是否含"合家"
            for n in names_nonempty:
                if '合家' in n:
                    has_hejia += 1
                    hejia_counter[n] += 1
                    break
        if len(sample_rows) < 15:
            sample_rows.append({
                'id': r['id'],
                '施主编号': r['施主编号'],
                '佛光接引一': r['佛光接引一'],
                '阳上一': r['阳上一'],
                '佛光注照一': r['佛光注照一'],
            })

    print(f"  其中姓名n字段至少有一个非空的: {has_any_name}")
    print(f"  其中姓名n字段含'合家'的: {has_hejia}")

    print("\n=== 3. 前 15 条空姓名记录样本 ===")
    for s in sample_rows:
        print(f"  id={s['id']}, 编号={s['施主编号']}, 佛光接引一={s['佛光接引一']!r}, 阳上一={s['阳上一']!r}, 佛光注照一={s['佛光注照一']!r}")

    print("\n=== 4. 含'合家'的姓名内容 Top 30 ===")
    for name, cnt in hejia_counter.most_common(30):
        print(f"  {cnt:5d}  {name!r}")

    print("\n=== 5. 全库（含已填施主姓名）姓名n字段中含'合家'的内容 Top 20 ===")
    cur.execute("SELECT * FROM fahui_users")
    all_rows = cur.fetchall()
    all_hejia = Counter()
    for r in all_rows:
        for f in NAME_FIELDS:
            v = normalize(r[f])
            if v and '合家' in v:
                all_hejia[v] += 1
    for name, cnt in all_hejia.most_common(20):
        print(f"  {cnt:5d}  {name!r}")

    print("\n=== 6. '冯煜合家' 在数据库中的分布 ===")
    for f in NAME_FIELDS:
        cur.execute(f"SELECT COUNT(*) AS cnt FROM fahui_users WHERE {f} = '冯煜合家'")
        cnt = cur.fetchone()['cnt']
        if cnt > 0:
            print(f"  {f} = '冯煜合家': {cnt} 条")

    conn.close()

if __name__ == '__main__':
    main()
