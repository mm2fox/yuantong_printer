---
name: "deploy"
description: "Creates deployment packages for temples, manages deployment records. Invoke when user asks to '部署', '创建部署包', '管理寺院部署', or '查看部署记录'."
---

# Temple Deployment

This skill creates deployment packages for individual temples and manages deployment records. Each temple gets its own independent directory with separate database, configuration, and uploads.

## Project Location

- Project root: `E:\Project\Print_tool\temple-management`
- Deploy tool: `E:\Project\Print_tool\temple-management\create_temple_package.py`
- Deploy manager: `E:\Project\Print_tool\temple-management\deploy_manager.py`
- Deploy records: `E:\Project\Print_tool\temple-management\deploy_records.json`
- Output directory: `E:\Project\Print_tool\temple-management\deploy\`

## Prerequisites

Before creating deployment packages, ensure the EXE has been built:
```powershell
cd "E:\Project\Print_tool\temple-management" ; python build.py
```

> **重要**: `build.py` 会先构建前端（`npm run build`）再打包 EXE。前端改动必须经过此步骤才能生效。切勿跳过 `build.py` 直接调用 `pyinstaller`，否则打包的是旧前端。

## Create Deployment Package

### Single Temple

```powershell
cd "E:\Project\Print_tool\temple-management" ; python create_temple_package.py <寺院名称> [选项]
```

Options:
- `--address <地址>` - Temple address
- `--username <用户名>` - Admin username (default: admin)
- `--password <密码>` - Admin password (empty = auto-generate on first startup)
- `--realname <姓名>` - Admin real name (default: 管理员)
- `--port <端口>` - Listening port (default: 8080)

Example:
```powershell
cd "E:\Project\Print_tool\temple-management" ; python create_temple_package.py 缘通寺 --address "浙江省杭州市" --password "yt2024"
```

### Multiple Temples (Batch)

```powershell
cd "E:\Project\Print_tool\temple-management" ; python create_temple_package.py batch --name 寺院A --address 地址A --password pwd1 --end --name 寺院B --address 地址B --password pwd2 --end
```

## Rebuild & Keep Database (重新打包保留数据)

当代码有改动需要重新打包时,构建 EXE 后创建部署包会生成**空数据库**。若要保留寺院的历史数据,需将旧数据库复制到新部署包中。

> **新流程**: 庆云寺等需要从远程 SQL Server 拉最新数据的寺院,见下文 [Remote Data Sync & Deploy](#remote-data-sync--deploy-远程拉数据并部署) 章节,不要再复制旧数据库。

### Old Database Locations (旧数据库位置)

旧版部署包位于 `dist\` 目录,按寺院拼音命名:

| 寺院名称 | 旧数据库路径 |
|---------|------------|
| 国庆寺 | `dist\guoqingsi\database\temple.db` |
| 伽蓝寺 | `dist\yanqingsi\database\temple.db` |

> 用 `Glob` 搜索 `**/temple.db` 可发现所有历史数据库文件。

### Migration Steps (迁移步骤)

创建部署包后,将旧数据库复制到新部署包的 `database\` 目录:

```powershell
# 国庆寺
Copy-Item -Path "E:\Project\Print_tool\temple-management\dist\guoqingsi\database\temple.db" -Destination "E:\Project\Print_tool\temple-management\deploy\国庆寺\database\temple.db" -Force

# 伽蓝寺
Copy-Item -Path "E:\Project\Print_tool\temple-management\dist\yanqingsi\database\temple.db" -Destination "E:\Project\Print_tool\temple-management\deploy\伽蓝寺\database\temple.db" -Force
```

### Password Logic (密码说明)

复制旧数据库后,登录密码以**数据库中的密码**为准,不是 `config.json` 中的 `admin_password`:

- **数据库已有 admin 用户** → 使用数据库中的旧密码登录（`password_hash` 字段,bcrypt 加密）
- **数据库无 admin 用户 + config.json 有明文密码** → 用 config 密码创建 admin,随后清除 config 明文密码
- **数据库无 admin 用户 + config.json 密码为空** → 自动生成随机密码,输出到日志 `%TEMP%\temple_management.log`

### Verify Migration (验证迁移)

复制后用 Python 验证数据库内容:

```powershell
cd "E:\Project\Print_tool\temple-management" ; python -c "import sqlite3; conn=sqlite3.connect('deploy/<寺院名称>/database/temple.db'); c=conn.cursor(); c.execute('SELECT id,username,real_name,role FROM users'); print('用户:', c.fetchall()); c.execute('SELECT id,寺庙名称 FROM temples'); print('寺庙:', c.fetchall()); conn.close()"
```

## Remote Data Sync & Deploy (远程拉数据并部署)

适用于:**数据源在远程 SQL Server** 的寺院(如庆云寺)。流程是 **先拉取远程最新数据 → 导入空数据库 → 再部署**。

### 适用场景

- 寺院本身用的是旧版 CStemple 系统(SQL Server 远程库)
- 远程库持续有新数据录入,部署前需拉最新
- 旧版数据库账号不是应用账号,而是 SQL Server 账号

> **账号区分(重要)**:
> - 应用账号(`印持`/`耀智`/`111111` 等)= 旧 CStemple 系统 `login` 表里的应用层用户,**不是** SQL Server 账号
> - SQL Server 账号(`qingyun`/`qingyun`) = 服务器级别账号,用于连接数据库
> - 两者是不同体系,登录 SQL Server 用后者

### 已知远程数据源

| 寺院 | SQL Server 地址 | 账号 | 库名 | 数据位置 |
|------|-----------------|------|------|----------|
| 庆云寺 | `93d1z808.wicp.vip,34219` | `qingyun`/`qingyun` | `qingyun` | `fahui` 表(法会记录)、`登记法会` 表(法会名称) |

- 远程 SQL Server 2008 R2,动态域名,可能不稳定
- 网络连通性测试:`python -c "import socket; s=socket.socket(); s.settimeout(8); s.connect(('93d1z808.wicp.vip',34219)); print('OK'); s.close()"`
- 若 `pyodbc` 未安装:`pip install pyodbc`(注意系统有多个 Python 环境,需用装了 pyodbc 的那个)

### Step 1: 拉取远程数据到 Excel

使用导出脚本生成标准格式 Excel(参照 [db\fahui_register_export.xlsx](file:///E:/Project/Print_tool/db/fahui_register_export.xlsx)):

```powershell
cd "E:\Project\Print_tool\script" ; C:\Users\admin\AppData\Local\Programs\Python\Python311\python.exe export_fahui.py
```

- 配置文件: [script\config.json](file:///E:/Project/Print_tool/script/config.json)(已配 `qingyun/qingyun`)
- 输出: `E:\Project\Print_tool\db\fahui_register_export.xlsx`
- 脚本逻辑: JOIN `fahui` + `登记法会` 取法会名,JOIN `gongdezhu` 取施主姓名电话,按 `yanwang` 分流 xm 字段
- 列名固定: 法会编号/法会名称/牌位类型/功德金/施主姓名/座次/往生/延生/已打印/电话/佛光接引一~四/阳上一~六/佛光注照一~四/施主编号/登记人/登记时间/年份

> **注意**: 必须用装了 pyodbc 的 Python(Python311),不是项目默认 Python。

### Step 2: 创建部署包(空数据库)

```powershell
cd "E:\Project\Print_tool\temple-management" ; python create_temple_package.py 庆云寺
```

生成 `deploy\庆云寺\` 目录,含 exe + config + 空数据库目录 + uploads/templates/。首次启动会自动建 9 张表但无业务数据。

### Step 3: 导入 Excel 数据到部署包数据库

新系统 `temple.db` 只有 9 张表(`users/temples/permissions/fahui_users/fahui_records/fahui_info/printer_templates/system_logs/version_info`),远程库是旧系统 97 张表,**不能直接复制**。

参照 [backend\app\api\database.py](file:///e:/Project/Print_tool/temple-management/backend/app/api/database.py) 的 `import_excel` 逻辑(L508-L767),写一次性脚本将 Excel 导入 `deploy\<寺院>\database\temple.db`。关键映射:

| Excel 列 | 目标字段 |
|---|---|
| 法会名称 | `fahui_info.法会名称`(去重),`fahui_records.fahui_name` |
| 牌位类型 | `fahui_records.paiwei_type` |
| 功德金 | `fahui_records.amount`(float) |
| 施主编号 | `fahui_users.施主编号`,`fahui_records.施主编号`(去重,空则生成 `IMP######`) |
| 施主姓名 | `fahui_users.施主姓名`,`fahui_records.施主姓名` |
| 座次 | `fahui_records.座次` |
| 往生/延生 | `fahui_records.yanwang`(往生=1,延生=0) |
| 已打印 | `fahui_records.prt`(否=0,空或=是=1) |
| 电话 | `fahui_users.电话`(仅更新非空) |
| 佛光接引一~四 | 延生→`xm1~xm4`,往生→`xm1~xm4` |
| 阳上一~六 | 往生→`xm5~xm10` |
| 佛光注照一~四 | 延生→`xm1~xm4` |
| 登记人 | `fahui_users.登记人`,`fahui_records.经办人` |
| 登记时间 | `fahui_users.登记时间`,`fahui_records.djdate` |
| 年份 | `fahui_records.remarks`(`年份:xxx`) |

> **xm 字段分流规则**: 延生(yanwang=0)取"佛光注照"→xm1~4,xm="佛光注照"; 往生(yanwang=1)取"佛光接引"→xm1~4 + "阳上"→xm5~10,xm="佛光接引"。

脚本要点(可参照已删除的 `_import_qingyun.py`):
1. `shutil.copy2` 复制其他寺院 db 作模板(保留 users/temples/permissions 结构),或直接 init 空 db
2. 清空 `fahui_records/fahui_users/fahui_info/system_logs`
3. `openpyxl.load_workbook(read_only=True, data_only=True)` 读 Excel,表头用 `_normalize_header` 去空格
4. 法会按名称去重写入 `fahui_info`,施主按编号去重写入 `fahui_users`,每行写 `fahui_records`
5. 设置 temples.寺庙名称、users 密码/角色(用 bcrypt 生成 hash)、清 system_logs

### Step 4: 设置密码和角色

```python
import bcrypt
new_hash = bcrypt.hashpw('111111'.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
# 参照 admin 的 role/permissions
c.execute("SELECT role, permissions FROM users WHERE username='admin'")
admin_role, admin_perms = c.fetchone()
c.execute("UPDATE users SET password_hash=?, role=?, permissions=?, is_active=1 WHERE username IN ('印持','耀智')",
          (new_hash, admin_role, admin_perms))
# 或新增用户
c.execute("INSERT INTO users (username, password_hash, real_name, role, permissions, is_active, temple_id, created_at, updated_at) VALUES (?,?,?,?,?,1,1,?,?)",
          ('演训', new_hash, '演训', admin_role, admin_perms, now, now))
```

### Step 5: 复制最新 EXE 到部署包

若 build.py 后新 exe 在 `dist\`,需复制到部署包:

```powershell
Copy-Item -Path "E:\Project\Print_tool\temple-management\dist\缘通寺院信息管理系统.exe" -Destination "E:\Project\Print_tool\temple-management\deploy\庆云寺\缘通寺院信息管理系统.exe" -Force
```

### Step 6: 验证部署包

```powershell
cd "E:\Project\Print_tool\temple-management" ; python -c "import sqlite3; conn=sqlite3.connect('deploy/庆云寺/database/temple.db'); c=conn.cursor(); c.execute('SELECT id,寺庙名称 FROM temples'); print('寺庙:', c.fetchall()); c.execute('SELECT id,username,real_name,role FROM users'); print('用户:', c.fetchall()); c.execute('SELECT COUNT(*) FROM fahui_records'); print('法会记录:', c.fetchone()[0]); c.execute('SELECT COUNT(*) FROM fahui_users'); print('施主:', c.fetchone()[0]); c.execute('SELECT COUNT(*) FROM fahui_info'); print('法会:', c.fetchone()[0]); c.execute('SELECT COUNT(*) FROM system_logs'); print('系统日志:', c.fetchone()[0]); conn.close()"
```

密码 bcrypt 校验:
```python
import bcrypt, sqlite3
conn = sqlite3.connect('deploy/庆云寺/database/temple.db')
h = conn.execute("SELECT password_hash FROM users WHERE username='印持'").fetchone()[0]
print(bcrypt.checkpw('111111'.encode(), h.encode()))  # 应为 True
```

### 庆云寺案例(2026-08-07 实例)

完整流程示例(已执行):
1. `python export_fahui.py`(Python311)→ 9722 条法会记录 → `fahui_register_export.xlsx`
2. `python build.py` → 新 exe(含翻转/对齐/PDF/数据同步功能)
3. `python create_temple_package.py 庆云寺` → 部署包骨架
4. 写迁移脚本(参照 import_excel 逻辑)→ 9722 条导入 fahui_records,5593 施主,17 法会,0 失败
5. UPDATE temples 设寺庙名=庆云寺,UPDATE users 印持/耀智 密码=111111 角色=管理员
6. 复制 dist exe → deploy\庆云寺\
7. 验证: 数据量/用户/密码全部通过

庆云寺部署账号:
- admin / admin123 / 管理员
- 印持 / 111111 / 管理员
- 耀智 / 111111 / 管理员

## Reset Database (重置干净数据库)

清空业务数据保留用户,或同时清空用户只留一个管理员。**操作前务必备份**:

```powershell
$ts = Get-Date -Format "yyyyMMdd_HHmmss"
Copy-Item "deploy\<寺院>\database\temple.db" "deploy\<寺院>\database\temple_backup_$ts.db"
```

清空业务数据(保留 users/temples/permissions/printer_templates/version_info):
```python
import sqlite3
conn = sqlite3.connect(r'deploy\<寺院>\database\temple.db')
c = conn.cursor()
for t in ['fahui_records', 'fahui_users', 'fahui_info', 'system_logs']:
    c.execute(f"DELETE FROM {t}")
try:
    c.execute("DELETE FROM sqlite_sequence WHERE name IN ('fahui_records','fahui_users','fahui_info','system_logs')")
except sqlite3.OperationalError:
    pass
conn.commit()
```

新增管理员(参照现有 admin 角色权限):
```python
import bcrypt, sqlite3
from datetime import datetime
conn = sqlite3.connect(r'deploy\<寺院>\database\temple.db')
c = conn.cursor()
c.execute("SELECT role, permissions FROM users WHERE username='admin'")
admin_role, admin_perms = c.fetchone()
new_hash = bcrypt.hashpw('111111'.encode(), bcrypt.gensalt()).decode()
now = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
c.execute("INSERT INTO users (username, password_hash, real_name, role, permissions, is_active, temple_id, created_at, updated_at) VALUES (?,?,?,?,?,1,1,?,?)",
          ('演训', new_hash, '演训', admin_role, admin_perms, now, now))
conn.commit()
```

## Manage Deployments

### List All Deployments

```powershell
cd "E:\Project\Print_tool\temple-management" ; python deploy_manager.py list
```

### Show Temple Details

```powershell
cd "E:\Project\Print_tool\temple-management" ; python deploy_manager.py show <序号|寺院名称>
```

Example:
```powershell
python deploy_manager.py show 1
python deploy_manager.py show 缘通寺
```

### Export Password List

```powershell
cd "E:\Project\Print_tool\temple-management" ; python deploy_manager.py export
```

Output: `passwords.txt` in project root.

## Deployment Directory Structure

Each temple gets an independent directory:

```
deploy/
├── 缘通寺/
│   ├── 缘通寺院信息管理系统.exe    # Application
│   ├── config.json                # Configuration
│   ├── database/
│   │   └── temple.db              # SQLite database (created on first run)
│   └── uploads/
│       └── templates/             # Print templates
├── 普济寺/
│   └── ...
└── 灵隐寺/
    └── ...
```

## Key Features

- **Database Isolation**: Each temple has its own `temple.db`
- **Configuration**: `config.json` defines temple name, admin credentials, port
- **Password Security**: Plain password in config.json is cleared after first initialization
- **Auto-generated Password**: If password is empty in config, a random 10-char password is generated on first startup (shown in logs)
- **Single Instance**: Uses named mutex to prevent multiple instances
- **Port Conflict**: Auto-finds available port if configured port is occupied

## First Startup

1. Copy the temple directory to target server
2. Run `缘通寺院信息管理系统.exe`
3. If admin password was auto-generated, check logs at `%TEMP%\temple_management.log`
4. Login with admin credentials
5. Change password immediately after first login

## Important Notes

- Always build the EXE first before creating deployment packages
- Each deployment package includes the same EXE but different config.json
- Deploy records are stored in `deploy_records.json` and auto-updated when creating packages
- The export command creates `passwords.txt` - keep it secure
- Database is created automatically on first run if it doesn't exist
- 密码存储在数据库 `users.password_hash` 中,`config.json` 的 `admin_password` 仅对首次初始化有效
- **远程数据源寺院**(如庆云寺)必须走 [Remote Data Sync & Deploy](#remote-data-sync--deploy-远程拉数据并部署) 流程,先拉数据再部署
- **重置数据库前务必备份**(`Copy-Item temple.db temple_backup_<时间戳>.db`)
- 远程 SQL Server 数据库账号与应用账号是两套体系,登录 SQL Server 用前者
