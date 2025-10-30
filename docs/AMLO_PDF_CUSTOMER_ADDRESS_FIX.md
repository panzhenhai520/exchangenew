# AMLO PDF customer_address字段修复

**修复日期**: 2025-10-28
**问题**: 数据库中不存在customer_address字段
**状态**: ✅ 已修复

---

## 问题描述

### 错误信息

```
Unknown column 'r.customer_address' in 'field list'
```

### 错误原因

`Reserved_Transaction` 表中**没有** `customer_address` 字段，但SQL查询尝试读取该字段。

---

## 修复内容

### 文件: `src/routes/app_amlo.py`

#### 修复1: 移除SQL查询中的customer_address

**位置**: 行 1065-1077

**修改前**:
```python
report_sql = text("""
    SELECT
        r.id, r.reservation_no, r.report_type, r.customer_id, r.customer_name,
        r.customer_address, r.currency_id, r.direction, r.amount, r.local_amount,  # ❌ 字段不存在
        ...
""")
```

**修改后**:
```python
report_sql = text("""
    SELECT
        r.id, r.reservation_no, r.report_type, r.customer_id, r.customer_name,
        r.currency_id, r.direction, r.amount, r.local_amount,  # ✅ 移除customer_address
        ...
""")
```

---

#### 修复2: 移除reservation_data中的customer_address

**位置**: 行 1135-1148

**修改前**:
```python
reservation_data = {
    'id': result.id,
    'reservation_no': result.reservation_no,
    'report_type': result.report_type,
    'customer_id': result.customer_id,
    'customer_name': result.customer_name,
    'customer_address': result.customer_address,  # ❌ 字段不存在
    'currency_code': result.currency_code,
    ...
}
```

**修改后**:
```python
reservation_data = {
    'id': result.id,
    'reservation_no': result.reservation_no,
    'report_type': result.report_type,
    'customer_id': result.customer_id,
    'customer_name': result.customer_name,
    # ✅ 移除customer_address，地址从form_data中获取
    'currency_code': result.currency_code,
    ...
}
```

---

## 数据来源说明

### customer_address应该从哪里获取？

`Reserved_Transaction` 表中的 `form_data` 字段（JSON格式）包含完整的表单数据，其中包括地址信息：

```json
{
  "maker_address_number": "Jingui Building, Futian District, Shenzhen, Guangdong Province",
  "maker_address_village": "",
  "maker_address_lane": "",
  "maker_address_road": "Jingui Building",
  "maker_address_subdistrict": "Futian District",
  "maker_address_district": "Shenzhen",
  "maker_address_province": "Guangdong Province",
  "maker_address_postalcode": ""
}
```

**正确做法**:
- ✅ 从 `form_data` JSON中提取地址字段
- ✅ 组合成完整地址字符串
- ✅ 填写到PDF相应字段

**代码示例**:
```python
import json

form_data = json.loads(result.form_data)

# 组合地址
address_parts = [
    form_data.get('maker_address_number', ''),
    form_data.get('maker_address_village', ''),
    form_data.get('maker_address_lane', ''),
    form_data.get('maker_address_road', ''),
    form_data.get('maker_address_subdistrict', ''),
    form_data.get('maker_address_district', ''),
    form_data.get('maker_address_province', ''),
    form_data.get('maker_address_postalcode', '')
]

full_address = ' '.join(filter(None, address_parts))
```

---

## 测试步骤

### 1. 重启后端服务

```bash
# Ctrl+C 停止当前服务
python src/main.py
```

### 2. 测试PDF生成

1. 进入 **AMLO审计** → **预约审核**
2. 找到预约记录 ID: **54**
3. 点击 **"查看PDF"** 按钮

### 3. 预期结果

**终端应该显示**:
```
================================================================================
[AMLO PDF STEP 1] 收到PDF生成请求
[AMLO PDF] 报告ID: 54
================================================================================

[AMLO PDF STEP 2] 数据库会话已创建
[AMLO PDF STEP 3] 开始查询数据库...
[AMLO PDF STEP 4] 数据库查询完成  ✅ 不再报错
[AMLO PDF] 查询结果: 找到记录
[AMLO PDF] 报告类型: AMLO-1-01
[AMLO PDF] 预约编号: 001-001-68-100055USD
...
```

**不应该再看到**:
```
❌ Unknown column 'r.customer_address' in 'field list'
```

---

## 相关修复

### 之前已修复的类似问题

1. **`reporter_id` 字段不存在** (`app_amlo.py:734`)
   - 状态: ✅ 已在之前修复

2. **`customer_address` 字段不存在** (`app_amlo.py:1065-1077`)
   - 状态: ✅ 本次修复

---

## 数据库表结构确认

### Reserved_Transaction 表实际字段

从测试日志可以看出，该表**有**以下字段：
- `id`
- `reservation_no`
- `report_type`
- `customer_id`
- `customer_name`
- `currency_id`
- `direction`
- `amount`
- `local_amount`
- `transaction_date`
- `form_data` (JSON)
- `created_at`
- `branch_id`

### Reserved_Transaction 表**没有**以下字段

- ❌ `customer_address` (地址在form_data中)
- ❌ `amount_thb` (使用local_amount)
- ❌ `reporter_id` (已在之前修复)

---

## 下一步

修复完成后，PDF生成应该能进行到下一步。可能遇到的下一个问题：

1. **PDF模板文件不存在**
   - 文件: `D:\Code\ExchangeNew\Re\1-01-fill.pdf`
   - 解决: 确保文件存在

2. **CSV字段映射文件不存在**
   - 文件: `D:\Code\ExchangeNew\Re\1-01-field-map.csv`
   - 解决: 确保文件存在

3. **form_data解析错误**
   - 确保form_data是有效的JSON
   - 确保包含所需字段

---

**修复人员**: Claude Code Assistant
**修复日期**: 2025-10-28
**状态**: ✅ 已完成，待测试验证
