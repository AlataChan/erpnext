# 德川/裕霖 BMS - 用户验收测试清单 (UAT Checklist)
# Version 1.0 | 2026-01-15

---

## 1. 模具项目管理 (Mold Project Management)

### 1.1 核心流程
- [ ] **创建模具项目**
  - [ ] 手动创建 Mold Project，验证自动编号 (DC2026XXX / YL2026XXX)
  - [ ] 选择德川/裕霖主体，确认编号前缀正确
  - [ ] 填写客户、项目名称、计划交期

- [ ] **销售订单联动**
  - [ ] 创建 Sales Order 并提交
  - [ ] 验证自动创建关联的 Mold Project
  - [ ] 检查 Mold Project 的 sales_order 字段已回填

- [ ] **Dashboard 关联显示**
  - [ ] 进入 Mold Project，查看 Dashboard 链接
  - [ ] 确认可快速跳转到关联的采购单、图纸、试模报告

### 1.2 状态流转
- [ ] 手动更新状态：立项 → 设计 → 采购 → 生产 → 质检 → 出货 → 完成
- [ ] 验证状态变更被正确保存

---

## 2. 工程管理 (Engineering)

### 2.1 图纸管理
- [ ] **备料图 (Preparation Drawing)**
  - [ ] 创建备料图，上传附件
  - [ ] 验证自动编号格式

- [ ] **正式图 (Formal Drawing)**
  - [ ] 创建正式图 V1 版本
  - [ ] 创建 V2 版本，勾选"当前生效版本"
  - [ ] 验证 V1 的"当前生效"自动取消

### 2.2 图纸确认流程
- [ ] **创建 Drawing Confirmation**
  - [ ] 关联 Mold Project
  - [ ] 初始状态为"待工程确认"

- [ ] **四方确认流程**
  - [ ] 调用 `confirm_engineering()` → 状态变为"待生产确认"
  - [ ] 调用 `confirm_production()` → 状态变为"待业务确认"
  - [ ] 调用 `confirm_sales()` → 状态变为"待客户确认"
  - [ ] 调用 `confirm_customer()` → 状态变为"已确认"
  - [ ] 验证 Mold Project 的 drawing_status 更新为"已确认"

- [ ] **催办提醒**
  - [ ] 创建一条 Drawing Confirmation，保持 24+ 小时不确认
  - [ ] 手动触发 `run_confirmation_reminder()`
  - [ ] 验证 ToDo 已创建给相关用户

---

## 3. 采购与成本 (Procurement & Costing)

### 3.1 采购流程
- [ ] **创建 Purchase Order**
  - [ ] 选择关联的 Mold Project
  - [ ] 提交 PO

- [ ] **采购入库**
  - [ ] 从 PO 创建 Purchase Receipt
  - [ ] 验证 mold_project 字段自动继承
  - [ ] 提交 PR

### 3.2 成本归集
- [ ] **验证 Mold Cost Ledger**
  - [ ] 提交 PR 后，检查是否自动创建 Mold Cost Ledger 条目
  - [ ] 验证 cost_type = "Material"
  - [ ] 验证金额正确

- [ ] **多次采购**
  - [ ] 为同一个 Mold Project 创建多个 PR
  - [ ] 验证成本累加正确

---

## 4. 生产与质量 (Production & Quality)

### 4.1 周计划
- [ ] **创建 Weekly Plan**
  - [ ] 添加多个任务项 (Weekly Plan Item)
  - [ ] 分配给不同人员
  - [ ] 保存，验证合计工时自动计算

- [ ] **发布计划**
  - [ ] 调用 `publish_plan()`
  - [ ] 验证所有被分配人员收到 ToDo

### 4.2 试模报告
- [ ] **创建 Trial Report**
  - [ ] 关联 Mold Project
  - [ ] 添加多个参数项 (Trial Parameter Item)
  - [ ] 填写外观/尺寸/功能检查结果

- [ ] **判定验证**
  - [ ] 尝试选择"出货"但综合判定为"不合格" → 应报错
  - [ ] 综合判定"合格"，选择"出货" → 应成功

---

## 5. 财务模块 (Finance)

### 5.1 对账单
- [ ] **创建 Reconciliation**
  - [ ] 选择客户和日期范围
  - [ ] 调用 `fetch_delivery_notes()` 自动拉取送货单
  - [ ] 验证合计数量和金额正确

- [ ] **打印对账单**
  - [ ] 使用 "Reconciliation Statement" 打印格式
  - [ ] 验证 PDF 内容完整、格式正确

- [ ] **确认流程**
  - [ ] 调用 `mark_confirmed()`
  - [ ] 验证状态变为 "Confirmed"

### 5.2 收款提醒
- [ ] **创建逾期发票**
  - [ ] 创建并提交 Sales Invoice
  - [ ] 设置 due_date 为 30+ 天前
  - [ ] 手动触发 `run_collection_reminder()`
  - [ ] 验证 ToDo 已创建

---

## 6. 报表 (Reports)

### 6.1 模具成本表
- [ ] 打开 **Mold Cost Sheet** 报表
- [ ] 设置筛选条件（客户、日期）
- [ ] 验证数据正确显示
- [ ] 验证图表和汇总数据

### 6.2 利润分析
- [ ] 打开 **Mold Profit Analysis** 报表
- [ ] 切换分组维度（按客户/公司主体/月份）
- [ ] 验证数据重新计算

---

## 7. AI Agents

### 7.1 进度查询
- [ ] 调用 `query_mold_progress('模具编号')`
- [ ] 验证返回项目状态信息

### 7.2 经验提取
- [ ] 调用 `get_similar_mold_experience('模具项目名')`
- [ ] 验证返回历史相关记录

---

## 8. 系统配置

### 8.1 Dechuan Settings
- [ ] 访问 Dechuan Settings
- [ ] 修改默认公司主体
- [ ] 配置确认超时时间
- [ ] (可选) 配置企业微信参数

---

## 9. 数据迁移验证

### 9.1 历史数据导入
- [ ] 准备客户 CSV 文件
- [ ] 执行 `import_customers()` 脚本
- [ ] 验证数据正确导入

### 9.2 数据完整性检查
- [ ] 执行 `validate_data_integrity()`
- [ ] 确认无报错或仅有可接受的警告

---

## 签署确认

| 角色 | 姓名 | 日期 | 签名 |
|------|------|------|------|
| 项目经理 | | | |
| 业务代表 | | | |
| IT 负责人 | | | |

---

**备注:**
- 所有测试项应在测试环境完成
- 重大问题需记录并修复后重新测试
- UAT 通过后方可进入数据迁移和正式上线阶段
