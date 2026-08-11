# 需求固化：二维码打印页面的“业务员信息”下拉框数据源

> **注意**：本文档中涉及的域名（如 `scan.example.com`）仅为示例。实际部署时请替换为您自己的域名。详见 [域名配置说明](./DOMAIN_CONFIGURATION.md)。

## 权限配置规范与角色矩阵

### 权限系统概述

本系统采用基于数据库的权限管理系统，支持角色-权限映射和细粒度权限控制。

### 角色定义

| 角色代码 | 角色名称 | 用户标识 | 权限范围 | 描述 |
|---------|---------|---------|---------|------|
| `admin` | 超级管理员 | admin/admin | `*` | 系统全部权限，任何资源任何操作 |
| `operator` | 系统操作员 | - | 除删除外的所有操作 | 新增、编辑、查询、下载、打印；禁止删除 |
| `manager` | 管理者 | 部门经理/总监/副总/总/董事/董事长 | 浏览+生产数据管理 | 只能浏览+对生产数据的删除/下载/打印 |
| `viewer` | 系统浏览者 | - | 仅浏览 | 无其他任何操作权限 |

### 权限命名规范

**格式**: `resource.action`

**资源类型**:
- `company` - 公司管理
- `department` - 部门管理  
- `staff` - 员工管理
- `logistics` - 物流管理
- `qr` - 二维码管理
- `qr_history` - 二维码历史
- `users` - 用户管理

**操作类型**:
- `view` - 查看
- `create` - 创建
- `update` - 编辑
- `delete` - 删除
- `download` - 下载
- `print` - 打印
- `generate` - 生成（二维码专用）

### 角色权限矩阵

#### 超级管理员 (admin)
```
权限: * (通配符，所有权限)
```

#### 系统操作员 (operator)
```
公司管理: company.view, company.create, company.update
部门管理: department.view, department.create, department.update
员工管理: staff.view, staff.create, staff.update
物流管理: logistics.view, logistics.create, logistics.update
二维码: qr.view, qr.generate, qr.download, qr.print
二维码历史: qr_history.view, qr_history.download, qr_history.print
用户管理: 无权限
删除操作: 全部禁止
```

#### 管理者 (manager)
```
基础浏览: company.view, department.view, staff.view, logistics.view
生产数据管理: 
  - qr.view, qr.delete, qr.download, qr.print
  - qr_history.view, qr_history.delete, qr_history.download, qr_history.print
其他操作: 禁止 (create, update)
```

#### 系统浏览者 (viewer)
```
仅浏览权限: 
  - company.view, department.view, staff.view
  - logistics.view, qr.view, qr_history.view
其他操作: 全部禁止
```

### 生产数据定义

**生产数据**仅限于：
- 二维码打印列表 (`qr`)
- 二维码历史记录 (`qr_history`)

### 权限检查实现

#### 中央校验方法
```python
from utils.permissions import has_permission

# 检查权限
if has_permission(user, "qr.generate"):
    # 允许生成二维码
    pass

# 支持通配符
if has_permission(user, "logistics.*"):
    # 拥有物流模块所有权限
    pass
```

#### 按钮级权限控制
```python
# 删除按钮权限检查
if has_permission(current_user, "qr.delete"):
    delete_btn.setEnabled(True)
else:
    delete_btn.setVisible(False)  # 隐藏无权限按钮

# 打印按钮权限检查  
if has_permission(current_user, "qr.print"):
    print_btn.setEnabled(True)
else:
    print_btn.setToolTip("您没有打印权限")
    print_btn.setEnabled(False)
```

#### 模块入口权限检查
```python
# 进入模块前检查浏览权限
if not has_permission(current_user, "qr.view"):
    QMessageBox.warning(None, "权限不足", "您没有访问此模块的权限")
    return
```

### 数据库结构

#### 核心表结构
```sql
-- 权限表
CREATE TABLE permissions (
    id INTEGER PRIMARY KEY,
    resource TEXT NOT NULL,  -- 资源名
    action TEXT NOT NULL,    -- 操作名
    description TEXT,        -- 权限描述
    UNIQUE(resource, action)
);

-- 角色权限关联表
CREATE TABLE role_permissions (
    id INTEGER PRIMARY KEY,
    role_id INTEGER NOT NULL,
    permission_id INTEGER NOT NULL,
    FOREIGN KEY (role_id) REFERENCES roles (id),
    FOREIGN KEY (permission_id) REFERENCES permissions (id),
    UNIQUE(role_id, permission_id)
);

-- 用户角色关联表  
CREATE TABLE user_roles (
    user_id INTEGER NOT NULL,
    role_id INTEGER NOT NULL,
    assigned_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (user_id, role_id)
);
```

### 菜单与按钮控制策略

1. **动态隐藏**: 无权限的菜单项和按钮完全隐藏
2. **禁用提示**: 某些场景下禁用并显示权限提示
3. **分级控制**: 
   - 模块级: 控制菜单显示
   - 功能级: 控制按钮可用性
   - 操作级: 控制具体操作执行

### 权限扩展方案 (可选)

#### 审计员 (auditor)
```
权限: 所有模块的查看 + 导出下载
特点: 无打印、无删除、无修改
适用: 财务审计、数据分析人员
```

#### 物流文员 (logistics_clerk)  
```
权限: logistics.view/create/update + qr/qr_history.view
特点: 专门负责物流数据维护
限制: 无删除权限
```

#### 分级管理者
```
- DeptManager: 部门经理
- Director: 总监  
- VP: 副总
- GM: 总经理
- Board: 董事
- Chairman: 董事长
权限: 相同 (manager权限)
区别: 仅用于统计展示和审计追踪
```

### 配置文件位置

- 权限配置参考: `config/permissions.json`
- 数据库权限: `qr_system.db` (permissions, role_permissions, user_roles表)
- 权限工具类: `utils/permissions.py`

### 初始化数据

系统已预置以下初始数据:
- 4个标准角色 (admin, operator, manager, viewer)
- 29个基础权限
- admin用户默认拥有admin角色
- 71条角色权限映射关系

---

- 需求时间：2025-09-25
- 模块：二维码打印（modules/qr_print_widget.py）
- 需求描述：
  - “业务员信息”下拉框的选项需要直接链接员工信息管理模块的数据源（数据库 staff 表），显示格式为“姓名 (工号)”。
  - 打开二维码打印页面时，应默认选中员工信息列表的第一行（即第一个员工的姓名与工号）。

## 技术实现

- 在 QRPrintWidget.initUI 中，已构建“业务员信息”下拉框并加入 combos_col1 列表（位于右栏顶部，行号0，列2）。
- 在 QRPrintWidget.load_data_to_combos 中：
  - 复用对 staff 表的查询（SELECT name, employee_id FROM staff ORDER BY name）。
  - 将所得 staff_names（如“示例员工A (20030001)”、“示例员工B (20030002)”）赋值给“业务员信息”下拉框（combos_col1[8]）。
  - 默认选中索引0，确保页面初次打开即显示员工列表第一行。
- 已保持与页面其他控件一致的样式与信号联动，避免额外耦合。

## 注意事项
- 若员工表为空，将显示空列表；后续只需在员工信息管理模块新增员工数据，即可自动出现在“业务员信息”下拉框中。
- 当前保存与表格显示仍沿用“发行人”字段（issuer_name）；如需将“业务员信息”单独入库为 salesperson 字段，可在 save_qr_record 和 load_qr_records 中按需扩展。

---

# JSON文件存储和同步规范（强制固化）

## 本地电脑端路径要求（必须严格遵守）
- **A系列JSON文件必须存放在**: `C:\Projects\Demo\cloud\demo_json_a\`
- **B系列JSON文件必须存放在**: `C:\Projects\Demo\cloud\demo_json_b\`
- **生成规则**: 本地电脑通过系统打印二维码标签后分别生成的A-Q*.JSON和B-Q*.JSON文件只能且必须分别存放在上述指定目录下

## 云服务器端路径要求（必须严格遵守）
- **服务器物理路径**:
  - `C:\inetpub\qr-system\companies\demo_json_a\` (A系列JSON文件)
  - `C:\inetpub\qr-system\companies\demo_json_b\` (B系列JSON文件)
- **对应 FTP 虚拟路径**:
  - `/companies/demo_json_a/` (A系列)
  - `/companies/demo_json_b/` (B系列)

## 自动同步要求（必须几乎同时完成）
- 本地JSON文件生成后，必须几乎在同时被自动同步上传到云服务器对应目录
- **A-Q*.json**: `C:\Projects\Demo\cloud\demo_json_a\` → `C:\inetpub\qr-system\companies\demo_json_a\`
- **B-Q*.json**: `C:\Projects\Demo\cloud\demo_json_b\` → `C:\inetpub\qr-system\companies\demo_json_b\`

## 强制要求和验证
- 所有自动/手动上传脚本、服务配置、计划任务，统一使用 `/companies/demo_json_a/` 与 `/companies/demo_json_b/`
- FTP根目录映射到 `C:\inetpub\qr-system\companies\`，确保JSON文件正确同步
- 若发现错误路径配置，应立即删除并修正

## 实施确认点
- ✅ PowerShell 上传器使用正确的 `/companies/demo_json_a/`、`/companies/demo_json_b/` 路径
- ✅ 文件监控器 `windows_ftp_json_watcher.ps1` 监控正确的本地目录
- ✅ `auto_sync/config.json` 配置正确的同步路径
- ✅ `config/ftp_config.json` 使用正确的 base_path
- ✅ 计划任务 QRJsonyour_ftp_username 正确扫描 `cloud/demo_json_a/` 与 `cloud/demo_json_b/`

## 验证方法
- 检查 `auto_sync/logs/ftp_uploader.log`，确认上传目标路径为 `/companies/demo_json_a/` 或 `/companies/demo_json_b/`
- 确认云服务器 `C:\inetpub\qr-system\companies\` 目录下存在 `demo_json_a/` 和 `demo_json_b/` 子目录
- 验证JSON文件能从本地正确同步到云服务器指定位置

# 移动端UI页面设计规范（强制固化）

## 整体布局结构（从上到下）

### 页面顶部标题区域
- `●产品溯源.示例城市 或 示例品牌A`（根据公司自动识别）
- `scan.example.com`
- `正品保证.一物一码.全程可溯`
- `产品溯源信息`

### 页面中间产品信息区域
**布局方式**: 左右对齐，每行一个项目，垂直排列
- **左侧**: 标题（左对齐）
- **右侧**: 内容（右对齐）

**字段映射标准**:
- 公司名称：[从二维码文本第1字段解析]
- 公网网址：[从二维码文本第2字段解析]
- 产品名称：[从二维码文本第3字段解析]
- 产品规格：[从二维码文本第4字段解析]
- 产品特性：[从二维码文本第5字段解析]
- 产品颜色：[从二维码文本第6字段解析]
- 物流车牌：[从二维码文本第7字段解析]
- 业务员电话：[从二维码文本第8字段解析]
- 生产日期：[从二维码文本第9字段解析]
- 产品批次号：[从二维码文本第10字段解析]
- 出厂检验：[从二维码文本第11字段解析]
- 二维码序号：[从二维码文本第12字段解析]
- 发行者工号：[从二维码文本第13字段解析]
- 执行标准：[从二维码文本第14字段解析]
- 经销商名称：[从二维码文本第15字段解析]
- 备注：[从二维码文本第16字段解析]

### 页面底部功能区域
- `进入官网` 功能按钮
- 版权信息：
  - 示例公司：`C2025[已脱敏城市]示例品牌B材料有限公司.科技赋能.安全溯源`
  - 示例公司：`C2025[已脱敏城市]示例品牌A有限公司.安全溯源`

## 技术实现要求

### 响应式设计
- 自适应移动端硬件设备屏幕大小
- 单屏显示完整内容
- 优化触摸操作体验

### 样式规范
- UI背景颜色：智能选择
- 文字大小：智能适配
- 文字字体：智能选择
- 高亮显示：重要字段突出
- 标题左对齐，内容右对齐

### 公司识别规则
- 根据二维码内容自动识别公司类型
- 动态显示对应的公司名称和版权信息
- 智能匹配官网链接

---

# 固化：二维码 JSON 的 verification_url 统一规范与落地

目标：
- 历史与未来所有二维码 JSON（A-Q*.json、B-Q*.json）中的 "verification_url" 统一为：
  https://scan.example.com/index.html?code={二维码编号}

一、历史 JSON 批量修正（PowerShell 脚本）
- 脚本位置：scripts/qr/update_verification_url.ps1
- 作用范围：cloud/demo_json_a 与 cloud/demo_json_b
- 行为：将旧域名 https://your-company-domain.com/index.html?code=... 替换为 https://scan.example.com/index.html?code=...
- 使用示例：
  pwsh -File scripts/qr/update_verification_url.ps1
  # 试运行（不写入）：
  pwsh -File scripts/qr/update_verification_url.ps1 -DryRun

二、后续新发行 JSON 生成要求
- 生成逻辑必须写入：
  "verification_url": "https://scan.example.com/index.html?code={QR_SEQUENCE}"
- 如当前生成流程仍引用旧域名，应立即将生成模块中的 verification_url 写死为新域，或改为读取环境变量：
  VERIFY_URL_BASE=https://scan.example.com/index.html?code=
- 生成模块可参考以下伪代码：
  verification_url = f"{VERIFY_URL_BASE}{qr_sequence}"
- 若需兼容旧链路，可在入口做 301 跳转到新域的 /index.html?code={QR_SEQUENCE}。

三、验证与回滚
- 修正后抽样打开云目录 JSON，确认 "verification_url" 字段为新域。
- 脚本对每个变更文件会生成 .bak 备份；如需回滚，删除修改文件并将 .bak 改回原名即可。

说明：
- 本规范适用于 A 与 B 两条产线。
- 与 scan.example.com 的边缘解析逻辑配合，可实现移动端“无感秒开”。