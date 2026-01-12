# ERPNext 开发模式 vs 生产模式 - 完整差异说明

## 📋 概述

ERPNext（基于Frappe框架）确实有**开发模式（Developer Mode）**和**生产模式（Production Mode）**的区别。这两种模式针对不同的使用场景进行了优化。

---

## 🔧 开发模式（Developer Mode）

### 激活方式

在站点配置文件 `site_config.json` 中设置：

```json
{
    "developer_mode": 1
}
```

或通过Bench命令：

```bash
bench --site [site-name] set-config developer_mode 1
```

### 主要特性

| 特性 | 说明 |
|------|------|
| **DocType创建/修改** | ✅ 允许创建和修改DocType，定义新的数据结构 |
| **代码编辑** | ✅ 可以直接编辑Python和JavaScript代码 |
| **缓存机制** | ❌ 禁用或减少缓存，确保代码更改立即生效 |
| **错误显示** | ✅ 显示详细的错误堆栈跟踪，便于调试 |
| **后台任务** | ⚡ 异步任务立即执行（`now=True`），无需等待队列 |
| **性能优化** | ❌ 禁用部分性能优化，优先考虑开发便利性 |
| **安全性** | ⚠️ 降低安全限制，允许更多开发操作 |

### 适用场景

- ✅ 应用开发和定制
- ✅ 功能测试和调试
- ✅ 学习ERPNext框架
- ✅ 原型开发

### 注意事项

⚠️ **不建议在生产环境使用开发模式**，因为：
- 性能可能受影响
- 存在安全风险
- 可能暴露敏感信息

---

## 🚀 生产模式（Production Mode）

### 激活方式

默认模式，或明确设置：

```json
{
    "developer_mode": 0
}
```

或通过Bench命令：

```bash
bench --site [site-name] set-config developer_mode 0
```

### 主要特性

| 特性 | 说明 |
|------|------|
| **DocType创建/修改** | ❌ 限制创建新DocType，只能修改现有DocType |
| **代码编辑** | ❌ 代码修改需要通过版本控制和部署流程 |
| **缓存机制** | ✅ 启用完整的缓存机制，提升性能 |
| **错误显示** | ❌ 隐藏详细错误信息，只显示用户友好的错误消息 |
| **后台任务** | ⏳ 异步任务通过队列系统执行（RQ/Redis） |
| **性能优化** | ✅ 启用所有性能优化（压缩、合并、CDN等） |
| **安全性** | ✅ 严格的安全限制和权限控制 |
| **服务管理** | ✅ 使用Nginx和Supervisor管理进程 |

### 适用场景

- ✅ 生产环境部署
- ✅ 正式业务运行
- ✅ 高并发访问
- ✅ 数据安全和稳定性要求高的场景

---

## 📊 详细对比表

### 功能对比

| 功能项 | 开发模式 | 生产模式 |
|--------|---------|---------|
| **创建DocType** | ✅ 允许 | ❌ 限制 |
| **修改DocType** | ✅ 允许 | ⚠️ 有限制 |
| **编辑Python代码** | ✅ 直接编辑 | ❌ 需部署 |
| **编辑JavaScript** | ✅ 直接编辑 | ❌ 需构建 |
| **查看错误详情** | ✅ 完整堆栈 | ❌ 简化信息 |
| **缓存** | ❌ 禁用/减少 | ✅ 完整启用 |
| **代码热重载** | ✅ 支持 | ❌ 不支持 |
| **后台任务执行** | ⚡ 立即执行 | ⏳ 队列执行 |
| **性能优化** | ❌ 禁用 | ✅ 启用 |
| **调试工具** | ✅ 完整 | ❌ 受限 |

### 性能对比

| 性能指标 | 开发模式 | 生产模式 |
|---------|---------|---------|
| **页面加载速度** | 较慢（无缓存） | 快（有缓存） |
| **API响应时间** | 较慢 | 快 |
| **资源压缩** | ❌ 未压缩 | ✅ 压缩 |
| **静态资源合并** | ❌ 未合并 | ✅ 合并 |
| **数据库查询优化** | 基础优化 | 完整优化 |

### 安全对比

| 安全特性 | 开发模式 | 生产模式 |
|---------|---------|---------|
| **错误信息暴露** | ⚠️ 详细暴露 | ✅ 隐藏敏感信息 |
| **调试信息** | ⚠️ 显示 | ✅ 隐藏 |
| **代码访问** | ⚠️ 宽松 | ✅ 严格 |
| **权限验证** | ⚠️ 可绕过 | ✅ 严格执行 |
| **SQL注入防护** | ✅ 有 | ✅ 有 |
| **XSS防护** | ✅ 有 | ✅ 有 |

---

## 💻 代码中的使用示例

### 1. 后台任务执行方式

```python
# bank_statement_import.py
run_now = frappe.in_test or frappe.conf.developer_mode

frappe.enqueue(
    start_import,
    queue="default",
    timeout=6000,
    now=run_now,  # 开发模式立即执行，生产模式队列执行
)
```

### 2. 条件性功能启用

```python
# financial_report_template.py
if not self.module or not frappe.conf.developer_mode:
    return  # 生产模式下禁用某些功能

# 开发模式下允许删除模板
def _delete_template(self):
    if not frappe.conf.developer_mode:
        return
    # ... 删除逻辑
```

### 3. 调试信息显示

```python
# call_log.py
if frappe.conf.developer_mode:
    self.add_comment(
        text=f"调试信息: {debug_data}"
    )
```

---

## 🔄 模式切换

### 从开发模式切换到生产模式

```bash
# 1. 禁用开发模式
bench --site [site-name] set-config developer_mode 0

# 2. 清理缓存
bench --site [site-name] clear-cache

# 3. 重建静态资源
bench build

# 4. 重启服务
bench restart
```

### 从生产模式切换到开发模式

```bash
# 1. 启用开发模式
bench --site [site-name] set-config developer_mode 1

# 2. 清理缓存
bench --site [site-name] clear-cache

# 3. 重启服务
bench restart
```

---

## 📝 配置文件位置

### site_config.json

位置：`sites/[site-name]/site_config.json`

```json
{
    "db_name": "erpnext_db",
    "db_password": "password",
    "developer_mode": 1,  // 0 = 生产模式, 1 = 开发模式
    "encryption_key": "...",
    "host_name": "erpnext.example.com"
}
```

---

## ⚙️ 生产环境最佳实践

### 1. 部署配置

```bash
# 确保开发模式已禁用
bench --site [site-name] set-config developer_mode 0

# 启用生产优化
bench --site [site-name] set-config serve_default_site 1
bench --site [site-name] set-config auto_reload 0
```

### 2. 使用Nginx和Supervisor

```ini
# supervisor配置示例
[program:frappe-bench-web]
command=/path/to/bench serve --port 8000
directory=/path/to/bench
user=frappe
autostart=true
autorestart=true
```

### 3. 性能优化

```bash
# 构建生产资源
bench build --production

# 启用压缩
bench --site [site-name] set-config compress_response 1

# 启用静态资源缓存
bench --site [site-name] set-config static_file_cache 1
```

---

## 🎯 关键差异总结

### 开发模式的核心特点

1. **灵活性优先**：允许快速开发和测试
2. **即时反馈**：代码更改立即生效
3. **详细调试**：完整的错误信息和堆栈跟踪
4. **开发工具**：支持DocType创建、代码编辑等

### 生产模式的核心特点

1. **稳定性优先**：确保系统可靠运行
2. **性能优化**：启用所有缓存和优化
3. **安全保护**：隐藏敏感信息，严格权限控制
4. **标准化部署**：通过版本控制和CI/CD流程

---

## ⚠️ 重要提醒

1. **永远不要在生产环境启用开发模式**
   - 安全风险：可能暴露系统内部信息
   - 性能影响：缓存禁用会导致性能下降
   - 稳定性：允许的修改可能影响系统稳定性

2. **开发完成后务必切换回生产模式**
   - 清理开发时的临时配置
   - 验证生产模式下的功能正常
   - 进行性能测试

3. **使用版本控制管理代码变更**
   - 开发模式的代码修改应通过Git管理
   - 生产环境通过部署流程更新代码
   - 避免直接在生产环境修改代码

---

## 📚 相关文档

- [Frappe Framework 开发模式文档](https://docs.frappe.io/framework/user/en/guides/app-development/how-enable-developer-mode-in-frappe)
- [ERPNext 部署指南](https://docs.erpnext.com/docs/user/manual/en/setting-up/installation)
- [Bench 命令参考](https://frappeframework.com/docs/user/en/bench)

---

**文档版本**：v1.0  
**创建日期**：2026-01-10  
**适用版本**：ERPNext v14+
