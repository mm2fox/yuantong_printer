# -*- coding: utf-8 -*-
"""合并国庆寺数据库中姓名n完全相同的重复施主

合并规则（用户要求）：
  只有当 施主姓名 + 佛光接引一/二/三/四 + 阳上一/二/三/四/五/六 + 佛光注照一/二/三/四
  这 15 个字段全部相同（NULL 与空字符串视为相同）时，才合并。

合并策略：
  - 每组保留 id 最小（最早创建）的一条作为 keeper
  - 非姓名n 字段（电话/地址/备注/功德主）做"无丢失合并"：
      * 功德主: 组内任一为 1 则 keeper 设为 1
      * 电话/地址/备注: keeper 为空时，从其他记录补入第一个非空值
  - 将组内其他记录的 fahui_records 全部改挂到 keeper：
      UPDATE fahui_records SET fahui_user_id=keeper.id, 施主编号=keeper.施主编号
      WHERE fahui_user_id=other.id
  - 删除组内其他记录

用法：
  python merge_shizhu.py --dry-run    # 仅预览，不写库
  python merge_shizhu.py              # 实际执行（会先自动备份）
"""
import sqlite3
import os
import sys
import shutil
import argparse
from datetime import datetime
from collections import defaultdict

DB_PATH = r'e:\Project\Print_tool\temple-management\deploy\国庆寺\database\temple.db'

# 姓名 n 相关字段：完全相同才合并
NAME_FIELDS = [
    '施主姓名',
    '佛光接引一', '佛光接引二', '佛光接引三', '佛光接引四',
    '阳上一', '阳上二', '阳上三', '阳上四', '阳上五', '阳上六',
    '佛光注照一', '佛光注照二', '佛光注照三', '佛光注照四',
]

# 非姓名n 字段：合并时做"无丢失"补全
INFO_FIELDS = ['电话', '地址', '备注']

# temple_id 也参与分组（不同 temple 视为不同施主，虽然本库只有国庆寺）
GROUP_FIELDS = NAME_FIELDS + ['temple_id']


def normalize(v):
    if v is None:
        return ''
    return str(v).strip()


def backup(db_path):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = db_path.replace('.db', f'_before_merge_{ts}.db')
    shutil.copy2(db_path, bak)
    print(f"[备份] 已备份到: {bak}")
    return bak


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help='仅预览不写库')
    args = parser.parse_args()

    if not os.path.exists(DB_PATH):
        print(f"ERROR: DB not found: {DB_PATH}")
        sys.exit(1)

    print(f"[模式] {'DRY-RUN（预览，不写库）' if args.dry_run else '实际执行'}")
    print(f"[数据库] {DB_PATH}")

    if not args.dry_run:
        backup(DB_PATH)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    # 1. 读取全部施主
    cur.execute("SELECT * FROM fahui_users")
    all_users = [dict(r) for r in cur.fetchall()]
    print(f"[扫描] fahui_users 总数: {len(all_users)}")

    # 2. 按 姓名 n + temple_id 分组
    groups = defaultdict(list)
    for u in all_users:
        key = tuple(normalize(u[f]) for f in GROUP_FIELDS)
        groups[key].append(u)

    dup_groups = {k: v for k, v in groups.items() if len(v) > 1}
    total_redundant = sum(len(v) - 1 for v in dup_groups.values())
    print(f"[扫描] 唯一组合数: {len(groups)}")
    print(f"[扫描] 重复组数: {len(dup_groups)}")
    print(f"[扫描] 待删除冗余记录数: {total_redundant}")

    # 3. 计算合并计划
    merge_plans = []  # 每项: (keeper, [other,...], keeper_updates)
    total_records_to_move = 0
    for key, users in dup_groups.items():
        # keeper = id 最小
        users_sorted = sorted(users, key=lambda u: u['id'])
        keeper = users_sorted[0]
        others = users_sorted[1:]

        # 无丢失合并：功德主取 max；电话/地址/备注 取 keeper 空则补第一个非空
        keeper_updates = {}
        gongdezhu_max = max(u['功德主'] or 0 for u in users)
        if (keeper['功德主'] or 0) != gongdezhu_max:
            keeper_updates['功德主'] = gongdezhu_max

        for field in INFO_FIELDS:
            keeper_val = normalize(keeper[field])
            if not keeper_val:
                for o in others:
                    ov = normalize(o[field])
                    if ov:
                        keeper_updates[field] = o[field]
                        break

        # 统计需改挂的 fahui_records 数
        for o in others:
            cur.execute("SELECT COUNT(*) AS cnt FROM fahui_records WHERE fahui_user_id = ?", (o['id'],))
            total_records_to_move += cur.fetchone()['cnt']

        merge_plans.append((keeper, others, keeper_updates))

    print(f"[计划] 需改挂 fahui_records 条数: {total_records_to_move}")
    print(f"[计划] keeper 字段需补全的组数: {sum(1 for _,_,u in merge_plans if u)}")

    # 打印前 10 个计划
    print("\n[预览] 前 10 个合并计划:")
    for i, (keeper, others, upd) in enumerate(merge_plans[:10]):
        name = keeper['施主姓名'] or '(空)'
        print(f"  [{i+1}] 姓名={name!r} 编号={keeper['施主编号']} (id={keeper['id']}) 保留")
        if upd:
            print(f"       keeper 补全字段: {upd}")
        for o in others:
            cur.execute("SELECT COUNT(*) AS cnt FROM fahui_records WHERE fahui_user_id = ?", (o['id'],))
            cnt = cur.fetchone()['cnt']
            print(f"       - 删除 id={o['id']}, 编号={o['施主编号']}, 改挂记录数={cnt}")

    if args.dry_run:
        print("\n[DRY-RUN] 未写库。如需执行，请去掉 --dry-run 重新运行。")
        conn.close()
        return

    # 4. 实际执行（事务）
    print("\n[执行] 开始事务...")
    try:
        cur.execute("BEGIN")

        deleted_count = 0
        moved_count = 0
        keeper_updated_count = 0

        for keeper, others, upd in merge_plans:
            # 4a. 改挂 fahui_records
            for o in others:
                cur.execute(
                    "UPDATE fahui_records SET fahui_user_id = ?, 施主编号 = ? WHERE fahui_user_id = ?",
                    (keeper['id'], keeper['施主编号'], o['id'])
                )
                moved_count += cur.rowcount

                # 4b. 删除冗余施主
                cur.execute("DELETE FROM fahui_users WHERE id = ?", (o['id'],))
                deleted_count += cur.rowcount

            # 4c. 更新 keeper 的补全字段
            if upd:
                set_clause = ", ".join(f"{k} = ?" for k in upd)
                params = list(upd.values()) + [keeper['id']]
                cur.execute(f"UPDATE fahui_users SET {set_clause} WHERE id = ?", params)
                keeper_updated_count += 1

        conn.commit()
        print(f"[执行] 已改挂 fahui_records: {moved_count} 条")
        print(f"[执行] 已删除冗余施主: {deleted_count} 条")
        print(f"[执行] 已补全 keeper 字段: {keeper_updated_count} 组")
    except Exception as e:
        conn.rollback()
        print(f"[错误] 合并失败，已回滚: {e}")
        raise
    finally:
        conn.close()

    # 5. 验证
    print("\n[验证] 重新打开数据库检查...")
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS cnt FROM fahui_users")
    print(f"  合并后 fahui_users 总数: {cur.fetchone()['cnt']}")

    cur.execute("""
        SELECT r.fahui_user_id, COUNT(*) AS cnt
        FROM fahui_records r
        LEFT JOIN fahui_users u ON r.fahui_user_id = u.id
        WHERE r.fahui_user_id IS NOT NULL AND u.id IS NULL
        GROUP BY r.fahui_user_id
    """)
    orphans = cur.fetchall()
    print(f"  孤立 fahui_user_id 引用数: {len(orphans)} (应为 0)")

    # 杨洁应仍为 9 条（姓名n不同，不应被合并）
    cur.execute("SELECT COUNT(*) AS cnt FROM fahui_users WHERE 施主姓名 = '杨洁'")
    print(f"  杨洁 记录数: {cur.fetchone()['cnt']} (应为 9，未被合并)")

    # 抽样验证：陈彦霏 第一组应被合并
    cur.execute("""
        SELECT COUNT(*) AS cnt FROM fahui_users
        WHERE 施主姓名='陈彦霏'
          AND 佛光接引一='未出生婴灵'
          AND 阳上一='陈彦霏 返荐'
    """)
    print(f"  陈彦霏(未出生婴灵/陈彦霏 返荐) 记录数: {cur.fetchone()['cnt']} (应为 1)")

    conn.close()
    print("\n[完成] 合并结束。")


if __name__ == '__main__':
    main()
