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

## Rebuild & Migrate Database (重新打包迁移数据)

当代码有改动需要重新打包时,构建 EXE 后创建部署包会生成**空数据库**。若要保留寺院的历史数据（用户、施主、法会记录、原有账号密码）,需将旧数据库复制到新部署包中。

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
- **重新打包时务必复制旧数据库**（见上文 Rebuild & Migrate Database 章节）,否则用户需重新注册且历史数据丢失
- 密码存储在数据库 `users.password_hash` 中,`config.json` 的 `admin_password` 仅对首次初始化有效
