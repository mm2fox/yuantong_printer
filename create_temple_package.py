import os
import json
import shutil
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent

from deploy_manager import add_record

DEFAULT_CONFIG = {
    "temple_name": "默认寺院",
    "temple_address": "",
    "admin_username": "admin",
    "admin_password": "",
    "admin_real_name": "管理员",
    "port": 8080
}

def get_exe_path():
    dist_path = PROJECT_ROOT / "dist"
    if dist_path.exists():
        for item in dist_path.iterdir():
            if item.is_file() and item.suffix == ".exe":
                return item
    return None

def create_temple_package(temple_name, output_dir=None, config_overrides=None):
    exe_path = get_exe_path()
    if exe_path is None:
        print("错误: 未找到打包后的 exe 文件，请先运行 pyinstaller 打包")
        print("运行命令: pyinstaller temple_management.spec")
        return False

    config = {**DEFAULT_CONFIG, **(config_overrides or {})}
    config["temple_name"] = temple_name
    
    if output_dir is None:
        output_dir = PROJECT_ROOT / "deploy" / temple_name
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    print(f"创建寺院部署包: {temple_name}")
    print(f"输出目录: {output_dir}")
    
    shutil.copy2(str(exe_path), str(output_dir / exe_path.name))
    
    config_path = output_dir / "config.json"
    with open(config_path, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)
    
    (output_dir / "database").mkdir(exist_ok=True)
    (output_dir / "uploads" / "templates").mkdir(parents=True, exist_ok=True)
    
    print(f"  - 复制 exe 文件: {exe_path.name}")
    print(f"  - 创建配置文件: config.json")
    print(f"  - 创建数据库目录: database/")
    print(f"  - 创建模板目录: uploads/templates/")
    print(f"\n配置信息:")
    print(f"  寺院名称: {config['temple_name']}")
    print(f"  寺院地址: {config['temple_address']}")
    print(f"  管理员账号: {config['admin_username']}")
    print(f"  管理员密码: {config['admin_password'] or '(首次启动自动生成，见日志)'}")
    print(f"  监听端口: {config['port']}")
    print(f"\n部署包创建完成！")
    print(f"请将 {output_dir} 文件夹复制到目标寺院的服务器上即可运行。")
    
    add_record(temple_name, config, output_dir)
    
    return True

def batch_create_packages(temples):
    for temple in temples:
        print("=" * 50)
        create_temple_package(
            temple_name=temple["name"],
            config_overrides={
                "temple_address": temple.get("address", ""),
                "admin_username": temple.get("admin_username", "admin"),
                "admin_password": temple.get("admin_password", "admin123"),
                "admin_real_name": temple.get("admin_real_name", "管理员"),
                "port": temple.get("port", 8080)
            }
        )

def main():
    print("=" * 50)
    print("缘通寺院信息管理系统 - 部署包生成工具")
    print("=" * 50)
    
    if len(sys.argv) > 1:
        if sys.argv[1] == "batch":
            temples = []
            i = 2
            while i < len(sys.argv):
                if sys.argv[i].startswith("--"):
                    key = sys.argv[i][2:]
                    i += 1
                    if i < len(sys.argv):
                        if key == "name":
                            current_temple = {"name": sys.argv[i]}
                        elif key == "address":
                            current_temple["address"] = sys.argv[i]
                        elif key == "username":
                            current_temple["admin_username"] = sys.argv[i]
                        elif key == "password":
                            current_temple["admin_password"] = sys.argv[i]
                        elif key == "realname":
                            current_temple["admin_real_name"] = sys.argv[i]
                        elif key == "port":
                            current_temple["port"] = int(sys.argv[i])
                        elif key == "end":
                            temples.append(current_temple)
                    i += 1
            if temples:
                batch_create_packages(temples)
            else:
                print("请指定寺院信息")
        else:
            temple_name = sys.argv[1]
            config_overrides = {}
            i = 2
            while i < len(sys.argv):
                if sys.argv[i].startswith("--"):
                    key = sys.argv[i][2:]
                    i += 1
                    if i < len(sys.argv):
                        if key == "address":
                            config_overrides["temple_address"] = sys.argv[i]
                        elif key == "username":
                            config_overrides["admin_username"] = sys.argv[i]
                        elif key == "password":
                            config_overrides["admin_password"] = sys.argv[i]
                        elif key == "realname":
                            config_overrides["admin_real_name"] = sys.argv[i]
                        elif key == "port":
                            config_overrides["port"] = int(sys.argv[i])
                    i += 1
                else:
                    i += 1
            create_temple_package(temple_name, config_overrides=config_overrides)
    else:
        print("使用方法:")
        print("  python create_temple_package.py <寺院名称> [选项]")
        print("")
        print("选项:")
        print("  --address <地址>          设置寺院地址")
        print("  --username <用户名>       设置管理员账号")
        print("  --password <密码>         设置管理员密码")
        print("  --realname <真实姓名>     设置管理员真实姓名")
        print("  --port <端口>             设置监听端口")
        print("")
        print("示例:")
        print("  python create_temple_package.py 缘通寺 --address \"XX省XX市\" --password \"123456\"")
        print("")
        print("批量创建:")
        print("  python create_temple_package.py batch")
        print("    --name 寺院A --address 地址A --end")
        print("    --name 寺院B --address 地址B --end")

if __name__ == "__main__":
    main()