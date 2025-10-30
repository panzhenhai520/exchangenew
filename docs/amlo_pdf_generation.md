# AMLO PDF报告自动生成系统

## 概述

本系统实现了基于CSV字段映射的AMLO合规报告PDF自动生成功能。系统根据`Re/`目录下的CSV字段映射文件，将业务数据自动填充到PDF模板表单中。

### 支持的报告类型

- **AMLO-1-01**: 现金交易报告 (Cash Transaction Report, CTR)
- **AMLO-1-02**: 资产交易报告 (Asset Transaction Report, ATR)
- **AMLO-1-03**: 可疑交易报告 (Suspicious Transaction Report, STR)

## 架构设计

### 核心组件

```
┌─────────────────────────────────────────────────────────┐
│                  AMLO PDF生成系统                        │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  ┌────────────────────────────────────────────────┐    │
│  │  1. AMLOCSVFieldLoader (CSV字段加载器)         │    │
│  │     - 加载 Re/1-01-field-map.csv               │    │
│  │     - 加载 Re/1-02-field-map.csv               │    │
│  │     - 加载 Re/1-03-field-map.csv               │    │
│  │     - 提供字段元数据查询接口                    │    │
│  └────────────────────────────────────────────────┘    │
│                          ↓                              │
│  ┌────────────────────────────────────────────────┐    │
│  │  2. AMLODataMapper (业务数据映射器)             │    │
│  │     - 从Reserved_Transaction提取数据            │    │
│  │     - 从form_data JSON解析表单数据              │    │
│  │     - 根据nearby_th_label映射到PDF字段          │    │
│  │     - 处理日期、地址、姓名等复杂字段            │    │
│  └────────────────────────────────────────────────┘    │
│                          ↓                              │
│  ┌────────────────────────────────────────────────┐    │
│  │  3. AMLOPDFFiller (PDF表单填充器)               │    │
│  │     - 使用PyPDF2填充PDF表单字段                 │    │
│  │     - 支持文本字段、复选框、组合字段            │    │
│  │     - 保持PDF原始格式和样式                     │    │
│  └────────────────────────────────────────────────┘    │
│                          ↓                              │
│  ┌────────────────────────────────────────────────┐    │
│  │  4. AMLOPDFService (集成服务)                   │    │
│  │     - 统一的高级API接口                         │    │
│  │     - 支持从数据库记录生成PDF                   │    │
│  │     - 自动创建输出目录                          │    │
│  │     - 规范化文件命名                            │    │
│  └────────────────────────────────────────────────┘    │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

### 文件结构

```
D:\Code\ExchangeNew\
│
├── Re/                                  # CSV映射和PDF模板
│   ├── 1-01-field-map.csv              # AMLO-1-01字段映射 (93字段)
│   ├── 1-02-field-map.csv              # AMLO-1-02字段映射 (90字段)
│   ├── 1-03-field-map.csv              # AMLO-1-03字段映射 (92字段)
│   ├── 1-01-fill.pdf                   # AMLO-1-01 PDF模板
│   ├── 1-02-fill.pdf                   # AMLO-1-02 PDF模板
│   └── 1-03-fill.pdf                   # AMLO-1-03 PDF模板
│
└── src/services/pdf/                    # PDF生成服务
    ├── __init__.py                      # 模块导出
    ├── amlo_csv_field_loader.py         # CSV字段加载器
    ├── amlo_data_mapper.py              # 业务数据映射器
    ├── amlo_pdf_filler_v2.py            # PDF填充器
    └── amlo_pdf_service.py              # 集成服务

```

## CSV字段映射格式

### CSV文件格式

```csv
page,field_name,type,nearby_th_label
1,fill_52,text,สถาบันการเงิน-สาขา-ใช้ ๒ หลักสุด. ท้าย-เลขลำดับรายงาน
1,Check Box2,checkbox,รายงานฉบับหลัก
1,comb_1,text,交易办理人身份证号码
1,fill_4,text,๑.๑ ชื่อ-นามสกุล
...
```

### 字段类型说明

| 类型 | 说明 | 示例 |
|------|------|------|
| `text` | 文本字段 | 姓名、地址、电话 |
| `checkbox` | 复选框 | 报告类型选择、证件类型选择 |
| `comb` | 组合字段 | 身份证号码的单字符框 |

### nearby_th_label说明

`nearby_th_label`字段包含PDF表单中该字段附近的泰文标签，用于理解字段含义和业务逻辑映射。

## 使用方法

### 方法1: 快捷函数（推荐）

```python
from services.db_service import DatabaseService
from services.pdf import generate_amlo_pdf

# 从预约记录ID生成PDF
with DatabaseService.get_session() as session:
    pdf_path = generate_amlo_pdf(
        reservation_id=123,
        db_session=session,
        output_dir='/path/to/output'  # 可选，默认为 src/amlo_reports/YYYY/MM/
    )

print(f"PDF已生成: {pdf_path}")
```

### 方法2: 使用服务类

```python
from services.pdf import AMLOPDFService
from services.db_service import DatabaseService

service = AMLOPDFService()

# 从数据库记录生成
with DatabaseService.get_session() as session:
    pdf_path = service.generate_pdf_from_db(
        db_session=session,
        reservation_id=123,
        output_dir='/custom/path'
    )
```

### 方法3: 直接使用预约数据

```python
from services.pdf import AMLOPDFService
from datetime import datetime

service = AMLOPDFService()

reservation_data = {
    'report_type': 'AMLO-1-01',
    'reservation_no': 'FI-001-68-001',
    'customer_id': '1234567890123',
    'customer_name': 'นายสมชาย ใจดี',
    'customer_address': '123 ถนนสุขุมวิท...',
    'direction': 'buy',  # 'buy' 或 'sell'
    'currency_code': 'USD',
    'local_amount': 2500000,  # THB金额
    'amount': 75000,  # 外币金额
    'transaction_date': datetime(2025, 10, 18),
    'form_data': {
        'maker_phone': '02-1234567',
        'maker_occupation': 'ธุรกิจส่วนตัว',
        'transaction_purpose': 'เพื่อการท่องเที่ยว',
        ...
    }
}

pdf_path = service.generate_pdf_from_reservation(
    reservation_data,
    output_path='/path/to/output.pdf'
)
```

## 业务数据到PDF字段的映射

### 交易办理人信息 (第1部分)

| PDF字段 | 业务数据来源 | 说明 |
|---------|-------------|------|
| `fill_52` | `reservation_no` | 报告编号 |
| `Check Box2` | `!is_amendment_report` | 原报告 |
| `Check Box3` | `is_amendment_report` | 修订报告 |
| `comb_1` | `maker_id_number` 或 `customer_id` | 身份证号 |
| `fill_4` | 组合自 `maker_title`, `maker_firstname`, `maker_lastname` | 姓名 |
| `fill_5`, `fill_5_2` | 组合自 `maker_address_*` 字段 | 地址 |
| `fill_7` | `maker_phone` 或 `maker_mobile` | 电话 |
| `fill_9` | `maker_occupation` | 职业 |
| `Check Box6-9` | `maker_id_type` | 证件类型 |

### 交易信息 (第3部分)

| PDF字段 | 业务数据来源 | 说明 |
|---------|-------------|------|
| `fill_37`, `fill_38`, `fill_39` | `transaction_date` | 交易日期(日/月/佛历年) |
| `fill_48` | `local_amount` (买入时) | 本币金额 |
| `fill_49` | `local_amount` (卖出时) | 本币金额 |
| `Check Box23` | `direction=='buy'` | 买入外币 |
| `Check Box30` | `direction=='sell'` | 卖出外币 |
| `fill_42` | `currency_code` | 外币币种 |
| `fill_46` | `beneficiary_name` | 受益人 |
| `fill_47` | `transaction_purpose` | 交易目的 |

## 输出规范

### 默认输出路径

```
src/amlo_reports/
└── YYYY/              # 年份
    └── MM/            # 月份
        ├── AMLO-1-01_FI-001-68-001.pdf
        ├── AMLO-1-01_FI-001-68-002.pdf
        └── ...
```

### 文件命名规则

```
{report_type}_{reservation_no}.pdf
```

示例:
- `AMLO-1-01_FI-001-68-001.pdf`
- `AMLO-1-02_FI-001-68-005.pdf`

## API路由集成

### 添加PDF生成端点

在 `src/routes/app_amlo.py` 中添加:

```python
@app_amlo.route('/reservation/<int:reservation_id>/generate-pdf', methods=['POST'])
@token_required
def generate_reservation_pdf(current_user, reservation_id):
    """
    生成预约记录的AMLO PDF报告

    POST /api/amlo/reservation/123/generate-pdf

    Returns:
    {
        "success": true,
        "pdf_path": "/path/to/AMLO-1-01_FI-001-68-001.pdf",
        "pdf_url": "/static/amlo_reports/2025/10/AMLO-1-01_FI-001-68-001.pdf"
    }
    """
    from services.pdf import generate_amlo_pdf
    from services.db_service import DatabaseService

    try:
        with DatabaseService.get_session() as session:
            pdf_path = generate_amlo_pdf(reservation_id, session)

            # 转换为Web可访问路径
            pdf_url = pdf_path.replace('\\', '/').replace('src/', '/static/')

            return jsonify({
                'success': True,
                'pdf_path': pdf_path,
                'pdf_url': pdf_url
            })

    except Exception as e:
        return jsonify({
            'success': False,
            'message': str(e)
        }), 500
```

## 测试

### 单元测试

```bash
# 测试CSV字段加载器
cd src/services/pdf
python amlo_csv_field_loader.py

# 测试PDF填充器
python amlo_pdf_filler_v2.py

# 测试数据映射器
python amlo_data_mapper.py

# 测试集成服务
python amlo_pdf_service.py
```

### 预期输出

```
[AMLOCSVFieldLoader] Loaded AMLO-1-01: 93 fields
[AMLOCSVFieldLoader] Loaded AMLO-1-02: 90 fields
[AMLOCSVFieldLoader] Loaded AMLO-1-03: 92 fields
[AMLOPDFService] Generating AMLO-1-01 PDF
[AMLOPDFService] Mapped 44 fields
[AMLOPDFFiller] Filled 88 fields
[AMLOPDFService] PDF generated successfully: output.pdf
```

## 故障排查

### 常见问题

#### 1. 找不到CSV文件

**错误**: `Warning: D:\Code\ExchangeNew\Re\1-01-field-map.csv not found`

**解决**: 确保CSV文件位于 `D:\Code\ExchangeNew\Re\` 目录

#### 2. 找不到PDF模板

**错误**: `Template not found: D:\Code\ExchangeNew\Re\1-01-fill.pdf`

**解决**: 确保PDF模板文件存在于 `Re/` 目录

#### 3. 字段填充失败

**错误**: `Error filling field: ...`

**解决**:
- 检查PDF模板是否有对应的表单字段
- 使用 `PdfReader` 验证字段名称:
  ```python
  from PyPDF2 import PdfReader
  r = PdfReader('Re/1-01-fill.pdf')
  print(list(r.get_fields().keys()))
  ```

#### 4. 泰文显示问题

**症状**: 控制台显示泰文编码错误

**说明**: 这是Windows控制台编码问题，不影响PDF生成。PDF中的泰文可以正常显示。

## 扩展功能

### 添加1-02和1-03表单支持

在 `amlo_data_mapper.py` 中实现:

```python
def _map_102_fields(self, reservation_data: Dict, form_data: Dict) -> Dict:
    """映射AMLO-1-02 (ATR) 字段"""
    pdf_fields = {}

    # 报告编号
    pdf_fields['fill_52'] = reservation_data.get('reservation_no', '')

    # 资产类型 (Check Box50-57)
    asset_type = form_data.get('asset_type', 'land')
    pdf_fields['Check Box50'] = (asset_type == 'mortgage')
    pdf_fields['Check Box54'] = (asset_type == 'land')
    # ... 更多字段映射

    return pdf_fields
```

### 自定义字段映射

创建自定义映射规则:

```python
from services.pdf import AMLODataMapper

class CustomAMLODataMapper(AMLODataMapper):
    def _map_101_fields(self, reservation_data, form_data):
        # 调用父类方法
        pdf_fields = super()._map_101_fields(reservation_data, form_data)

        # 添加自定义映射
        pdf_fields['custom_field'] = form_data.get('custom_value', '')

        return pdf_fields
```

## 性能优化

### 批量生成PDF

```python
from services.pdf import AMLOPDFService
from services.db_service import DatabaseService

service = AMLOPDFService()

reservation_ids = [123, 124, 125, 126]

with DatabaseService.get_session() as session:
    for res_id in reservation_ids:
        try:
            pdf_path = service.generate_pdf_from_db(session, res_id)
            print(f"✓ {res_id}: {pdf_path}")
        except Exception as e:
            print(f"✗ {res_id}: {e}")
```

## 参考资料

- [PyPDF2 文档](https://pypdf2.readthedocs.io/)
- [AMLO 报告规范](https://www.amlo.go.th/)
- CSV字段映射文件: `Re/1-01-field-map.csv`, `Re/1-02-field-map.csv`, `Re/1-03-field-map.csv`
- PDF模板文件: `Re/1-01-fill.pdf`, `Re/1-02-fill.pdf`, `Re/1-03-fill.pdf`

## 更新日志

### 2025-10-28

- ✅ 实现CSV字段映射加载器 (`amlo_csv_field_loader.py`)
- ✅ 实现PDF表单填充器 (`amlo_pdf_filler_v2.py`)
- ✅ 实现业务数据映射器 (`amlo_data_mapper.py`)
- ✅ 实现集成服务 (`amlo_pdf_service.py`)
- ✅ 完成AMLO-1-01表单的完整映射 (88字段自动填充)
- ✅ 测试通过,成功生成PDF报告

### 待开发

- ⏳ AMLO-1-02 (ATR) 完整映射
- ⏳ AMLO-1-03 (STR) 完整映射
- ⏳ 与前端审核流程集成
- ⏳ PDF预览功能
- ⏳ PDF下载接口
