# 数据库管理 - 添加 Excel 导入功能计划

## 需求概述

在"数据库管理"模块中添加"导入Excel"菜单项和功能，支持将 `E:\Project\Print_tool\db` 目录下的 Excel 文件（`.xls` / `.xlsx`）导入到系统数据库中。

## 现有分析

### Excel 文件结构
db 目录下有两个 `.xls` 文件，列结构一致（23列）：
- `2014-6.19-yansheng.xls` — 延生法会数据（33行含表头）
- `2014-qingming-wangsheng.xls` — 往生法会数据（33行含表头）

Excel 列名：`施主姓名, 座次, 往生/延生, 已打印, 电话, 佛光接引一~四, 阳上一~六, 佛光注照一~四, 施主编号, 登记人, 登记时间, 年份`

### 数据库模型
- **FahuiUser**（施主）：施主编号、施主姓名、电话、地址、功德主、佛光接引一~四、阳上一~六、佛光注照一~四、登记人、登记时间、备注、temple_id
- **FahuiRecord**（法会记录）：fahui_user_id、fahui_id、fahui_name、座次、amount、paiwei_type、yanwang、xm1~xm10、xm、djdate、经办人、prt、remarks、施主姓名、施主编号、temple_id
- **FahuiInfo**（法会信息）：法会名称、开始日期、截止日期、功德金中/小/大、完成状态、备注、temple_id

### 导入逻辑
Excel 数据需要同时写入 FahuiUser 和 FahuiRecord 两张表：
1. 每行 Excel → 根据施主编号去重判断：若已存在则复用已有施主，否则创建新施主
2. 每行 Excel → 创建一条 FahuiRecord 记录（法会记录），关联到对应的 FahuiUser
3. `往生/延生` 列映射到 `yanwang` 字段（延生=0，往生=1）
4. 需要用户选择关联的法会（FahuiInfo），以填充 fahui_id 和 fahui_name

### 施主去重策略
- **去重依据**：以 `施主编号` 为主键进行去重
- **去重逻辑**：
  1. 导入前，先查询数据库中所有已有的 FahuiUser，构建 `施主编号 → FahuiUser.id` 的映射表
  2. 逐行处理 Excel 数据时，先检查该行的 `施主编号` 是否已存在于映射表中
  3. 如果**已存在**：复用已有施主的 `id`，不创建新的 FahuiUser 记录，但**更新**该施主的字段（电话、佛光接引、阳上、佛光注照等，仅当 Excel 中对应值非空时才更新）
  4. 如果**不存在**：创建新的 FahuiUser 记录，并将新记录加入映射表（避免同一 Excel 中重复施主编号被重复创建）
  5. 每行都创建一条新的 FahuiRecord 记录，关联到对应施主的 `fahui_user_id`
- **同文件内去重**：同一 Excel 文件中可能有多行具有相同施主编号（同一施主参加不同法会），这些行应关联到同一个 FahuiUser

## 实施步骤

### 步骤 1：后端 - 安装 Excel 处理依赖

在 `backend/requirements.txt` 中添加：
```
openpyxl==3.1.2
xlrd==2.0.2
```
- `openpyxl` 用于读取 `.xlsx` 格式
- `xlrd` 用于读取 `.xls` 格式（db 目录下的文件是此格式）

### 步骤 2：后端 - 添加 Excel 导入 API

在 `backend/app/api/database.py` 中新增以下端点：

#### 2.1 `GET /api/database/excel-files` — 获取可导入的 Excel 文件列表
- 扫描配置的 Excel 目录（默认 `E:\Project\Print_tool\db`）
- 返回文件名列表（仅 `.xls` / `.xlsx`）
- 需要管理员权限

#### 2.2 `GET /api/database/excel-preview/{filename}` — 预览 Excel 文件内容
- 读取指定 Excel 文件的前 N 行（如前 5 行）
- 返回列名和预览数据，供用户确认映射关系
- 需要管理员权限

#### 2.3 `POST /api/database/import-excel` — 执行 Excel 导入
- 请求参数：`filename`（文件名）、`fahui_id`（关联法会ID，可选）
- 读取 Excel 文件，逐行解析
- 列映射逻辑：
  - `施主编号` → FahuiUser.施主编号、FahuiRecord.施主编号
  - `施主姓名` → FahuiUser.施主姓名、FahuiRecord.施主姓名
  - `电话` → FahuiUser.电话
  - `佛光接引一~四` → FahuiUser.佛光接引一~四
  - `阳上一~六` → FahuiUser.阳上一~六
  - `佛光注照一~四` → FahuiUser.佛光注照一~四
  - `登记人` → FahuiUser.登记人、FahuiRecord.经办人
  - `登记时间` → FahuiUser.登记时间、FahuiRecord.djdate
  - `座次` → FahuiRecord.座次
  - `往生/延生` → FahuiRecord.yanwang（延生=0，往生=1）
  - `已打印` → FahuiRecord.prt（是=1，否=0）
- 施主去重逻辑：
  1. 导入前查询所有已有 FahuiUser，构建 `施主编号 → FahuiUser` 映射
  2. 逐行处理时，按施主编号查找：
     - **已存在**：复用已有施主 id，更新非空字段
     - **不存在**：创建新 FahuiUser，加入映射（防同文件内重复创建）
  3. 每行均创建一条新的 FahuiRecord，关联到对应施主的 fahui_user_id
  4. 如果指定了 fahui_id，则填充 FahuiRecord.fahui_id 和 fahui_name
- 返回导入结果（成功数、失败数、跳过数/复用数、失败详情）
- 需要管理员权限

### 步骤 3：前端 - 添加 API 方法

在 `frontend/src/api/database.js` 中添加：
```javascript
getExcelFiles()           // GET /database/excel-files
previewExcel(filename)    // GET /database/excel-preview/{filename}
importExcel(filename, fahuiId)  // POST /database/import-excel
```

### 步骤 4：前端 - 在数据库管理页面添加导入功能

修改 `frontend/src/views/system/DatabaseManagement.vue`，在"数据库操作"卡片中添加"导入Excel"操作区域：

功能设计：
1. 显示一个"导入Excel"操作区块，包含：
   - 一个下拉选择框，列出 db 目录下可用的 Excel 文件
   - 一个下拉选择框，选择关联的法会（可选，从 FahuiInfo 列表获取）
   - 一个"预览"按钮，点击后弹出对话框显示 Excel 前几行数据
   - 一个"导入"按钮，执行导入操作
2. 导入前弹出确认对话框
3. 导入后显示结果（成功/失败数量）
4. 导入完成后刷新数据库信息

### 步骤 5：前端 - 添加路由和菜单

在"系统管理"子菜单中添加"导入Excel"菜单项：
- 修改 `frontend/src/router/index.js`：添加路由 `system/import-excel`
- 修改 `frontend/src/views/Layout.vue`：在系统管理子菜单中添加菜单项

**或者**（更推荐的方案）：不新增独立页面，而是在现有数据库管理页面中直接添加导入功能区域，无需新增路由和菜单。这样更符合"在数据库管理中添加导入Excel功能"的需求。

## 推荐方案

采用**步骤 5 的第二种方案**：直接在现有的 `DatabaseManagement.vue` 页面中添加 Excel 导入功能区域，不新增独立页面和路由。这样：
- 用户在"数据库管理"页面就能看到并使用导入功能
- 不需要修改路由和菜单配置
- 与现有的备份/恢复/清空操作在同一页面，操作逻辑一致

## 涉及文件清单

| 文件 | 操作 |
|------|------|
| `backend/requirements.txt` | 修改 - 添加 openpyxl、xlrd 依赖 |
| `backend/app/api/database.py` | 修改 - 添加 3 个 Excel 导入相关端点 |
| `frontend/src/api/database.js` | 修改 - 添加 3 个 API 方法 |
| `frontend/src/views/system/DatabaseManagement.vue` | 修改 - 添加 Excel 导入功能区域 |
