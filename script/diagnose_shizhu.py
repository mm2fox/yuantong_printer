# -*- coding: utf-8 -*-
"""进一步诊断: 检查 fahui_users 总数、杨洁详细字段、所有重复施主"""
import sqlite3
import os
import sys
from collections import defaultdict

DB_PATH = r'e:\Project\Print_tool\temple-management\deploy\国庆寺\database\temple.db'

NAME_FIELDS = [
    '施主姓名',
    '佛光接引一', '佛光接引二', '佛光接引三', '佛光接引四',
    '阳上一', '阳上二', '阳上三', '阳上四', '阳上五', '阳上六',
    '佛光注照一', '佛光注照二', '佛光注照三', '佛光注照四',
]

def normalize(v):
    """统一空值处理: NULL/None/空字符串视为相同"""
    if v is None:
        return ''
    return str(v).strip()

def main():
    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found: {DB_PATH}")
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    print("=" * 80)
    print("=== fahui_users 总数和 ID 范围 ===")
    cur.execute("SELECT COUNT(*) AS cnt, MIN(id) AS min_id, MAX(id) AS max_id FROM fahui_users")
    r = cur.fetchone()
    print(f"  总数: {r['cnt']}, id 范围: {r['min_id']} ~ {r['max_id']}")

    print("\n=== 关键诊断: 后端 getList 返回的前 500 条 (ORDER BY id DESC) 中是否包含'杨洁'的 9 条 ===")
    cur.execute("SELECT id, 施主编号, 施主姓名 FROM fahui_users ORDER BY id DESC LIMIT 500")
    top500 = cur.fetchall()
    print(f"  前500条中 '杨洁' 的记录:")
    found_in_top500 = False
    for r in top500:
        if r['施主姓名'] == '杨洁':
            found_in_top500 = True
            print(f"    id={r['id']}, 编号={r['施主编号']}")
    if not found_in_top500:
        print("    (无 - 这就是管理页面显示 no data 的原因！)")
        # 查一下前500条最小id是多少
        if top500:
            print(f"    前500条最小 id = {top500[-1]['id']}, 杨洁的 id 范围是 651 ~ 2364")

    print("\n=== 杨洁 9 条记录的详细姓名字段 ===")
    cur.execute("SELECT * FROM fahui_users WHERE 施主姓名 = '杨洁' ORDER BY id")
    rows = cur.fetchall()
    for r in rows:
        print(f"\n  id={r['id']}, 编号={r['施主编号']}, 登记人={r['登记人']}, 登记时间={r['登记时间']}")
        print(f"    电话={r['电话']}, 地址={r['地址']}, 功德主={r['功德主']}, 备注={r['备注']}")
        print(f"    佛光接引: 一={r['佛光接引一']!r}, 二={r['佛光接引二']!r}, 三={r['佛光接引三']!r}, 四={r['佛光接引四']!r}")
        print(f"    阳上: 一={r['阳上一']!r}, 二={r['阳上二']!r}, 三={r['阳上三']!r}, 四={r['阳上四']!r}, 五={r['阳上五']!r}, 六={r['阳上六']!r}")
        print(f"    佛光注照: 一={r['佛光注照一']!r}, 二={r['佛光注照二']!r}, 三={r['佛光注照三']!r}, 四={r['佛光注照四']!r}")

    print("\n" + "=" * 80)
    print("=== 全库重复施主扫描 (按姓名+所有姓名n字段分组) ===")
    cur.execute("SELECT * FROM fahui_users")
    all_users = cur.fetchall()
    print(f"  全库 fahui_users 总数: {len(all_users)}")

    groups = defaultdict(list)
    for u in all_users:
        key = tuple(normalize(u[f]) for f in NAME_FIELDS)
        groups[key].append(dict(u))

    dup_groups = {k: v for k, v in groups.items() if len(v) > 1}
    print(f"  唯一姓名n组合数: {len(groups)}")
    print(f"  有重复的组数 (同姓名n): {len(dup_groups)}")
    total_redundant = sum(len(v) - 1 for v in dup_groups.values())
    print(f"  冗余记录总数 (可合并): {total_redundant}")

    print("\n=== 前 20 个重复组详情 ===")
    sorted_dups = sorted(dup_groups.items(), key=lambda kv: -len(kv[1]))
    for i, (key, users) in enumerate(sorted_dups[:20]):
        print(f"\n  [组 {i+1}] 姓名={key[0]!r}, 组内记录数={len(users)}, 冗余={len(users)-1}")
        print(f"    佛光接引: {key[1]!r}, {key[2]!r}, {key[3]!r}, {key[4]!r}")
        print(f"    阳上: {key[5]!r}, {key[6]!r}, {key[7]!r}, {key[8]!r}, {key[9]!r}, {key[10]!r}")
        print(f"    佛光注照: {key[11]!r}, {key[12]!r}, {key[13]!r}, {key[14]!r}")
        for u in users:
            # 统计每条记录在 fahui_records 中的引用数
            cur.execute("SELECT COUNT(*) AS cnt FROM fahui_records WHERE fahui_user_id = ?", (u['id'],))
            cnt = cur.fetchone()['cnt']
            print(f"      - id={u['id']}, 编号={u['施主编号']}, 登记人={u['登记人']}, 关联记录数={cnt}")

    print("\n=== 同时也按仅'施主姓名'分组的重复情况 (供参考) ===")
    name_groups = defaultdict(list)
    for u in all_users:
        name_groups[normalize(u['施主姓名'])].append(dict(u))
    name_dups = {k: v for k, v in name_groups.items() if len(v) > 1}
    print(f"  仅按姓名分组的重复组数: {len(name_dups)}")
    print(f"  其中前 10 个姓名重复最多的:")
    sorted_name_dups = sorted(name_dups.items(), key=lambda kv: -len(kv[1]))
    for name, users in sorted_name_dups[:10]:
        # 进一步看这些同名记录里有多少组的姓名n字段也完全相同
        sub_groups = defaultdict(list)
        for u in users:
            key = tuple(normalize(u[f]) for f in NAME_FIELDS[1:])
            sub_groups[key].append(u)
        mergable_subgroups = sum(1 for v in sub_groups.values() if len(v) > 1)
        print(f"    姓名={name!r}: 共 {len(users)} 条, 其中姓名n完全相同的子组数={mergable_subgroups}")

    conn.close()

if __name__ == '__main__':
    main()
