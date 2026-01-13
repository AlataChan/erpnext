# 开发环境搭建指南

本指南将指导您在本地机器（macOS/Linux）上搭建用于 ERPNext 二次开发的 Frappe 环境。

## 1. 前置条件

确保您的系统安装了以下基础工具：
- **Python** (3.10 或 3.11)
- **Node.js** (v18 或 v20)
- **MariaDB** (10.6+)
- **Redis**
- **Git**
- **VS Code** (推荐编辑器)

### macOS 快速安装依赖 (使用 Homebrew)
```bash
brew install git python@3.10 node mariadb redis
brew install wkhtmltopdf  # 用于生成PDF
```

## 2. 此 Fork 项目的开发环境

假设您已经 Fork 并 Clone 了代码库到本地，例如 `/Users/yourname/erpnext`。

### 2.1 安装 Frappe Bench CLI
```bash
pip3 install frappe-bench
```

### 2.2 初始化 Bench
在您希望存放项目的目录下初始化 bench：
```bash
bench init frappe-bench --frappe-branch version-16 --python python3.10
cd frappe-bench
```

### 2.3 挂载本次开发的 ERPNext 应用
将您 Clone 下来的 ERPNext 目录安装到 bench 的 `apps` 目录中：

```bash
# 这一步将现有的本地目录链接过去，方便开发
bench get-app erpnext /path/to/your/erpnext --resolve-deps
```

*注意：如果遇到权限问题，请确保您的当前用户对 bench 目录有完全的读写权限。*

### 2.4 创建开发站点
```bash
# 创建一个新站点，数据库名会自动生成
bench new-site dechuan.localhost

# 将 ERPNext 安装到该站点
bench --site dechuan.localhost install-app erpnext
```

### 2.5 启动开发服务器
```bash
bench start
```
访问 `http://dechuan.localhost:8000` (需要修改 /etc/hosts 将 dechuan.localhost 指向 127.0.0.1，或者直接访问 localhost:8000)

---

## 3. 德川定制模块开发

本项目建议采用了模块化的开发方式。虽然您可以直接修改 `erpnext` 应用，但最佳实践是创建一个独立的应用（App）或在 `erpnext` 内创建独立的模块包。

本指南中，我们在 `erpnext` 目录下建立了 `dechuan` 子目录来存放自定义逻辑。

### 3.1 目录结构
```
erpnext/
  erpnext/
    dechuan/
      mold_management/
      engineering/
      ...
```

### 3.2 启用开发模式
在 `bench start` 运行的状态下，前端资源会自动编译。
对于 Python 代码的修改，Bench 会自动检测重启（Debug模式下）。

请在 `site_config.json` 中配置：
```json
{
 "developer_mode": 1
}
```

## 4. AI Agent 开发环境配置 (V2.0 新增)
由于 V2.0 架构深度集成了 AI Agent，您需要额外配置以下环境变量及工具。

### 4.1 配置文件
在 `site_config.json` 中添加 AI 服务所需的密钥（请勿提交到 Git）：
```json
{
 "developer_mode": 1,
 "ai_agent_config": {
  "openai_api_key": "sk-...",
  "claude_api_key": "sk-ant-...",
  "wechat_corp_id": "ww...",
  "wechat_corp_secret": "..."
 }
}
```

### 4.2 Python 依赖
AI Agent 模块可能需要额外的 Python 库，请并在 `pyproject.toml` 或 `requirements.txt` 中声明，并安装：
```bash
./env/bin/pip install langchain openai pdfplumber wechatpy
```

## 5. 常用命令速查

| 想要做什么 | 命令 |
|------------|------|
| 启动服务 | `bench start` |
| 重启 Python 进程 | `bench restart` |
| 更新数据库结构 | `bench --site [sitename] migrate` |
| 导出 DocType 修改 | `bench --site [sitename] export-fixtures` |
| 创建新网站 | `bench new-site [sitename]` |
| 运行 Python Shell | `bench --site [sitename] console` |

## 5. 调试技巧

### VS Code 配置
在 `.vscode/launch.json` 中添加配置以支持 Python Debugger 附加到 Bench 进程。

### 查看日志
- `bench start` 终端窗口会实时显示 web, worker, schedule 的日志。
- 详细日志在 `frappe-bench/logs/` 目录下。

---

> **注意：** 提交代码前，请务必运行 `pre-commit` 检查代码规范。
