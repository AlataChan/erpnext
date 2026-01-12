# 德川/裕霖业务管理系统 - 数据库 ER 图

本图描述了系统核心实体及其关系，特别是自定义新增的业务对象与 ERPNext 原生对象的关联。

```mermaid
erDiagram

    %% --- 核心：模具项目 ---
    MOLD_PROJECT {
        string name PK "模具编号 (DC2025001)"
        string project_name "项目名称"
        string flow_status "状态 (立项/设计/生产...)"
        string company_entity "主体 (德川/裕霖)"
        date planned_delivery "计划交期"
        int cavitiex "穴数"
    }

    CUSTOMER ||--o{ MOLD_PROJECT : "委托"
    COMPANY ||--o{ MOLD_PROJECT : "承接"

    %% --- 关联：原生单据 ---
    SALES_ORDER ||--o{ MOLD_PROJECT : "生成"
    QUOTATION ||--o{ MOLD_PROJECT : "前期报价"
    
    %% --- 扩展：工程管理 ---
    PREPARATION_DRAWING {
        string name PK
        string version "版本号"
        string file_url "图纸文件"
    }

    FORMAL_DRAWING {
        string name PK
        string version "版本号"
    }

    DRAWING_CONFIRMATION {
        string name PK
        string status "状态"
        datetime eng_confirm_time
        datetime prod_confirm_time
        string customer_feedback
    }

    MOLD_PROJECT ||--o{ PREPARATION_DRAWING : "包含"
    MOLD_PROJECT ||--o{ FORMAL_DRAWING : "包含"
    MOLD_PROJECT ||--o{ DRAWING_CONFIRMATION : "流程控制"
    PREPARATION_DRAWING ||--o{ FORMAL_DRAWING : "依据"

    %% --- 扩展：生产与质量 ---
    TRIAL_REPORT {
        string name PK
        int trial_count "试模次数"
        string result_visual "外观判定"
        string result_dims "尺寸判定"
        string final_verdict "综合判定"
    }

    WEEKLY_PLAN {
        string name PK
        string week_num "周次"
    }

    WEEKLY_PLAN_ITEM {
        string task_desc
        date start_date
        date end_date
    }

    MOLD_PROJECT ||--o{ TRIAL_REPORT : "质检"
    MOLD_PROJECT ||--o{ WEEKLY_PLAN_ITEM : "生产任务"
    WEEKLY_PLAN ||--|{ WEEKLY_PLAN_ITEM : "包含"
    USER ||--o{ WEEKLY_PLAN_ITEM : "负责"

    %% --- 扩展：财务 ---
    RECONCILIATION {
        string name PK
        string period "对账周期"
        float total_amount "总金额"
        string status "对账状态"
    }

    DELIVERY_NOTE }|--|| RECONCILIATION : "汇总"
    MOLD_PROJECT ||--o{ RECONCILIATION : "结算"
    RECONCILIATION ||--o{ COLLECTION_PLAN : "生成计划"

    %% --- 关联：采购成本 ---
    PURCHASE_ORDER_ITEM {
        string item_code
        float amount
    }
    
    MOLD_PROJECT ||--o{ PURCHASE_ORDER_ITEM : "成本归集(自定义字段)"
```

## 说明

1.  **MOLD_PROJECT (模具项目)** 是全系统的核心枢纽，几乎所有业务单据都通过外键（`Link` 字段）与其关联。
2.  **工程管理** 采用 `Drawing` -> `Confirmation` 的分离设计，版本文件与确认流程解耦，支持多次确认。
3.  **成本归集** 并不创建独立的成本表，而是通过在 `Purchase Order Item` (原生) 上添加 `mold_project` 字段来实现动态汇总。
4.  **对账管理** `Reconciliation` 是一个新的实体，用于在 `Delivery Note` (原生送货单) 和 `Payment Entry` (原生收款) 之间建立一个确认层。
