import json
import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent
PACKAGES_DIR = PROJECT_ROOT / "packages"
DEPLOY_RECORD_FILE = PROJECT_ROOT / "deploy_records.json"

def load_records():
    if DEPLOY_RECORD_FILE.exists():
        with open(DEPLOY_RECORD_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"temples": []}

def save_records(records):
    with open(DEPLOY_RECORD_FILE, 'w', encoding='utf-8') as f:
        json.dump(records, f, ensure_ascii=False, indent=2)

def add_record(temple_name, config, package_path):
    records = load_records()
    
    for i, t in enumerate(records["temples"]):
        if t["temple_name"] == temple_name:
            records["temples"][i] = {
                "temple_name": temple_name,
                "temple_address": config.get("temple_address", ""),
                "admin_username": config.get("admin_username", "admin"),
                "admin_password": config.get("admin_password", ""),
                "port": config.get("port", 8080),
                "package_path": str(package_path),
                "created_at": t.get("created_at", datetime.now().isoformat()),
                "updated_at": datetime.now().isoformat()
            }
            save_records(records)
            return
    
    records["temples"].append({
        "temple_name": temple_name,
        "temple_address": config.get("temple_address", ""),
        "admin_username": config.get("admin_username", "admin"),
        "admin_password": config.get("admin_password", ""),
        "port": config.get("port", 8080),
        "package_path": str(package_path),
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat()
    })
    save_records(records)

def list_records():
    records = load_records()
    if not records["temples"]:
        print("暂无部署记录")
        return
    
    print("=" * 80)
    print(f"{'序号':<4} {'寺院名称':<15} {'地址':<20} {'端口':<6} {'管理员':<10}")
    print("=" * 80)
    for i, t in enumerate(records["temples"], 1):
        addr = t.get("temple_address", "")[:18] or "-"
        pwd = t.get("admin_password", "")
        pwd_display = pwd if pwd else "(自动生成)"
        print(f"{i:<4} {t['temple_name']:<15} {addr:<20} {t.get('port', 8080):<6} {t.get('admin_username', 'admin')}")
    print("=" * 80)
    print(f"共 {len(records['temples'])} 个寺院")

def show_detail(index=None, name=None):
    records = load_records()
    
    if index is not None:
        if 1 <= index <= len(records["temples"]):
            t = records["temples"][index - 1]
        else:
            print(f"序号 {index} 不存在")
            return
    elif name:
        for t in records["temples"]:
            if t["temple_name"] == name:
                break
        else:
            print(f"寺院 '{name}' 不存在")
            return
    else:
        print("请指定序号或名称")
        return
    
    print("=" * 50)
    print(f"寺院名称: {t['temple_name']}")
    print(f"寺院地址: {t.get('temple_address', '-')}")
    print(f"管理员账号: {t.get('admin_username', 'admin')}")
    pwd = t.get("admin_password", "")
    print(f"管理员密码: {pwd if pwd else '(首次启动自动生成)'}")
    print(f"监听端口: {t.get('port', 8080)}")
    print(f"部署包路径: {t.get('package_path', '-')}")
    print(f"创建时间: {t.get('created_at', '-')}")
    print(f"更新时间: {t.get('updated_at', '-')}")
    print("=" * 50)

def export_passwords():
    records = load_records()
    output_file = PROJECT_ROOT / "passwords.txt"
    
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("缘通寺院信息管理系统 - 管理员密码清单\n")
        f.write(f"导出时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("=" * 60 + "\n\n")
        
        for t in records["temples"]:
            pwd = t.get("admin_password", "")
            f.write(f"寺院: {t['temple_name']}\n")
            f.write(f"地址: {t.get('temple_address', '-')}\n")
            f.write(f"账号: {t.get('admin_username', 'admin')}\n")
            f.write(f"密码: {pwd if pwd else '(首次启动自动生成，见日志)'}\n")
            f.write(f"端口: {t.get('port', 8080)}\n")
            f.write("-" * 40 + "\n\n")
        
        f.write(f"共 {len(records['temples'])} 个寺院\n")
    
    print(f"密码清单已导出到: {output_file}")
    print("请妥善保管此文件！")

def main():
    if len(sys.argv) < 2:
        print("使用方法:")
        print("  python deploy_manager.py list              # 查看所有部署记录")
        print("  python deploy_manager.py show <序号|名称>  # 查看详情")
        print("  python deploy_manager.py export            # 导出密码清单")
        print("")
        print("提示: 创建部署包时会自动记录到此系统")
        return
    
    cmd = sys.argv[1]
    
    if cmd == "list":
        list_records()
    elif cmd == "show":
        if len(sys.argv) >= 3:
            arg = sys.argv[2]
            if arg.isdigit():
                show_detail(index=int(arg))
            else:
                show_detail(name=arg)
        else:
            print("请指定序号或寺院名称")
    elif cmd == "export":
        export_passwords()
    else:
        print(f"未知命令: {cmd}")

if __name__ == "__main__":
    main()