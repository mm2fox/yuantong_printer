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
