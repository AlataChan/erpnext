# 德川/裕霖业务管理系统 - V2.0 完整开发计划
# Dechuan/Yulin BMS Total Development Plan (V2.0)

> **基于:** ERPNext 深度适配性分析报告 V2.0 & AI Agent 增强方案  
> **核心战略:** "ERPNext 核心数据架构" + "AI Agent 智能增强" 双轮驱动  
> **实施周期:** 5-6 个月 (18-20 周)  
> **总开发人天估算:** 105-145 人天 (含 AI 部分)

---

## 1. 核心架构重构 (The Core Shift)

在 V2.0 计划中，我们彻底放弃 "以 Item 为核心" 的标准 ERPNext 模式，转向 "以 Mold Project 为核心" 的 ETO (Engineer-to-Order) 模式。

### 1.1 核心数据模型
*   **MOLD PROJECT (模具项目)**: 系统的绝对核心 DocType。所有业务（报价、设计、采购、生产、质检、财务）都必须通过 Link 字段关联到此对象。
*   **Drawing System (图纸子系统)**: 独立于 ERPNext 原生文档系统的图纸版本管理与分发系统。
*   **Cost Ledger (成本账本)**: 独立于 Item Valuation 的项目级成本归集中心。

### 1.2 AI Agent 集成策略
AI Agent 不是外挂插件，而是深度嵌入到低匹配度模块（工程、质量）的工作流中，解决"难录入"和"难查询"的问题。

---

## 2. 实施路线图 (Master Roadmap)

### Phase 1: 核心架构与主流程打通 (Week 1-4)
**目标**: 完成 "从报价到立项" 的核心数据链路，确立 Mold Project 的核心地位。

*   **W1: 环境与基础设施**
    *   搭建开发环境 (Bench, Redis, MariaDB)
    *   配置 AI Agent 基础环境 (OpenAI/Claude Key, 企业微信对接)
    *   初始化 `dechuan` app 结构
*   **W2: 核心 DocType 开发 (P0)**
    *   开发 `Mold Project`：定义字段、状态机、命名规则 `DC{YYYY}{XXX}`
    *   数据迁移脚本：导入历史客户、供应商数据
    *   **[AI]** 进度查询 Agent (MVP版)：实现通过模具号查询基本状态
*   **W3: 销售与立项自动化**
    *   配置 `Quotation` -> `Sales Order` 流程
    *   开发 Hook：Sales Order 提交 -> 自动创建/关联 Mold Project
    *   扩展 Customer：添加对账习惯、公司主体字段
*   **W4: 采购流程适配**
    *   扩展 Purchase Order/Receipt：强制关联 Mold Project
    *   **[P0]** 成本归集逻辑验证：采购入库 -> 自定义成本账本

### Phase 2: 工程管理子系统 (Week 5-8)
**目标**: 解决最痛的 "设计-确认" 环节，引入 AI 辅助图纸处理。

*   **W5: 图纸管理基础**
    *   开发 `Preparation Drawing` (备料图) & `Formal Drawing` (正式图)
    *   实现自定义版本控制逻辑 (非 ERPNext 原生 Versioning)
*   **W6: 三方确认工作流**
    *   开发 `Drawing Confirmation`：实现 工程->生产->业务 串行审批流
    *   **[AI]** 确认催办 Agent：监控审批停留时间，超时自动推送到企业微信
*   **W7: 客户对接与参数**
    *   **[AI]** 客户参数对接 Agent：从聊天记录提取参数 -> 生成确认单
*   **W8: 工程模块集成测试**
    *   验证：图纸上传 -> 内部确认 -> 客户确认 -> 状态回写 Mold Project

### Phase 3: 生产与质量智能增强 (Week 9-13)
**目标**: 适配单件生产模式，利用 AI 解决质量检测难题。

*   **W9: 生产计划适配**
    *   配置 Work Order (Qty=1 模式)
    *   开发 `Weekly Plan` (周计划) DocType 及打印格式
*   **W10: 生产执行与反馈**
    *   配置 Job Card (工序任务)
    *   **[AI]** 经验提醒 Agent：派工时自动推送历史同类模具的工艺注意事项
*   **W11: 试模报告与质量**
    *   开发 `Trial Report`：完全自定义的试模报告（含多组参数）
    *   **[AI]** 语音数据采集 Agent：车间嘈杂环境下语音录入试模参数
*   **W12: 视觉检测 (POC)**
    *   **[AI]** 视觉质量检测 Agent：上传产品图片 -> 识别表面缺陷 (裂纹/气泡)
*   **W13: 生产质量集成测试**

### Phase 4: 财务闭环与报表 (Week 14-17)
**目标**: 实现"模具维度"的成本利润分析，解决对账痛点。

*   **W14: 对账管理**
    *   开发 `Reconciliation` (对账单) DocType：汇总 Delivery Notes
    *   **[AI]** 收款提醒 Agent：计算账龄，多级自动催收
*   **W15: 成本核算中心**
    *   开发 `Mold Cost Sheet` 报表：汇总 材料 + 工时 + 费用
    *   开发利润分析 Dashboard：按模具、客户、业务员多维度分析
*   **W16: 双主体报表**
    *   定制 Sales/Purchase 报表：支持按 "德川/裕霖" 字段筛选隔离
*   **W17: 财务集成测试 (UAT)**

### Phase 5: 上线与优化 (Week 18-20)
*   **W18: 全链路压力测试 & AI 调优**
*   **W19: 用户培训 & 数据导入**
*   **W20: 正式割接上线**

---

## 3. 详细任务清单 (按角色)

### 3.1 后端开发 (Python/Frappe)
- [x] **Data Model**: Mold Project, Drawing, Trial Report, Reconciliation 等 10+ 个 DocType 定义
- [x] **Logic**: 
    - 自动编号逻辑 (DC/YL前缀)
    - 状态机流转 (Status Transitions)
    - 成本归集计算脚本 (Cost Aggregation Script)
- [x] **API**: 为 AI Agent 提供标准 REST API 接口 (GET status, POST confirmation)

### 3.2 AI 工程师 (Python/LangChain)
- [x] **Agent 1 (Query)**: 基于特定意图识别 (Intent Recognition) 的查询机器人
- [ ] **Agent 2 (OCR/Extraction)**: 图纸/参数提取 Prompt Engineering (待实现)
- [ ] **Agent 3 (Vision)**: 基于通义千问VL/GPT-4V 的缺陷检测流程 (待实现)
- [x] **Integration**: 封装为 ERPNext App 内部模块

### 3.3 前端/报表 (JS/Vue)
- [ ] **Views**: 看板视图 (Kanban) 定制，方便查看模具流转 (待实现)
- [x] **Reports**: 复杂的成本利润交叉报表 (Script Report)
- [x] **Print Formats**: 对账单高保真打印模板

---

## 4. 关键风险与对策 (Risk Mitigation)

| 风险点 | 概率 | 影响 | 缓解对策 |
|--------|------|------|----------|
| **成本归集数据不准** | 高 | 严重 | 在 Phase 1 就验证成本逻辑；强制采购单关联模具号 |
| **AI 识别率不达标** | 中 | 中 | 提供"人工修正"界面；AI 仅作为辅助建议，不作为最终通过标准 |
| **三方确认流程卡顿** | 高 | 中 | 实施初期允许"后补确认"或"代理确认"，配合催办 Agent |
| **图纸版本混乱** | 中 | 严重 | 严格锁定已确认版本的修改权限；强制新版本升级流程 |

---

## 5. 资源预算 (Resource Estimation)

*   **人力投入**: 
    *   ERP 开发: 2人 × 4个月
    *   AI 开发: 1人 × 2个月
    *   项目经理/BA: 1人 × 3个月 (兼职)
*   **云资源**:
    *   应用服务器: 4核 8G (生产环境)
    *   AI API 费用: 预估 $200-$500/月 (取决于视觉检测调用量)

---

**批准签字:** ____________________  **日期:** ____________________
