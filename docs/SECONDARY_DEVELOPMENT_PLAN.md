# 德川/裕霖业务管理系统 - 二次开发实施计划

## 1. 项目概述

本项目旨在对 ERPNext 进行深度二次开发，以适配德川/裕霖模具制造企业的核心业务流程。项目以“模具项目”为核心，打通从客户询价、工程设计、采购生产到财务核算的全链条。

**核心目标：**
*   建立以模具为核心的项目管理体系
*   实现工程图纸的三方确认流程
*   打通采购、工时的成本归集
*   利用 AI Agent 解决进度查询和催办痛点

---

## 2. 开发路线图 (Roadmap)

### Phase 0: 准备阶段 (Week 1-2)
*   **W1**: 开发环境搭建，Fork项目代码，配置CI/CD。
*   **W2**: 需求细节确认，数据库设计评审，创建应用骨架。

### Phase 1: 核心业务破局 (Week 3-6)
*   **W3**: **[P0]** 开发 `Mold Project` (模具项目) 核心 DocType，实现模具编号自动生成规则 `DC/YL{YYYY}{XXX}`。
*   **W4**: **[P0]** 打通 `Quotation` -> `Sales Order` -> `Mold Project` 的自动化立项流程。
*   **W5**: **[P0]** 开发工程管理基础：`Preparation Drawing` (备料图) 和 `Formal Drawing` (正式图)。
*   **W6**: **[P0]** 实现图纸确认流程 `Drawing Confirmation` (三方确认 + 客户确认)。

### Phase 2: 生产与成本 (Week 7-10)
*   **W7**: **[P1]** 采购流程适配：`Purchase Order` 关联 `Mold Project`，实现材料成本自动归集。
*   **W8**: **[P1]** 开发 `Weekly Plan` (周计划) 及任务分配逻辑。
*   **W9**: **[P1]** 开发 `Trial Report` (试模报告) 及质量判定逻辑。
*   **W10**: **[P1]** 开发 `Mold Cost Entry`，汇总材料、人工、制造费用，输出初步成本报表。

### Phase 3: 财务与AI增强 (Week 11-14)
*   **W11**: **[P1]** 开发 `Reconciliation` (对账单) 管理，适配客户对账习惯。
*   **W12**: **[P2]** 开发 `Collection Plan` (收款计划) 及超期预警逻辑。
*   **W13**: **[P2]** **AI Agent 1&2**: 进度查询 Agent (企业微信集成) + 确认催办 Agent (定时任务)。
*   **W14**: **[P2]** **AI Agent 3&4**: 经验提醒 Agent + 收款提醒 Agent。

### Phase 4: 交付与稳定 (Week 15-16)
*   **W15**: 全流程集成测试 (UAT)，修复Bug，性能优化。
*   **W16**: 数据迁移，用户培训，正式上线。

---

## 3. 详细任务分解

### 3.1 基础架构与配置
- [ ] 初始化 `dechuan` 模块/App
- [ ] 配置 `hooks.py` 挂载点
- [ ] 扩展 `Customer` 字段：`reconciliation_habit` (对账习惯), `company_entity` (默认主体)
- [ ] 扩展 `Company` 字段：支持双主体逻辑 (或通过自定义字段隔离)

### 3.2 模具管理模块 (Mold Management)
- [ ] **Mold Project**
    - [ ] 定义字段：基本信息、技术参数、状态流、关联单据
    - [ ] 编写 `autoname` 逻辑：`format:{company_code}{YYYY}{###}`
    - [ ] 编写 Dashboard：显示关联的订单、采购、图纸、试模记录
- [ ] **关联逻辑**
    - [ ] 销售订单提交 -> 自动创建 Mold Project

### 3.3 工程管理模块 (Engineering)
- [ ] **Preparation Drawing (备料图)**
    - [ ] 文件上传字段
    - [ ] 提取BOM逻辑 (可选：解析Excel BOM)
- [ ] **Formal Drawing (正式图)**
    - [ ] 版本控制逻辑
- [ ] **Drawing Confirmation (图纸确认)**
    - [ ] 工作流状态：工程确认 -> 生产确认 -> 业务确认 -> 客户确认
    - [ ] 钉钉/企微消息通知集成

### 3.4 生产与质量 (Production & Quality)
- [ ] **Weekly Plan (周计划)**
    - [ ] 汇总本周所有进行中模具的工序任务
    - [ ] 任务分配给具体人员
- [ ] **Trial Report (试模报告)**
    - [ ] 试模参数子表 (参数名, 标准值, 实测值, 判定)
    - [ ] 综合判定与处置建议 (出货/返工/报废)

### 3.5 财务模块 (Finance)
- [ ] **Reconciliation (对账单)**
    - [ ] 选取客户和日期范围 -> 自动拉取未对账送货单
    - [ ] 生成对账PDF模板
- [ ] **Mold Cost Sheet**
    - [ ] 报表开发：按模具汇总采购成本、工时成本

### 3.6 AI Agents (Python & Integration)
- [ ] **Progress Agent**: API端点开发，接收自然语言查询，返回模具状态摘要
- [ ] **Reminder Agent**: Scheduler开发，每日扫描超时任务，发送提醒
- [ ] **Experience Agent**: 匹配相似模具，提取历史问题
- [ ] **Collection Agent**: 扫描应收账款，计算账龄，触发提醒

---

## 4. 资源需求

*   **人力**:
    *   后端开发 (Python/Frappe): 1人 (核心)
    *   前端/全栈 (JS/Vue): 0.5人 (AI Agent、大屏展示)
    *   业务分析/PM: 0.5人 (需求确认、验收)
*   **环境**:
    *   开发环境: MacOS/Linux + VS Code
    *   服务器: Ubuntu 22.04 LTS (推荐)
    *   数据库: MariaDB 10.6+

## 5. 风险管理

| 风险点 | 影响 | 应对措施 |
|--------|------|----------|
| 模具编号逻辑与旧数据冲突 | 高 | 上线前进行彻底的数据清洗和迁移测试，预留编号段 |
| 三方确认流程过于繁琐 | 中 | 初期允许"代确认"或"批量确认"，逐步规范化 |
| 成本归集不准确 | 高 | 必须严格要求采购订单关联模具，定期审计未关联单据 |
