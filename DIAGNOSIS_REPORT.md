# AMLO系统诊断报告

**诊断日期**: 2025-10-28
**问题**:
1. CTR触发条件不正确
2. PDF生成成功但内容为空

---

## 🔍 问题1: CTR触发条件分析

### 发现的规则配置

数据库中存在**5条**AMLO触发规则：

#### AMLO-1-01 (CTR) 规则：2条

**规则13**: AMLO-1-01单笔大额 (优先级100)
```json
{
  "logic": "AND",
  "conditions": [{
    "field": "total_amount",
    "operator": ">=",
    "value": 5000000  // 500万THB ❌ 错误！标准应为200万
  }]
}
```

**规则16**: AMLO-1-01高风险组合 (优先级110 - 更高)
```json
{
  "logic": "OR",
  "conditions": [
    {
      "logic": "AND",
      "conditions": [
        {"field": "total_amount", "operator": ">=", "value": 1000000},  // 100万
        {"field": "customer_age", "operator": ">=", "value": 65}        // 65岁
      ]
    },
    {
      "logic": "AND",
      "conditions": [
        {"field": "total_amount", "operator": ">=", "value": 1500000},  // 150万 ⚠️
        {"field": "payment_method", "operator": "==", "value": "cash"}   // 现金支付
      ]
    }
  ]
}
```

### 🚨 问题所在

**您的交易**: 1,948,299 THB

**触发原因**: 规则16的第二个条件组

```
条件: total_amount >= 1,500,000 AND payment_method == 'cash'
```

如果 `payment_method == 'cash'`，则会触发！

**分析**:
- ✅ 1,948,299 >= 1,500,000 (满足)
- ❓ payment_method == 'cash' (需要检查)

### ✅ 解决方案

#### 方案1: 删除规则16（推荐）

规则16是一个**非标准规则**，应该删除：

```sql
DELETE FROM trigger_rules WHERE id = 16;
```

#### 方案2: 修改规则16的阈值

将150万改为200万：

```sql
UPDATE trigger_rules
SET rule_expression = JSON_SET(
    rule_expression,
    '$.conditions[1].conditions[0].value',
    2000000
)
WHERE id = 16;
```

#### 方案3: 禁用规则16

```sql
UPDATE trigger_rules SET is_active = 0 WHERE id = 16;
```

#### 方案4: 重新配置所有规则（最推荐）

运行标准配置脚本：

```bash
python src/migrations/configure_amlo_trigger_rules.py
```

这会：
1. 删除所有旧规则（包括规则16）
2. 创建标准的CTR规则：`total_amount >= 2,000,000`

---

### 📊 标准规则应该是

| 报告类型 | 条件 | 阈值 |
|---------|------|------|
| AMLO-1-01 (CTR) | single_amount >= | 2,000,000 THB |
| AMLO-1-02 (ATR) | single_amount >= AND asset_backed | 8,000,000 THB |
| AMLO-1-03 (STR) | cumulative_30d >= | 5,000,000 THB |

---

## 🔍 问题2: PDF内容为空

### 可能的原因

根据代码分析，PDF生成流程是：

```
1. app_amlo.py (路由)
   ↓
2. AMLOPDFService.generate_pdf_from_reservation()
   ↓
3. AMLODataMapper.map_reservation_to_pdf_fields()  ← 映射业务数据到PDF字段
   ↓
4. AMLOPDFFiller.fill_form()  ← 填充PDF
   ↓
5. 使用CSV映射填充字段
```

### 需要检查的点

#### 检查点1: 数据映射是否正确

**问题**: `AMLODataMapper._map_101_fields()` 是否正确映射了字段？

**检查方法**: 查看后端日志中的：
```
[AMLODataMapper] Mapping fields for AMLO-1-01
[AMLODataMapper] Mapped XX fields
```

#### 检查点2: CSV字段映射是否加载

**问题**: `AMLOCSVFieldLoader` 是否成功加载了 `1-01-field-map.csv`？

**检查方法**: 查看日志中的：
```
[AMLOCSVFieldLoader] Loaded AMLO-1-01: XX fields
```

#### 检查点3: PDF字段填充是否成功

**问题**: `AMLOPDFFiller._fill_pdf_fields()` 是否成功填充了字段？

**检查方法**: 查看日志中的：
```
[AMLOPDFFiller] Filled field: fill_52 = 001-001-68-100055USD
[AMLOPDFFiller] Filled field: comb_1 = 1234567890123
...
[AMLOPDFFiller] Filled XX fields
```

#### 检查点4: PDF模板字段名称匹配

**最可能的问题**:
- CSV中的 `field_name` (如 `fill_52`, `comb_1`)
- 与PDF模板中的实际字段名称不匹配

**检查方法**:

1. 读取PDF模板的字段列表：

```python
from PyPDF2 import PdfReader

reader = PdfReader('D:\\Code\\ExchangeNew\\Re\\1-01-fill.pdf')
if reader.get_fields():
    print("PDF表单字段:")
    for field_name, field in reader.get_fields().items():
        print(f"  {field_name}: {field.get('/FT', '?')}")
else:
    print("⚠️  PDF没有表单字段！")
```

2. 对比CSV中的字段名：

```bash
# 查看CSV中的所有field_name
cat Re/1-01-field-map.csv | cut -d',' -f1 | sort | uniq
```

### 🚨 关键问题假设

**最可能的原因**:
1. PDF模板 `1-01-fill.pdf` 中的字段名与CSV不匹配
2. 或者PDF根本没有可编辑的表单字段

**验证方法**:

运行以下脚本检查PDF字段：

```bash
python scripts/inspect_pdf_fields.py Re/1-01-fill.pdf
```

---

## 🔧 诊断脚本

我将创建以下诊断脚本：

### 1. `check_pdf_fields.py`
检查PDF模板的表单字段

### 2. `check_mapping_flow.py`
跟踪整个数据映射流程

### 3. `test_pdf_generation.py`
端到端测试PDF生成

---

## 📋 下一步行动

### 立即执行

1. ✅ **修复CTR触发规则**:
   ```bash
   python src/migrations/configure_amlo_trigger_rules.py
   ```

2. ⏳ **检查PDF字段**:
   ```bash
   python scripts/inspect_pdf_fields.py Re/1-01-fill.pdf
   ```

3. ⏳ **测试PDF生成流程**:
   - 重新生成PDF
   - 查看后端完整日志
   - 检查是否有 `[AMLOPDFFiller] Filled field: ...` 日志

### 需要提供的信息

为了诊断PDF问题，请提供：

1. **后端生成PDF时的完整日志**（包括所有 `[AMLO*]` 开头的日志）

2. **PDF模板文件信息**:
   ```bash
   # 文件是否存在
   dir D:\Code\ExchangeNew\Re\1-01-fill.pdf

   # 文件大小
   ```

3. **CSV映射文件前几行**:
   ```bash
   head -20 D:\Code\ExchangeNew\Re\1-01-field-map.csv
   ```

---

## 🎯 总结

### 问题1: CTR触发条件
- **原因**: 规则16设置了150万阈值
- **修复**: 删除规则16或重新配置标准规则
- **命令**: `python src/migrations/configure_amlo_trigger_rules.py`

### 问题2: PDF内容为空
- **可能原因**: PDF字段名不匹配或映射失败
- **需要**: 查看后端日志确认具体原因
- **检查**: PDF模板是否有表单字段

---

**下一步**: 请运行修复命令并提供后端日志
