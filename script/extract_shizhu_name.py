# -*- coding: utf-8 -*-
"""从姓名n字段提取施主姓名，填入空的 施主姓名 字段

提取规则（用户确认）：
  1. 合家 + 阖家 都处理
  2. 去掉前缀（善信/后裔/孝女/孝子/孝孙/先父/先母等）取主体
  3. 多人合家取第一个姓名
  4. 不含合家/阖家的也尝试提取（去掉长生/往生/大人等后缀）
  5. 最后把姓名里面的空格去掉

用法：
  python extract_shizhu_name.py --dry-run    # 仅预览
  python extract_shizhu_name.py              # 实际执行（自动备份）
"""
import sqlite3
import os
import sys
import shutil
import argparse
from datetime import datetime

DB_PATH = r'e:\Project\Print_tool\temple-management\deploy\国庆寺\database\temple.db'

# 字段优先级：优先从"阳上"提取（最可能是施主），然后佛光注照，最后佛光接引
FIELD_PRIORITY = [
    '阳上一', '阳上二', '阳上三', '阳上四', '阳上五', '阳上六',
    '佛光注照一', '佛光注照二', '佛光注照三', '佛光注照四',
    '佛光接引一', '佛光接引二', '佛光接引三', '佛光接引四',
]

# 前缀（按长度降序匹配，避免"孝孙女"被"女"抢先匹配）
PREFIXES = [
    # 三字
    '孝孙女', '先祖父', '先祖母', '先考妣', '先祖考', '先祖妣',
    '外孙女', '外甥女', '孙女儿',
    # 两字
    '善信', '后裔', '孝女', '孝子', '孝孙', '善男',
    '信女', '信士', '弟子', '先父', '先母', '先考', '先妣',
    '亡父', '亡母', '故父', '故母',
    '孙女', '外孙', '外甥', '侄女', '侄子', '孙子',
    '女婿', '孙婿', '妹夫', '姐夫', '师兄', '师姐',
    '师弟', '师妹', '同修', '道友', '儿媳', '孙媳',
    # 单字
    '女',
]

# 非人名关键词（法会超度对象），含这些词的跳过
SKIP_KEYWORDS = [
    '历代宗亲', '冤亲债主', '婴灵', '门中', '七世父母', '六亲眷属',
    '十方', '一切', '众生', '孤魂', '野鬼', '亡灵',
]

# 后缀（去掉这些及其后内容）
SUFFIXES = ['大人', '长生', '往生', '超度', '居士', '菩萨', '尊者', '老菩萨']


def normalize(v):
    if v is None:
        return ''
    return str(v).strip()


def extract_name(raw):
    """从姓名n字段内容提取施主姓名"""
    s = normalize(raw)
    if not s:
        return ''

    # 1. 跳过非人名内容（法会对象）
    for kw in SKIP_KEYWORDS:
        if kw in s:
            return ''

    # 2. 去掉"合家/阖家"及其后内容
    for sep in ['合家', '阖家']:
        idx = s.find(sep)
        if idx >= 0:
            s = s[:idx]
            break

    # 3. 去掉常见后缀及其后内容
    for suffix in SUFFIXES:
        idx = s.find(suffix)
        if idx >= 0:
            s = s[:idx]
            break

    s = s.strip()
    if not s:
        return ''

    # 4. 去掉前缀（前缀后必须跟空格，避免误匹配；按长度降序）
    for prefix in sorted(PREFIXES, key=len, reverse=True):
        if s == prefix:
            return ''
        if s.startswith(prefix + ' '):
            s = s[len(prefix) + 1:].strip()
            break

    if not s:
        return ''

    # 5. 多人合家：取第一个姓名
    #    按空格分段：第一段是单字(姓)则合并前两段；否则取第一段
    parts = s.split()
    if len(parts) == 0:
        return ''
    elif len(parts) == 1:
        result = parts[0]
    elif len(parts[0]) == 1:
        # 第一段是单字（可能是姓），合并前两段
        result = parts[0] + parts[1]
    else:
        # 第一段长度>=2，取第一段
        result = parts[0]

    # 6. 最终去掉所有空格
    result = result.replace(' ', '')

    # 7. 过滤：至少2个字才作为有效姓名
    if len(result) < 2:
        return ''

    return result


def backup(db_path):
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')
    bak = db_path.replace('.db', f'_before_extract_{ts}.db')
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

    # 查询所有空施主姓名的记录
    cur.execute("""
        SELECT * FROM fahui_users
        WHERE 施主姓名 IS NULL OR TRIM(施主姓名) = ''
    """)
    rows = cur.fetchall()
    print(f"[扫描] 空施主姓名记录数: {len(rows)}")

    # 对每条记录计算提取结果
    updates = []  # [(id, 提取的姓名, 来源字段, 原始内容), ...]
    skip_count = 0
    for r in rows:
        extracted = ''
        source_field = ''
        source_value = ''
        for field in FIELD_PRIORITY:
            raw = r[field]
            if normalize(raw):
                extracted = extract_name(raw)
                if extracted:
                    source_field = field
                    source_value = raw
                    break
        if extracted:
            updates.append((r['id'], extracted, source_field, source_value))
        else:
            skip_count += 1

    print(f"[结果] 可提取姓名: {len(updates)} 条")
    print(f"[结果] 无法提取(跳过): {skip_count} 条")

    # 打印样本：前 40 条
    print("\n[预览] 前 40 条提取结果:")
    print(f"  {'id':<8} {'提取姓名':<10} {'来源字段':<12} {'原始内容'}")
    print(f"  {'-'*8} {'-'*10} {'-'*12} {'-'*30}")
    for uid, name, field, raw in updates[:40]:
        print(f"  {uid:<8} {name:<10} {field:<12} {raw!r}")

    # 打印跳过的样本
    print(f"\n[预览] 跳过的记录样本（前 20 条无法提取的）:")
    skipped_samples = []
    for r in rows:
        all_names = [(f, normalize(r[f])) for f in FIELD_PRIORITY if normalize(r[f])]
        if all_names:
            extracted = False
            for field, raw in all_names:
                if extract_name(raw):
                    extracted = True
                    break
            if not extracted:
                skipped_samples.append((r['id'], all_names[0]))
        else:
            skipped_samples.append((r['id'], ('(空)', '')))
        if len(skipped_samples) >= 20:
            break
    for uid, (field, raw) in skipped_samples:
        print(f"  id={uid}, {field}={raw!r}")

    if args.dry_run:
        print("\n[DRY-RUN] 未写库。如需执行，请去掉 --dry-run 重新运行。")
        conn.close()
        return

    # 实际执行
    print(f"\n[执行] 开始更新 {len(updates)} 条记录...")
    try:
        cur.execute("BEGIN")
        updated = 0
        for uid, name, field, raw in updates:
            cur.execute(
                "UPDATE fahui_users SET 施主姓名 = ? WHERE id = ?",
                (name, uid)
            )
            updated += cur.rowcount
        conn.commit()
        print(f"[执行] 已更新: {updated} 条")
    except Exception as e:
        conn.rollback()
        print(f"[错误] 更新失败，已回滚: {e}")
        raise
    finally:
        conn.close()

    # 验证
    print("\n[验证] 重新检查...")
    conn = sqlite3.connect(DB_PATH)
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM fahui_users WHERE 施主姓名 IS NULL OR TRIM(施主姓名) = ''")
    print(f"  空施主姓名记录数: {cur.fetchone()[0]} (原 5114)")
    cur.execute("SELECT COUNT(*) FROM fahui_users WHERE 施主姓名 = '冯煜'")
    print(f"  冯煜 记录数: {cur.fetchone()[0]}")
    conn.close()
    print("[完成]")


if __name__ == '__main__':
    main()
