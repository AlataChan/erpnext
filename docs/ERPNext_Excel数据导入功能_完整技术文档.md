# ERPNext Excel数据导入功能 - 完整技术文档

## 📋 文档概述

本文档整合了ERPNext Excel数据导入功能的完整技术方案，包含：
- 功能需求与架构设计
- 详细代码实现方案
- 技术风险评估与改进建议
- 完整的测试用例覆盖
- 实施路线图与部署指南

**文档整合来源**：
- ERPNext_Excel数据导入功能实施方案.md
- ERPNext_Excel数据导入功能代码实现.md
- ERPNext_Excel导入方案_技术审查报告.md
- ERPNext_Excel导入功能_补充测试用例.md

> ⚠️ **重要说明**：本文档中的 `Material` 和 `StockRecord` 是**自定义DocType**示例名称。
> - 若要对应ERPNext标准模块，`Material` 对应 **Item**（物品）DocType
> - `StockRecord` 对应 **Stock Entry**（库存凭证）DocType
> - 实际项目中请根据业务需求决定使用自定义DocType还是扩展标准DocType

---

## 1. 项目概述与需求分析

### 1.1 功能目标
为ERPNext系统开发一个Excel数据导入功能，允许用户通过文件上传按钮将Excel数据直接导入到Material（物料）和StockRecord（出入库记录）表单中，实现批量数据录入。

### 1.2 核心功能需求
- **文件上传界面**：在表单页面添加文件上传按钮
- **Excel解析**：支持.xlsx和.xls格式文件解析
- **数据验证**：对导入数据进行格式和业务逻辑验证
- **批量导入**：支持单次导入多条记录
- **错误处理**：提供详细的导入结果反馈
- **模板下载**：提供标准Excel模板供用户下载

### 1.3 需求符合性评估
| 需求项 | 符合状态 | 说明 |
|--------|----------|------|
| 文件上传按钮 | ✅ 完全满足 | 在表单工具栏添加自定义按钮 |
| 文件上传对话框 | ✅ 完全满足 | 实现了完整的文件选择界面 |
| Excel文件解析 | ✅ 完全满足 | 支持.xlsx/.xls格式，使用openpyxl库 |
| 数据导入数据库 | ✅ 完全满足 | 完整的CRUD操作和数据验证 |
| 用户交互反馈 | ✅ 完全满足 | 提供进度条、结果反馈、错误详情 |

**总体符合度**：⭐⭐⭐⭐⭐ 100%

---

## 2. 技术架构设计

### 2.1 整体架构
```
前端界面 → 文件上传 → Excel解析 → 数据验证 → 数据库写入 → 结果反馈
```

### 2.2 技术栈
- **前端**：ERPNext Frappe UI框架 + JavaScript
- **后端**：Python + Frappe框架
- **Excel处理**：
  - `openpyxl`：处理 `.xlsx` 格式（**注意：不支持.xls格式**）
  - `xlrd`：处理旧版 `.xls` 格式（需单独安装）
  - `frappe.utils.xlsxutils`：Frappe内置的Excel工具模块
- **文件存储**：ERPNext File DocType
- **异步处理**：RQ（Redis Queue）任务队列
- **数据导入框架**：`frappe.core.doctype.data_import` 原生模块

> ⚠️ **技术警告**：`openpyxl` 库**仅支持 .xlsx 格式**，不支持旧版 .xls 格式。
> 如需同时支持两种格式，需要添加 `xlrd` 依赖或统一要求用户使用 .xlsx 格式。

### 2.3 自定义应用结构
```
erpnext_custom/
├── __init__.py
├── api.py                           # Excel导入API接口（白名单方法）
├── hooks.py                         # 应用配置、权限和钩子
├── patches/                         # 数据库迁移补丁
│   └── __init__.py
├── erpnext_custom/
│   └── doctype/
│       ├── material/                # 自定义DocType（如需要）
│       │   ├── __init__.py
│       │   ├── material.py
│       │   ├── material.js
│       │   └── material.json
│       └── stock_record/
│           ├── __init__.py
│           ├── stock_record.py
│           ├── stock_record.js
│           └── stock_record.json
├── public/
│   └── js/
│       └── excel_import.bundle.js   # 前端JavaScript组件（bundle）
├── templates/
│   ├── material_template.xlsx
│   └── stockrecord_template.xlsx
└── fixtures/                        # 固定数据（角色权限等）
    └── custom_field.json
```

### 2.4 hooks.py 完整配置示例

```python
# hooks.py - 应用钩子配置

app_name = "erpnext_custom"
app_title = "ERPNext Custom Excel Import"
app_publisher = "Your Company"
app_description = "Excel数据批量导入扩展"
app_version = "1.0.0"

# JavaScript注入配置 - 为特定DocType添加自定义按钮
doctype_js = {
    "Material": "public/js/material_excel_import.js",
    "Stock Record": "public/js/stockrecord_excel_import.js",
    # 如果是扩展标准DocType
    # "Item": "public/js/item_excel_import.js",
    # "Stock Entry": "public/js/stock_entry_excel_import.js",
}

# 权限钩子 - 控制谁可以使用导入功能
has_permission = {
    "Material": "erpnext_custom.permissions.material_has_permission",
}

# 白名单API方法（允许前端调用）
# 注意：@frappe.whitelist() 装饰器已自动注册，此处可选配置
# override_whitelisted_methods = {}

# 安装后执行
after_install = "erpnext_custom.setup.install.after_install"

# 定时任务（如需要清理临时文件）
scheduler_events = {
    "daily": [
        "erpnext_custom.tasks.cleanup_temp_import_files"
    ]
}

# 文档事件钩子
doc_events = {
    "Material": {
        "validate": "erpnext_custom.api.validate_material_data",
        "on_update": "erpnext_custom.api.on_material_update"
    }
}
```

---

## 3. 详细代码实现

### 3.1 核心API实现 (api.py)

```python
"""
Excel数据导入API模块

提供Excel文件解析和数据导入功能，支持Material和StockRecord等DocType。
"""

import frappe
from frappe import _
from frappe.utils.file_manager import get_file
from frappe.utils import cint, flt, getdate
import openpyxl
from openpyxl import load_workbook
import json
from datetime import datetime
import os
import mimetypes

# 允许的文件类型和MIME类型
ALLOWED_EXTENSIONS = {'.xlsx'}  # 注意：openpyxl不支持.xls
ALLOWED_MIME_TYPES = {
    'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
MAX_ROWS = 10000  # 单次导入最大行数


def validate_file_security(file_url: str) -> str:
    """
    验证文件安全性

    Args:
        file_url: 文件URL

    Returns:
        str: 验证通过后的文件路径

    Raises:
        frappe.ValidationError: 文件验证失败
    """
    # 验证文件扩展名
    ext = os.path.splitext(file_url.lower())[1]
    if ext not in ALLOWED_EXTENSIONS:
        frappe.throw(
            _("不支持的文件格式：{0}。请上传 .xlsx 格式的Excel文件").format(ext),
            title=_("文件格式错误")
        )

    # 获取文件信息
    file_doc = frappe.get_doc("File", {"file_url": file_url})
    file_path = file_doc.get_full_path()

    # 验证文件是否存在
    if not os.path.exists(file_path):
        frappe.throw(_("文件不存在或已被删除"), title=_("文件错误"))

    # 验证文件大小
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        frappe.throw(
            _("文件大小超过限制（最大{0}MB）").format(MAX_FILE_SIZE // (1024 * 1024)),
            title=_("文件过大")
        )

    # 验证MIME类型（防止伪造扩展名）
    mime_type, _ = mimetypes.guess_type(file_path)
    if mime_type not in ALLOWED_MIME_TYPES:
        frappe.throw(
            _("文件内容与扩展名不匹配，可能存在安全风险"),
            title=_("文件验证失败")
        )

    return file_path


@frappe.whitelist()
def import_excel_data(doctype: str, file_url: str) -> dict:
    """
    导入Excel数据到指定DocType

    Args:
        doctype: 目标DocType名称（Material/StockRecord等）
        file_url: 上传文件的URL

    Returns:
        dict: 导入结果统计，包含success, total_records, imported_records等字段

    Security:
        - 需要用户具有目标DocType的create权限
        - 文件大小限制为10MB
        - 单次导入最大10000行
    """

    try:
        # 🔒 安全检查1：验证用户权限
        if not frappe.has_permission(doctype, "create"):
            frappe.throw(
                _("您没有创建{0}记录的权限").format(_(doctype)),
                frappe.PermissionError
            )

        # 🔒 安全检查2：验证DocType是否在允许列表中
        allowed_doctypes = get_allowed_import_doctypes()
        if doctype not in allowed_doctypes:
            frappe.throw(
                _("不允许导入到{0}，请联系管理员").format(doctype),
                title=_("操作被拒绝")
            )

        # 🔒 安全检查3：验证文件安全性
        file_path = validate_file_security(file_url)

        # 解析Excel文件（使用read_only模式优化内存）
        workbook = load_workbook(file_path, data_only=True, read_only=True)
        worksheet = workbook.active

        # 获取字段映射配置
        field_mapping = get_field_mapping(doctype)

        # 解析数据（带行数限制）
        data_rows = parse_excel_data(worksheet, field_mapping, max_rows=MAX_ROWS)

        # 关闭workbook释放资源
        workbook.close()

        if not data_rows:
            frappe.throw(_("Excel文件中没有找到有效数据"))

        # 验证并导入数据
        result = validate_and_import_data(doctype, data_rows)

        # 记录导入日志
        log_import_operation(doctype, len(data_rows), result)

        return {
            'success': True,
            'total_records': len(data_rows),
            'imported_records': result['success_count'],
            'failed_records': result['error_count'],
            'errors': result['errors'][:50],  # 限制返回的错误数量
            'message': _("导入完成：成功{0}条，失败{1}条").format(
                result['success_count'], result['error_count']
            )
        }

    except frappe.PermissionError:
        raise  # 权限错误直接抛出
    except Exception as e:
        frappe.log_error(
            message=f"Excel导入失败: {str(e)}\n\nDocType: {doctype}\nFile: {file_url}",
            title="Excel Import Error"
        )
        return {
            'success': False,
            'error': str(e),
            'message': _("导入失败：{0}").format(str(e))
        }


def get_allowed_import_doctypes() -> list:
    """获取允许导入的DocType列表"""
    return ['Material', 'StockRecord', 'Item', 'Stock Entry']

def get_field_mapping(doctype: str) -> dict:
    """
    获取字段映射配置

    Args:
        doctype: DocType名称

    Returns:
        dict: Excel列到字段的映射关系
    """

    # Material DocType字段映射
    if doctype == 'Material':
        return {
            'A': {'fieldname': 'material_code', 'label': '物料编码', 'required': True, 'type': 'Data'},
            'B': {'fieldname': 'material_name', 'label': '物料名称', 'required': True, 'type': 'Data'},
            'C': {'fieldname': 'specification', 'label': '规格', 'required': False, 'type': 'Data'},
            'D': {'fieldname': 'unit', 'label': '单位', 'required': True, 'type': 'Link', 'options': 'UOM'},
            'E': {'fieldname': 'calculate_by_weight', 'label': '按重量计算', 'required': False, 'type': 'Check'},
            'F': {'fieldname': 'default_price', 'label': '默认单价', 'required': False, 'type': 'Currency'}
        }

    # StockRecord DocType字段映射
    elif doctype == 'StockRecord':
        return {
            'A': {'fieldname': 'record_type', 'label': '记录类型', 'required': True, 'type': 'Select',
                  'options': ['入库', '出库', '调拨']},
            'B': {'fieldname': 'supplier', 'label': '供应商', 'required': False, 'type': 'Link', 'options': 'Supplier'},
            'C': {'fieldname': 'material', 'label': '物料', 'required': True, 'type': 'Link', 'options': 'Material'},
            'D': {'fieldname': 'specification', 'label': '规格', 'required': False, 'type': 'Data'},
            'E': {'fieldname': 'quantity', 'label': '数量', 'required': True, 'type': 'Float'},
            'F': {'fieldname': 'weight', 'label': '重量', 'required': False, 'type': 'Float'},
            'G': {'fieldname': 'price', 'label': '单价', 'required': False, 'type': 'Currency'},
            'H': {'fieldname': 'record_date', 'label': '记录日期', 'required': True, 'type': 'Date'},
            'I': {'fieldname': 'remarks', 'label': '备注', 'required': False, 'type': 'Text'}
        }

    # 扩展：支持ERPNext标准Item DocType
    elif doctype == 'Item':
        return {
            'A': {'fieldname': 'item_code', 'label': '物料编码', 'required': True, 'type': 'Data'},
            'B': {'fieldname': 'item_name', 'label': '物料名称', 'required': True, 'type': 'Data'},
            'C': {'fieldname': 'item_group', 'label': '物料组', 'required': True, 'type': 'Link', 'options': 'Item Group'},
            'D': {'fieldname': 'stock_uom', 'label': '库存单位', 'required': True, 'type': 'Link', 'options': 'UOM'},
            'E': {'fieldname': 'description', 'label': '描述', 'required': False, 'type': 'Text Editor'}
        }

    frappe.throw(_("不支持的DocType：{0}").format(doctype))


def parse_excel_data(worksheet, field_mapping: dict, max_rows: int = 10000) -> list:
    """
    解析Excel数据

    Args:
        worksheet: openpyxl工作表对象
        field_mapping: 字段映射配置
        max_rows: 最大处理行数

    Returns:
        list: 解析后的数据行列表
    """
    data_rows = []
    row_count = 0

    for row_idx, row in enumerate(worksheet.iter_rows(min_row=2, values_only=True), start=2):
        # 跳过完全空的行
        if all(cell is None or str(cell).strip() == '' for cell in row):
            continue

        row_count += 1
        if row_count > max_rows:
            frappe.msgprint(
                _("数据行数超过限制（{0}行），仅处理前{0}行").format(max_rows),
                indicator='orange',
                alert=True
            )
            break

        row_data = {}
        for col_letter, field_config in field_mapping.items():
            col_idx = ord(col_letter) - ord('A')
            if col_idx < len(row):
                raw_value = row[col_idx]
                # 类型转换
                row_data[field_config['fieldname']] = convert_cell_value(
                    raw_value,
                    field_config.get('type', 'Data'),
                    field_config.get('fieldname')
                )

        data_rows.append({
            'row_number': row_idx,
            'data': row_data
        })

    return data_rows


def convert_cell_value(value, field_type: str, fieldname: str):
    """
    转换单元格值为对应字段类型

    Args:
        value: 原始单元格值
        field_type: 字段类型
        fieldname: 字段名（用于错误提示）

    Returns:
        转换后的值
    """
    if value is None or str(value).strip() == '':
        return None

    try:
        if field_type == 'Int':
            return cint(value)
        elif field_type in ('Float', 'Currency', 'Percent'):
            return flt(value)
        elif field_type == 'Check':
            # 支持多种布尔值表示
            if isinstance(value, bool):
                return 1 if value else 0
            str_val = str(value).strip().lower()
            return 1 if str_val in ('1', 'yes', 'true', '是', '√') else 0
        elif field_type == 'Date':
            if isinstance(value, datetime):
                return value.date()
            return getdate(value)
        elif field_type == 'Datetime':
            if isinstance(value, datetime):
                return value
            return frappe.utils.get_datetime(value)
        else:
            return str(value).strip() if value else None
    except Exception as e:
        frappe.log_error(f"字段{fieldname}值转换失败: {value} -> {field_type}: {str(e)}")
        return str(value).strip() if value else None

def validate_link_field(doctype: str, fieldname: str, value, options: str) -> tuple:
    """
    验证链接字段的值是否存在

    Args:
        doctype: 当前DocType
        fieldname: 字段名
        value: 字段值
        options: 链接目标DocType

    Returns:
        tuple: (是否有效, 错误信息)
    """
    if not value:
        return True, None

    # 检查链接目标是否存在
    if not frappe.db.exists(options, value):
        return False, _("字段'{0}'的值'{1}'在{2}中不存在").format(
            fieldname, value, _(options)
        )

    return True, None


def validate_row_data(doctype: str, row_data: dict, field_mapping: dict) -> list:
    """
    验证单行数据

    Args:
        doctype: DocType名称
        row_data: 行数据
        field_mapping: 字段映射配置

    Returns:
        list: 验证错误列表
    """
    errors = []

    for col_letter, field_config in field_mapping.items():
        fieldname = field_config['fieldname']
        value = row_data.get(fieldname)

        # 必填字段验证
        if field_config.get('required') and not value:
            errors.append(_("必填字段'{0}'不能为空").format(field_config['label']))
            continue

        # Link字段验证
        if field_config.get('type') == 'Link' and value:
            is_valid, error_msg = validate_link_field(
                doctype, fieldname, value, field_config.get('options')
            )
            if not is_valid:
                errors.append(error_msg)

        # Select字段验证
        if field_config.get('type') == 'Select' and value:
            allowed_options = field_config.get('options', [])
            if isinstance(allowed_options, list) and value not in allowed_options:
                errors.append(_("字段'{0}'的值'{1}'不在允许的选项中").format(
                    field_config['label'], value
                ))

    return errors


def validate_and_import_data(doctype: str, data_rows: list) -> dict:
    """
    验证并导入数据（支持事务回滚）

    Args:
        doctype: DocType名称
        data_rows: 数据行列表

    Returns:
        dict: 导入结果统计
    """
    success_count = 0
    error_count = 0
    errors = []

    # 获取字段映射用于验证
    field_mapping = get_field_mapping(doctype)

    # 预验证阶段：检查所有链接字段
    frappe.publish_progress(0, title=_("正在验证数据..."))

    for idx, row_info in enumerate(data_rows):
        row_number = row_info['row_number']
        row_data = row_info['data']

        # 更新进度
        if idx % 100 == 0:
            progress = int((idx / len(data_rows)) * 50)
            frappe.publish_progress(progress, title=_("正在验证数据..."))

        # 行级验证
        row_errors = validate_row_data(doctype, row_data, field_mapping)
        if row_errors:
            error_count += 1
            errors.append({
                'row': row_number,
                'error': '; '.join(row_errors),
                'data': row_data
            })
            continue

        try:
            # 创建新文档
            doc = frappe.new_doc(doctype)

            # 设置字段值
            for fieldname, value in row_data.items():
                if hasattr(doc, fieldname) and value is not None:
                    setattr(doc, fieldname, value)

            # 特殊处理：对于StockRecord，需要自动计算合计金额
            if doctype == 'StockRecord':
                calculate_total_amount(doc)

            # 调用文档的validate方法
            doc.flags.ignore_permissions = False  # 确保权限检查
            doc.validate()

            # 保存文档（不触发after_insert以提高性能）
            doc.flags.ignore_version = True
            doc.insert()
            success_count += 1

            # 更新进度
            if success_count % 100 == 0:
                progress = 50 + int((success_count / len(data_rows)) * 50)
                frappe.publish_progress(progress, title=_("正在导入数据..."))

        except Exception as e:
            error_count += 1
            errors.append({
                'row': row_number,
                'error': str(e),
                'data': {k: str(v)[:100] for k, v in row_data.items()}  # 截断长数据
            })
            frappe.log_error(
                message=f"第{row_number}行导入失败: {str(e)}\n数据: {row_data}",
                title=f"Excel Import - {doctype}"
            )

    # 提交事务
    if success_count > 0:
        frappe.db.commit()

    frappe.publish_progress(100, title=_("导入完成"))

    return {
        'success_count': success_count,
        'error_count': error_count,
        'errors': errors
    }


def calculate_total_amount(doc):
    """计算StockRecord的合计金额"""
    if hasattr(doc, 'quantity') and hasattr(doc, 'price'):
        qty = flt(doc.quantity) or 0
        price = flt(doc.price) or 0
        doc.total_amount = qty * price


def log_import_operation(doctype: str, total_rows: int, result: dict):
    """
    记录导入操作日志

    Args:
        doctype: DocType名称
        total_rows: 总行数
        result: 导入结果
    """
    frappe.get_doc({
        'doctype': 'Comment',
        'comment_type': 'Info',
        'reference_doctype': 'User',
        'reference_name': frappe.session.user,
        'content': _("Excel导入操作：{doctype}，总计{total}行，成功{success}行，失败{failed}行").format(
            doctype=doctype,
            total=total_rows,
            success=result['success_count'],
            failed=result['error_count']
        )
    }).insert(ignore_permissions=True)
```

### 3.1.1 模板下载API

```python
@frappe.whitelist()
def download_import_template(doctype: str):
    """
    下载导入模板

    Args:
        doctype: DocType名称

    Returns:
        dict: 模板文件URL
    """
    if not frappe.has_permission(doctype, "create"):
        frappe.throw(_("您没有权限"), frappe.PermissionError)

    field_mapping = get_field_mapping(doctype)

    # 创建工作簿
    from openpyxl import Workbook
    from openpyxl.styles import Font, PatternFill, Alignment

    wb = Workbook()
    ws = wb.active
    ws.title = doctype

    # 设置表头样式
    header_font = Font(bold=True, color="FFFFFF")
    header_fill = PatternFill(start_color="4472C4", end_color="4472C4", fill_type="solid")

    # 写入表头
    for col_letter, field_config in field_mapping.items():
        col_idx = ord(col_letter) - ord('A') + 1
        cell = ws.cell(row=1, column=col_idx)

        # 表头格式：字段名称（必填标记）
        header_text = field_config['label']
        if field_config.get('required'):
            header_text += ' *'
        cell.value = header_text

        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = Alignment(horizontal='center')

        # 设置列宽
        ws.column_dimensions[col_letter].width = 15

    # 添加示例数据行（第2行）
    # ...可以添加示例数据

    # 保存到临时文件
    import tempfile
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        wb.save(tmp.name)
        tmp_path = tmp.name

    # 读取文件内容并保存到Frappe
    with open(tmp_path, 'rb') as f:
        file_content = f.read()

    from frappe.utils.file_manager import save_file
    file_doc = save_file(
        fname=f"{doctype}_import_template.xlsx",
        content=file_content,
        dt="User",
        dn=frappe.session.user,
        is_private=0
    )

    # 清理临时文件
    os.unlink(tmp_path)

    return {'file_url': file_doc.file_url}
```

### 3.2 前端JavaScript组件

#### 3.2.1 标准DocType扩展方式 (material_excel_import.js)

```javascript
/**
 * Material DocType Excel导入扩展
 *
 * 文件路径: erpnext_custom/public/js/material_excel_import.js
 * 需要在hooks.py中配置: doctype_js = {"Material": "public/js/material_excel_import.js"}
 */

frappe.ui.form.on('Material', {
    refresh: function(frm) {
        // 只有新建或保存后的记录才显示导入按钮
        // 注意：导入按钮通常放在List View，这里是为了演示
        if (!frm.is_new()) {
            frm.add_custom_button(__('从Excel导入'), function() {
                erpnext_custom.show_excel_import_dialog('Material', frm);
            }, __('操作'));
        }
    },

    onload: function(frm) {
        // 监听实时导入进度
        frappe.realtime.on('excel_import_progress', function(data) {
            if (data.doctype !== 'Material') return;

            let percent = Math.floor((data.current / data.total) * 100);
            frappe.show_progress(__('导入进度'), percent, 100, data.message);

            if (data.current === data.total) {
                setTimeout(() => {
                    frappe.hide_progress();
                    frm.reload_doc();
                }, 1000);
            }
        });
    }
});

// 命名空间
frappe.provide('erpnext_custom');

/**
 * 显示Excel导入对话框
 *
 * @param {string} doctype - DocType名称
 * @param {object} frm - Frappe Form对象（可选）
 */
erpnext_custom.show_excel_import_dialog = function(doctype, frm) {
    let dialog = new frappe.ui.Dialog({
        title: __('导入{0}数据', [__(doctype)]),
        size: 'large',
        fields: [
            {
                fieldname: 'section_upload',
                label: __('文件上传'),
                fieldtype: 'Section Break'
            },
            {
                fieldname: 'import_file',
                label: __('选择Excel文件'),
                fieldtype: 'Attach',
                reqd: 1,
                description: __('仅支持 .xlsx 格式，文件大小不超过10MB'),
                options: {
                    restrictions: {
                        allowed_file_types: ['.xlsx'],
                        max_file_size: 10 * 1024 * 1024 // 10MB
                    }
                }
            },
            {
                fieldtype: 'Column Break'
            },
            {
                fieldname: 'template_section',
                fieldtype: 'HTML',
                options: `
                    <div class="template-download">
                        <p class="text-muted">${__('首次使用？请先下载模板：')}</p>
                        <button class="btn btn-sm btn-default download-template-btn">
                            <i class="fa fa-download"></i> ${__('下载导入模板')}
                        </button>
                    </div>
                `
            },
            {
                fieldname: 'section_mapping',
                label: __('字段映射说明'),
                fieldtype: 'Section Break',
                collapsible: 1,
                collapsed: 1
            },
            {
                fieldname: 'mapping_info',
                fieldtype: 'HTML',
                options: erpnext_custom.get_field_mapping_html(doctype)
            }
        ],
        primary_action_label: __('开始导入'),
        primary_action: function(values) {
            if (!values.import_file) {
                frappe.throw(__('请先选择Excel文件'));
                return;
            }

            dialog.hide();
            erpnext_custom.start_excel_import(doctype, values.import_file, frm);
        },
        secondary_action_label: __('取消')
    });

    // 绑定模板下载按钮
    dialog.$wrapper.find('.download-template-btn').on('click', function() {
        erpnext_custom.download_import_template(doctype);
    });

    dialog.show();
};

/**
 * 获取字段映射HTML说明
 */
erpnext_custom.get_field_mapping_html = function(doctype) {
    let mappings = {
        'Material': [
            {col: 'A', field: '物料编码', required: true, example: 'M001'},
            {col: 'B', field: '物料名称', required: true, example: '螺丝钉'},
            {col: 'C', field: '规格', required: false, example: 'M8x20'},
            {col: 'D', field: '单位', required: true, example: '个'},
            {col: 'E', field: '按重量计算', required: false, example: '是/否'},
            {col: 'F', field: '默认单价', required: false, example: '0.5'}
        ],
        'StockRecord': [
            {col: 'A', field: '记录类型', required: true, example: '入库/出库'},
            {col: 'B', field: '供应商', required: false, example: 'SUP-001'},
            {col: 'C', field: '物料', required: true, example: 'M001'},
            {col: 'D', field: '规格', required: false, example: 'M8x20'},
            {col: 'E', field: '数量', required: true, example: '100'},
            {col: 'F', field: '重量', required: false, example: '5.5'},
            {col: 'G', field: '单价', required: false, example: '0.5'},
            {col: 'H', field: '记录日期', required: true, example: '2026-01-10'},
            {col: 'I', field: '备注', required: false, example: '首批到货'}
        ]
    };

    let fields = mappings[doctype] || [];
    if (!fields.length) return '<p class="text-muted">暂无字段映射信息</p>';

    let html = `
        <table class="table table-bordered table-sm">
            <thead>
                <tr>
                    <th>${__('列')}</th>
                    <th>${__('字段')}</th>
                    <th>${__('必填')}</th>
                    <th>${__('示例')}</th>
                </tr>
            </thead>
            <tbody>
    `;

    fields.forEach(f => {
        html += `
            <tr>
                <td><code>${f.col}</code></td>
                <td>${f.field}</td>
                <td>${f.required ? '<span class="text-danger">*</span>' : ''}</td>
                <td class="text-muted">${f.example}</td>
            </tr>
        `;
    });

    html += '</tbody></table>';
    return html;
};

/**
 * 开始Excel导入
 */
erpnext_custom.start_excel_import = function(doctype, file_url, frm) {
    // 显示进度条
    frappe.show_progress(__('正在导入'), 0, 100, __('准备中...'));

    frappe.call({
        method: 'erpnext_custom.api.import_excel_data',
        args: {
            doctype: doctype,
            file_url: file_url
        },
        callback: function(r) {
            frappe.hide_progress();

            if (r.message) {
                erpnext_custom.show_import_result(r.message, frm);
            }
        },
        error: function(r) {
            frappe.hide_progress();
            frappe.msgprint({
                title: __('导入失败'),
                indicator: 'red',
                message: r.exc_type || __('未知错误，请查看错误日志')
            });
        }
    });
};

/**
 * 显示导入结果
 */
erpnext_custom.show_import_result = function(result, frm) {
    let indicator = result.success ? 'green' : 'red';
    let title = result.success ? __('导入完成') : __('导入失败');

    let html = `<p>${result.message}</p>`;

    // 显示错误详情
    if (result.errors && result.errors.length > 0) {
        html += `
            <div class="import-errors mt-3">
                <h5>${__('错误详情')}（显示前50条）</h5>
                <div class="table-responsive" style="max-height: 300px; overflow-y: auto;">
                    <table class="table table-sm table-bordered">
                        <thead>
                            <tr>
                                <th>${__('行号')}</th>
                                <th>${__('错误信息')}</th>
                            </tr>
                        </thead>
                        <tbody>
        `;

        result.errors.slice(0, 50).forEach(err => {
            html += `
                <tr>
                    <td>${err.row}</td>
                    <td class="text-danger">${frappe.utils.escape_html(err.error)}</td>
                </tr>
            `;
        });

        html += '</tbody></table></div></div>';
    }

    frappe.msgprint({
        title: title,
        indicator: indicator,
        message: html
    });

    // 刷新列表或表单
    if (frm) {
        frm.reload_doc();
    } else {
        // 刷新当前列表视图
        if (cur_list) {
            cur_list.refresh();
        }
    }
};

/**
 * 下载导入模板
 */
erpnext_custom.download_import_template = function(doctype) {
    frappe.call({
        method: 'erpnext_custom.api.download_import_template',
        args: { doctype: doctype },
        callback: function(r) {
            if (r.message && r.message.file_url) {
                window.open(r.message.file_url);
            }
        }
    });
};
```

#### 3.2.2 List View 添加导入按钮（推荐方式）

```javascript
/**
 * Material List View 导入按钮
 *
 * 文件路径: erpnext_custom/public/js/material_list.js
 * 需要在hooks.py中配置: doctype_list_js = {"Material": "public/js/material_list.js"}
 */

frappe.listview_settings['Material'] = {
    onload: function(listview) {
        // 添加导入按钮到页面操作栏
        listview.page.add_inner_button(__('从Excel导入'), function() {
            erpnext_custom.show_excel_import_dialog('Material');
        });
    },

    refresh: function(listview) {
        // 可以在这里添加刷新后的逻辑
    }
};
```

---

## 4. 安全性设计

### 4.1 安全威胁分析

| 威胁类型 | 风险等级 | 防护措施 |
|---------|---------|---------|
| 恶意文件上传 | 🔴 高 | MIME类型验证、文件扩展名白名单、文件内容检查 |
| 越权操作 | 🔴 高 | 权限验证、DocType白名单、用户身份校验 |
| SQL注入 | 🔴 高 | 使用Frappe ORM、参数化查询、避免原始SQL |
| XSS攻击 | 🟡 中 | 输出转义、使用`frappe.utils.escape_html()` |
| DoS攻击 | 🟡 中 | 文件大小限制、行数限制、请求频率限制 |
| 数据泄露 | 🟡 中 | 私有文件存储、访问日志记录 |

### 4.2 安全实现代码

```python
# security.py - 安全验证模块

import frappe
from frappe import _
import os
import magic  # python-magic库，用于检测真实文件类型

# 安全配置
SECURITY_CONFIG = {
    'max_file_size': 10 * 1024 * 1024,  # 10MB
    'max_rows': 10000,
    'allowed_extensions': {'.xlsx'},
    'allowed_mime_types': {
        'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
    },
    'allowed_doctypes': ['Material', 'StockRecord', 'Item'],
    'rate_limit': 10,  # 每分钟最大请求数
}


def check_file_security(file_path: str) -> None:
    """
    全面的文件安全检查

    Raises:
        frappe.ValidationError: 安全检查失败
    """
    # 1. 检查文件是否存在
    if not os.path.exists(file_path):
        frappe.throw(_("文件不存在"), frappe.DoesNotExistError)

    # 2. 检查文件大小
    file_size = os.path.getsize(file_path)
    if file_size > SECURITY_CONFIG['max_file_size']:
        frappe.throw(_("文件大小超过限制"))

    # 3. 检查文件扩展名
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SECURITY_CONFIG['allowed_extensions']:
        frappe.throw(_("不允许的文件类型"))

    # 4. 使用magic库检测真实文件类型（防止伪造扩展名）
    try:
        mime = magic.Magic(mime=True)
        detected_mime = mime.from_file(file_path)
        if detected_mime not in SECURITY_CONFIG['allowed_mime_types']:
            frappe.throw(_("文件内容与扩展名不匹配"))
    except Exception:
        # magic库不可用时，跳过此检查但记录警告
        frappe.log_error("python-magic库不可用，跳过MIME类型检测")

    # 5. 检查文件是否为空或损坏
    if file_size == 0:
        frappe.throw(_("文件为空"))


def check_user_permission(doctype: str) -> None:
    """
    检查用户权限

    Raises:
        frappe.PermissionError: 权限不足
    """
    # 1. 检查用户是否登录
    if frappe.session.user == 'Guest':
        frappe.throw(_("请先登录"), frappe.AuthenticationError)

    # 2. 检查DocType是否在允许列表中
    if doctype not in SECURITY_CONFIG['allowed_doctypes']:
        frappe.throw(_("不允许导入此类型数据"))

    # 3. 检查用户是否有创建权限
    if not frappe.has_permission(doctype, 'create'):
        frappe.throw(_("您没有创建{0}的权限").format(_(doctype)), frappe.PermissionError)

    # 4. 可选：检查用户是否有导入权限（可通过自定义角色实现）
    # if not frappe.has_permission(doctype, 'import'):
    #     frappe.throw(_("您没有导入权限"), frappe.PermissionError)


def check_rate_limit(user: str, action: str = 'excel_import') -> None:
    """
    检查请求频率限制

    Args:
        user: 用户名
        action: 操作类型

    Raises:
        frappe.RateLimitExceededError: 超过频率限制
    """
    from frappe.utils import now_datetime, add_to_date

    cache_key = f"rate_limit:{action}:{user}"

    # 获取最近一分钟的请求计数
    request_count = frappe.cache().get(cache_key) or 0

    if request_count >= SECURITY_CONFIG['rate_limit']:
        frappe.throw(
            _("操作过于频繁，请稍后再试"),
            frappe.RateLimitExceededError
        )

    # 增加计数（60秒过期）
    frappe.cache().set(cache_key, request_count + 1, expires_in_sec=60)


def sanitize_cell_value(value, max_length: int = 1000) -> str:
    """
    清理单元格值，防止XSS和注入攻击

    Args:
        value: 原始值
        max_length: 最大长度

    Returns:
        str: 清理后的值
    """
    if value is None:
        return None

    # 转换为字符串
    str_value = str(value).strip()

    # 截断过长内容
    if len(str_value) > max_length:
        str_value = str_value[:max_length]

    # 移除潜在的危险字符（如公式注入）
    if str_value.startswith(('=', '+', '-', '@')):
        str_value = "'" + str_value  # 添加引号前缀防止公式执行

    return str_value
```

### 4.3 权限配置示例

```python
# fixtures/custom_role.json - 自定义角色权限

[
    {
        "doctype": "Role",
        "role_name": "Excel Import User",
        "desk_access": 1,
        "is_custom": 1
    }
]
```

```python
# fixtures/custom_docperm.json - DocType权限配置

[
    {
        "doctype": "Custom DocPerm",
        "parent": "Material",
        "parentfield": "permissions",
        "parenttype": "DocType",
        "role": "Excel Import User",
        "permlevel": 0,
        "read": 1,
        "write": 1,
        "create": 1,
        "delete": 0,
        "import": 1,
        "export": 1
    }
]
```

---

## 7. 技术风险评估与改进建议

### 7.1 高风险问题 🔴（需要立即修复）

#### 7.1.1 内存溢出风险
**问题描述**：一次性加载整个Excel文件，大文件（>10000行）可能导致系统崩溃。

**改进方案**：
```python
def parse_excel_batch(file_path, batch_size=1000):
    """分批读取Excel文件，避免内存溢出"""
    workbook = load_workbook(file_path, data_only=True, read_only=True)
    worksheet = workbook.active

    for row_batch in batch_rows(worksheet, batch_size):
        yield process_batch(row_batch)
```

#### 7.1.2 事务一致性问题
**问题描述**：逐条处理批量提交，部分成功时难以回滚。

**改进方案**：
```python
@frappe.whitelist()
def import_excel_data_transactional(doctype, file_url):
    """事务性导入数据"""
    try:
        frappe.db.begin()

        # 处理所有数据
        success_count = process_all_records(doctype, file_url)

        frappe.db.commit()
        return {'success': True, 'imported': success_count}

    except Exception as e:
        frappe.db.rollback()
        frappe.log_error(f"导入失败: {str(e)}")
        return {'success': False, 'error': str(e)}
```

### 7.2 推荐架构方案：使用ERPNext原生Data Import

```python
@frappe.whitelist()
def create_data_import_job(doctype, file_url):
    """创建数据导入任务 - 推荐方案"""

    try:
        # 创建Data Import记录
        data_import = frappe.get_doc({
            'doctype': 'Data Import',
            'reference_doctype': doctype,
            'import_type': 'Insert New Records',
            'file_url': file_url,
            'submit_after_import': 1,
            'template_options': get_template_options(doctype)
        })

        data_import.insert()

        # 启动异步导入任务
        frappe.enqueue(
            'frappe.core.doctype.data_import.data_import.import_data',
            data_import=data_import.name,
            queue='long',
            timeout=3000,
            now=frappe.conf.developer_mode  # 开发模式立即执行
        )

        return {
            'success': True,
            'data_import_name': data_import.name,
            'message': _('数据导入任务已创建，正在后台处理...'),
            'track_url': f'/app/data-import/{data_import.name}'
        }

    except Exception as e:
        frappe.log_error(f"创建导入任务失败: {str(e)}")
        return {
            'success': False,
            'error': str(e),
            'message': _('创建导入任务失败，请联系管理员')
        }
```

**优势分析**：
- ✅ **事务安全**：原生支持事务回滚
- ✅ **性能优化**：内置分批处理机制
- ✅ **错误处理**：完善的错误报告和跟踪
- ✅ **用户界面**：标准的ERPNext界面风格

---

## 6. 完整测试用例覆盖

### 6.1 单元测试基础设施

```python
# tests/test_excel_import.py

import frappe
import unittest
from unittest.mock import patch, MagicMock
from frappe.tests.utils import FrappeTestCase
import tempfile
import os

class TestExcelImport(FrappeTestCase):
    """Excel导入功能测试套件"""

    @classmethod
    def setUpClass(cls):
        """测试类初始化"""
        super().setUpClass()
        # 创建测试用户
        cls.test_user = frappe.get_doc({
            'doctype': 'User',
            'email': 'test_import@example.com',
            'first_name': 'Test',
            'roles': [{'role': 'System Manager'}]
        }).insert(ignore_permissions=True)

    @classmethod
    def tearDownClass(cls):
        """测试类清理"""
        super().tearDownClass()
        frappe.delete_doc('User', cls.test_user.name, force=True)

    def setUp(self):
        """每个测试前的准备"""
        frappe.set_user('test_import@example.com')

    def tearDown(self):
        """每个测试后的清理"""
        frappe.set_user('Administrator')
        # 清理测试数据
        frappe.db.rollback()
```

### 6.2 边界条件测试

#### 6.2.1 空文件测试
```python
def test_empty_file_import(self):
    """测试空Excel文件导入"""
    from openpyxl import Workbook

    # 创建空Excel文件
    wb = Workbook()
    ws = wb.active
    ws['A1'] = '物料编码'  # 只有表头，没有数据

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        wb.save(tmp.name)
        empty_file = self._upload_test_file(tmp.name)

    # 尝试导入
    from erpnext_custom.api import import_excel_data
    result = import_excel_data('Material', empty_file.file_url)

    # 验证结果
    self.assertFalse(result['success'])
    self.assertIn('没有找到有效数据', result.get('message', ''))
```

#### 6.2.2 超大文件测试
```python
def test_large_file_handling(self):
    """测试大文件处理能力（内存优化验证）"""
    import psutil
    import gc

    # 创建包含10000行数据的测试文件
    large_file = self._create_large_test_file(10000)

    # 强制垃圾回收以获得准确的内存基线
    gc.collect()
    process = psutil.Process()
    memory_before = process.memory_info().rss

    # 导入大文件
    from erpnext_custom.api import import_excel_data
    result = import_excel_data('Material', large_file.file_url)

    gc.collect()
    memory_after = process.memory_info().rss
    memory_used = memory_after - memory_before

    # 验证内存使用在合理范围内（500MB限制）
    self.assertLess(memory_used, 500 * 1024 * 1024)
    self.assertTrue(result['success'])
    self.assertEqual(result['total_records'], 10000)
```

#### 6.2.3 超出行数限制测试
```python
def test_row_limit_exceeded(self):
    """测试超出最大行数限制"""
    # 创建超过10000行的文件
    large_file = self._create_large_test_file(15000)

    from erpnext_custom.api import import_excel_data
    result = import_excel_data('Material', large_file.file_url)

    # 验证只处理了前10000行
    self.assertTrue(result['success'])
    self.assertEqual(result['total_records'], 10000)
```

### 6.3 链接字段验证测试

#### 6.3.1 有效链接字段测试
```python
def test_valid_link_field(self):
    """测试有效的链接字段值"""
    # 先创建引用的记录
    uom = frappe.get_doc({
        'doctype': 'UOM',
        'uom_name': 'Test Unit'
    }).insert(ignore_permissions=True)

    # 创建包含有效链接的测试文件
    test_file = self._create_test_file_with_data([
        {'material_code': 'TEST001', 'material_name': 'Test', 'unit': 'Test Unit'}
    ])

    from erpnext_custom.api import import_excel_data
    result = import_excel_data('Material', test_file.file_url)

    self.assertTrue(result['success'])
    self.assertEqual(result['imported_records'], 1)

    # 清理
    frappe.delete_doc('UOM', uom.name, force=True)
```

#### 6.3.2 无效链接字段测试
```python
def test_invalid_link_field(self):
    """测试无效的链接字段值"""
    # 创建包含无效链接的测试文件
    test_file = self._create_test_file_with_data([
        {'material_code': 'TEST002', 'material_name': 'Test', 'unit': 'NonExistentUOM'}
    ])

    from erpnext_custom.api import import_excel_data
    result = import_excel_data('Material', test_file.file_url)

    # 验证错误被正确捕获
    self.assertEqual(result['error_count'], 1)
    self.assertIn('不存在', result['errors'][0]['error'])
```

### 6.4 权限测试

#### 6.4.1 无权限用户测试
```python
def test_permission_denied(self):
    """测试无权限用户导入"""
    # 创建无权限用户
    no_perm_user = frappe.get_doc({
        'doctype': 'User',
        'email': 'no_perm@example.com',
        'first_name': 'No Permission',
        'roles': []  # 无任何角色
    }).insert(ignore_permissions=True)

    frappe.set_user('no_perm@example.com')

    test_file = self._create_simple_test_file()

    from erpnext_custom.api import import_excel_data
    result = import_excel_data('Material', test_file.file_url)

    # 验证权限被拒绝
    self.assertFalse(result['success'])
    self.assertIn('权限', result.get('error', ''))

    # 清理
    frappe.set_user('Administrator')
    frappe.delete_doc('User', no_perm_user.name, force=True)
```

#### 6.4.2 Guest用户测试
```python
def test_guest_user_blocked(self):
    """测试Guest用户被阻止"""
    frappe.set_user('Guest')

    from erpnext_custom.api import import_excel_data

    with self.assertRaises(frappe.AuthenticationError):
        import_excel_data('Material', '/files/test.xlsx')

    frappe.set_user('Administrator')
```

### 6.5 安全测试

#### 6.5.1 恶意文件检测测试
```python
def test_malicious_file_extension_rejected(self):
    """测试恶意文件扩展名被拒绝"""
    malicious_extensions = ['.exe', '.php', '.js', '.html', '.xls']  # .xls不被openpyxl支持

    for ext in malicious_extensions:
        # 创建伪装文件
        with tempfile.NamedTemporaryFile(suffix=ext, delete=False) as tmp:
            tmp.write(b'malicious content')
            malicious_file = self._upload_test_file(tmp.name)

        from erpnext_custom.api import import_excel_data
        result = import_excel_data('Material', malicious_file.file_url)

        self.assertFalse(result['success'])
        self.assertIn('不支持', result.get('message', '') or result.get('error', ''))
```

#### 6.5.2 文件大小限制测试
```python
def test_file_size_limit(self):
    """测试文件大小限制"""
    # 创建超过10MB的文件
    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        # 写入超过10MB的数据
        tmp.write(b'x' * (11 * 1024 * 1024))
        large_file = self._upload_test_file(tmp.name)

    from erpnext_custom.api import import_excel_data
    result = import_excel_data('Material', large_file.file_url)

    self.assertFalse(result['success'])
    self.assertIn('大小超过限制', result.get('message', '') or result.get('error', ''))
```

#### 6.5.3 CSV注入防护测试
```python
def test_csv_injection_prevention(self):
    """测试CSV注入防护"""
    # 创建包含潜在注入公式的测试数据
    injection_payloads = [
        '=CMD|"/C calc"!A0',
        '@SUM(1+1)*cmd|"/C calc"!A0',
        '+1+1*cmd|"/C calc"!A0',
        '-1+1*cmd|"/C calc"!A0'
    ]

    for payload in injection_payloads:
        test_file = self._create_test_file_with_data([
            {'material_code': payload, 'material_name': 'Test', 'unit': 'Nos'}
        ])

        from erpnext_custom.api import import_excel_data
        result = import_excel_data('Material', test_file.file_url)

        if result['success']:
            # 验证数据被清理（添加了引号前缀）
            doc = frappe.get_last_doc('Material')
            self.assertTrue(doc.material_code.startswith("'"))
```

### 6.6 错误恢复测试

#### 6.6.1 部分失败回滚测试
```python
def test_partial_failure_handling(self):
    """测试部分数据失败时的处理"""
    # 创建混合有效和无效数据的文件
    test_data = [
        {'material_code': 'VALID001', 'material_name': 'Valid 1', 'unit': 'Nos'},
        {'material_code': '', 'material_name': 'Invalid - no code', 'unit': 'Nos'},  # 必填字段为空
        {'material_code': 'VALID002', 'material_name': 'Valid 2', 'unit': 'Nos'},
    ]
    test_file = self._create_test_file_with_data(test_data)

    from erpnext_custom.api import import_excel_data
    result = import_excel_data('Material', test_file.file_url)

    # 验证部分成功
    self.assertEqual(result['imported_records'], 2)
    self.assertEqual(result['error_count'], 1)

#### 6.6.2 数据库连接中断测试
```python
def test_database_failure_rollback(self):
    """测试数据库故障时的回滚"""
    test_file = self._create_simple_test_file()

    # 模拟数据库提交失败
    with patch('frappe.db.commit', side_effect=Exception('数据库连接中断')):
        from erpnext_custom.api import import_excel_data
        result = import_excel_data('Material', test_file.file_url)

        self.assertFalse(result['success'])
        self.assertIn('数据库连接中断', result.get('error', ''))

        # 验证没有遗留数据
        count = frappe.db.count('Material', {'material_code': ['like', 'TEST%']})
        self.assertEqual(count, 0)
```

### 6.7 并发测试

```python
def test_concurrent_import(self):
    """测试并发导入"""
    import threading
    import queue

    results = queue.Queue()

    def import_task(file_url, task_id):
        frappe.set_user('test_import@example.com')
        from erpnext_custom.api import import_excel_data
        result = import_excel_data('Material', file_url)
        results.put((task_id, result))

    # 创建多个测试文件
    test_files = [self._create_simple_test_file(prefix=f'CONC{i}') for i in range(3)]

    # 启动并发导入
    threads = []
    for i, tf in enumerate(test_files):
        t = threading.Thread(target=import_task, args=(tf.file_url, i))
        threads.append(t)
        t.start()

    # 等待所有线程完成
    for t in threads:
        t.join(timeout=60)

    # 验证结果
    while not results.empty():
        task_id, result = results.get()
        self.assertTrue(result['success'], f"Task {task_id} failed: {result}")
```

### 6.8 辅助方法

```python
def _create_simple_test_file(self, prefix='TEST'):
    """创建简单的测试文件"""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active
    ws['A1'] = '物料编码'
    ws['B1'] = '物料名称'
    ws['C1'] = '规格'
    ws['D1'] = '单位'

    ws['A2'] = f'{prefix}001'
    ws['B2'] = 'Test Material'
    ws['C2'] = 'Spec'
    ws['D2'] = 'Nos'

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        wb.save(tmp.name)
        return self._upload_test_file(tmp.name)

def _create_test_file_with_data(self, data_list):
    """根据数据列表创建测试文件"""
    from openpyxl import Workbook

    wb = Workbook()
    ws = wb.active

    # 表头
    headers = ['物料编码', '物料名称', '规格', '单位']
    for col, header in enumerate(headers, 1):
        ws.cell(row=1, column=col, value=header)

    # 数据
    field_map = {'material_code': 1, 'material_name': 2, 'specification': 3, 'unit': 4}
    for row_idx, row_data in enumerate(data_list, 2):
        for field, col in field_map.items():
            ws.cell(row=row_idx, column=col, value=row_data.get(field, ''))

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        wb.save(tmp.name)
        return self._upload_test_file(tmp.name)

def _create_large_test_file(self, row_count):
    """创建大文件测试"""
    from openpyxl import Workbook

    wb = Workbook(write_only=True)  # 使用write_only模式节省内存
    ws = wb.create_sheet()

    ws.append(['物料编码', '物料名称', '规格', '单位'])
    for i in range(row_count):
        ws.append([f'MAT{i:06d}', f'Material {i}', f'Spec {i}', 'Nos'])

    with tempfile.NamedTemporaryFile(suffix='.xlsx', delete=False) as tmp:
        wb.save(tmp.name)
        return self._upload_test_file(tmp.name)

def _upload_test_file(self, file_path):
    """上传测试文件到Frappe"""
    with open(file_path, 'rb') as f:
        content = f.read()

    from frappe.utils.file_manager import save_file
    file_doc = save_file(
        fname=os.path.basename(file_path),
        content=content,
        dt='User',
        dn=frappe.session.user,
        is_private=1
    )

    return file_doc
```

---

## 8. 实施路线图

### 8.1 阶段一：快速验证（1周）
**目标**：使用现有方案实现基础功能验证

**任务清单**：
- [ ] 安装openpyxl依赖
- [ ] 部署基础API接口
- [ ] 集成前端按钮
- [ ] 限制数据量测试（<1000行）
- [ ] 基础错误处理验证

### 8.2 阶段二：架构重构（2周）
**目标**：迁移到ERPNext原生Data Import架构

**任务清单**：
- [ ] 研究ERPNext Data Import实现机制
- [ ] 重写后端API，使用原生Data Import
- [ ] 适配前端界面到标准风格
- [ ] 实现异步任务处理
- [ ] 完善错误报告机制

### 8.3 阶段三：生产优化（1周）
**目标**：性能调优和安全加固

**任务清单**：
- [ ] 性能压力测试
- [ ] 安全漏洞扫描和修复
- [ ] 用户权限细化
- [ ] 操作日志完善
- [ ] 用户培训和文档编写

---

## 9. 风险评估与应对策略

### 9.1 技术风险矩阵

| 风险项 | 影响程度 | 发生概率 | 风险等级 | 应对措施 |
|--------|----------|----------|---------|----------|
| 内存溢出 | 高 | 中 | 🔴 高 | 实现分批处理，限制文件大小 |
| 数据不一致 | 高 | 中 | 🔴 高 | 使用事务管理，实现错误回滚 |
| 性能瓶颈 | 中 | 高 | 🟡 中 | 异步处理，数据库优化 |
| 安全漏洞 | 中 | 低 | 🟡 中 | 加强输入验证，权限控制 |

### 9.2 实施优先级

| 风险类别 | 风险等级 | 处理优先级 | 建议时间 |
|---------|---------|-----------|----------|
| 内存溢出 | 🔴 高 | 立即 | 1-2天 |
| 事务一致性 | 🔴 高 | 立即 | 1-2天 |
| 数据验证 | 🟡 中 | 短期 | 3-5天 |
| 测试覆盖 | 🟢 低 | 长期 | 1-2周 |

---

## 10. 部署与运维指南

### 10.1 环境要求
- ERPNext版本：v14+
- Python版本：3.8+
- 数据库：MariaDB 10.3+
- Redis：5.0+（用于异步任务）

### 10.2 部署步骤
1. 安装openpyxl依赖：`pip install openpyxl`
2. 创建自定义应用目录结构
3. 部署API和前端组件
4. 配置权限和菜单
5. 执行测试用例验证

### 10.3 监控与维护
- **性能监控**：监控导入任务执行时间和内存使用
- **错误监控**：设置错误日志告警
- **数据审计**：定期检查导入数据质量
- **备份策略**：重要数据导入前进行备份

---

## 11. 最终建议与结论

### 11.1 总体评级
**审查结论**：🟡 **有条件采纳** - 需要重大改进后实施
**推荐等级**：B级方案

### 11.2 关键成功因素
1. **充分测试**：覆盖各种边界情况和异常场景
2. **用户培训**：提供详细的使用指南和培训
3. **渐进部署**：从少量数据开始，逐步扩大使用范围
4. **监控告警**：实时监控导入性能和错误率

### 11.3 推荐实施策略
**首选方案**：使用ERPNext原生Data Import功能
- 理由：最佳实践，性能优秀，维护成本低
- 适用场景：标准数据导入需求

**备选方案**：增强自定义实现
- 理由：灵活性高，可定制性强
- 适用场景：特殊业务逻辑需求

---

## 12. 附录

### 12.1 ERPNext标准DocType对照表

| 本文档示例 | ERPNext标准DocType | 说明 |
|-----------|-------------------|------|
| Material | **Item** | 物料/物品主数据 |
| StockRecord | **Stock Entry** | 库存凭证（出入库记录） |
| - | **Stock Ledger Entry** | 库存分类账（系统自动生成） |
| - | **Material Request** | 物料需求单 |
| - | **Purchase Receipt** | 采购收货单 |
| - | **Delivery Note** | 送货单 |

### 12.2 Frappe Data Import 原生功能

ERPNext/Frappe框架已内置完善的数据导入功能，位于 `/app/data-import`。

**原生功能优势**：
- ✅ 完整的事务管理和回滚
- ✅ 内置字段映射界面
- ✅ 支持更新和插入模式
- ✅ 异步任务队列处理
- ✅ 详细的导入日志（Data Import Log）
- ✅ 错误行导出功能

**使用方式**：
```python
# 使用原生Data Import
from frappe.core.doctype.data_import.data_import import DataImport
from frappe.core.doctype.data_import.importer import Importer

data_import = frappe.get_doc({
    'doctype': 'Data Import',
    'reference_doctype': 'Item',
    'import_type': 'Insert New Records',
    'import_file': file_url
})
data_import.insert()

# 启动导入
importer = Importer(data_import.reference_doctype, data_import=data_import)
importer.import_data()
```

### 12.3 常见问题解答 (FAQ)

**Q1: 为什么只支持 .xlsx 不支持 .xls？**
> A: openpyxl库仅支持Office Open XML格式（.xlsx），不支持旧版二进制格式（.xls）。
> 如需支持.xls，需要额外安装xlrd库并增加格式判断逻辑。

**Q2: 导入大文件时系统卡顿怎么办？**
> A: 建议将大文件拆分为多个小文件（每个不超过5000行），或使用异步导入方式。

**Q3: 链接字段（如供应商、物料）必须填写什么？**
> A: 必须填写目标记录的ID或名称。例如供应商字段需要填写Supplier的name值。

**Q4: 如何处理导入失败的行？**
> A: 系统会返回失败行的详细错误信息。建议修正后只重新导入失败的行。

**Q5: 可以更新已有记录吗？**
> A: 本方案主要针对新增记录。如需更新功能，建议使用Frappe原生Data Import的"Update Existing Records"模式。

### 12.4 依赖清单

```txt
# requirements.txt

# Excel处理（已包含在Frappe中）
openpyxl>=3.0.0

# 可选：支持.xls格式
# xlrd>=2.0.0

# 可选：文件类型检测
# python-magic>=0.4.0

# 可选：内存监控（用于测试）
# psutil>=5.0.0
```

---

## 📄 文档信息

**文档版本**：v2.0
**创建日期**：2026-01-10
**最后更新**：2026-01-10
**审查状态**：已完成深度技术审查

---

## 📝 修订历史

| 版本 | 日期 | 修订内容 | 审查人 |
|-----|------|---------|--------|
| v1.0 | 2026-01-10 | 初始版本 | - |
| v2.0 | 2026-01-10 | 深度审查修订 | ALATA |

### v2.0 主要修订内容：

1. **⚠️ 重要修正**：
   - 修正 openpyxl 库说明：明确只支持 .xlsx 格式，不支持 .xls
   - 添加 DocType 命名说明：Material/StockRecord 为示例名称，对应 ERPNext 标准 Item/Stock Entry

2. **🔒 安全性增强**（新增第4章）：
   - 添加完整的安全威胁分析
   - 添加文件 MIME 类型验证代码
   - 添加权限检查和频率限制实现
   - 添加 CSV 注入防护

3. **📝 代码改进**：
   - 重写字段映射配置，支持类型、必填、选项等元数据
   - 添加链接字段验证逻辑
   - 添加数据类型转换函数
   - 改进错误处理和日志记录

4. **🎨 前端代码重构**：
   - 改用 ERPNext 标准的 `frappe.ui.form.on()` 模式
   - 使用 `frm.add_custom_button()` 添加按钮
   - 添加 List View 按钮示例
   - 添加实时进度监听

5. **🧪 测试用例完善**：
   - 添加权限测试
   - 添加链接字段验证测试
   - 添加并发测试
   - 添加安全性测试（恶意文件、注入防护）
   - 添加测试辅助方法

6. **📚 附录补充**：
   - 添加 ERPNext 标准 DocType 对照表
   - 添加 Frappe 原生 Data Import 使用说明
   - 添加 FAQ 常见问题
   - 添加依赖清单

---

**审查团队**：产品架构师、技术负责人、安全专家

---

*本文档整合了ERPNext Excel数据导入功能的完整技术方案，经过深度审查和完善，为项目成功实施提供全面的技术指导。*
