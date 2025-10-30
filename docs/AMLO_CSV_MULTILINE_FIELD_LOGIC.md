# AMLO CSV字段多行填写逻辑说明

**创建日期**: 2025-10-28
**重要性**: ⭐⭐⭐⭐⭐ (关键业务逻辑)

---

## 📋 用户需求说明

### 核心规则

CSV字段映射文件中，当多个 `field_name` 对应**相同的** `nearby_th_label` 时，表示PDF模板中该字段有**多行填写区域**。

---

## 🔍 具体示例

### 示例1: 地址字段多行填写

**文件**: `Re/1-01-field-map.csv`

| field_name | field_type | nearby_th_label | x | y | width | height |
|------------|------------|-----------------|---|---|-------|--------|
| fill_5     | text       | ๑.๒ ที่อยู่     | 100 | 200 | 400 | 20 |
| fill_5_2   | text       | ๑.๒ ที่อยู่     | 100 | 220 | 400 | 20 |

**说明**:
- `๑.๒ ที่อยู่` (地址字段) 在PDF模板 `1-01-fill.pdf` 中有**两行**填写区域
- **第一行**: `fill_5` (位于 y=200)
- **第二行**: `fill_5_2` (位于 y=220)

**填写逻辑**:
```
1. 从表单中获取 ๑.๒ ที่อยู่ 的值
2. 优先填写第一行 (fill_5)
3. 如果第一行不够，自动折行到第二行 (fill_5_2)
```

---

### 示例2: Checkbox + Fill组合

**CSV示例**:

| field_name | field_type | nearby_th_label | x | y | width | height |
|------------|------------|-----------------|---|---|-------|--------|
| checkbox_10 | checkbox  | ๒.๓ อาชีพ      | 50 | 300 | 20 | 20 |
| fill_10     | text      | ๒.๓ อาชีพ      | 80 | 300 | 200 | 20 |

**说明**:
- `๒.๓ อาชีพ` (职业字段) 既有checkbox又有填写框
- **先勾选checkbox** (`checkbox_10`)
- **然后填写具体内容** (`fill_10`)

**填写逻辑**:
```
1. 如果表单中有 ๒.๓ อาชีพ 的值
2. 勾选 checkbox_10 ✓
3. 在 fill_10 中填写具体的职业内容
```

---

## 🎯 字段匹配规则

### 规则1: 多行文本字段识别

**特征**: 多个 `field_name` 有相同的 `nearby_th_label`

**命名模式**:
- 主字段: `fill_5`
- 第二行: `fill_5_2` (后缀 `_2`)
- 第三行: `fill_5_3` (后缀 `_3`)
- 以此类推...

**处理逻辑**:
```python
def fill_multiline_field(field_label, content, field_mappings):
    """
    填写多行字段

    Args:
        field_label: 字段标签 (如 "๑.๒ ที่อยู่")
        content: 要填写的内容 (可能很长)
        field_mappings: 从CSV加载的所有字段映射
    """
    # 1. 找出所有匹配该标签的字段
    matching_fields = [
        field for field in field_mappings
        if field['nearby_th_label'] == field_label
        and field['field_type'] == 'text'
    ]

    # 2. 按field_name排序 (fill_5, fill_5_2, fill_5_3...)
    matching_fields.sort(key=lambda f: f['field_name'])

    # 3. 计算每行最大字符数
    for i, field in enumerate(matching_fields):
        max_chars = estimate_max_chars(field['width'], field['height'])

        if len(content) <= max_chars:
            # 当前行够用，直接填写
            fill_pdf_field(field['field_name'], content)
            break
        else:
            # 当前行不够，填满后继续下一行
            line_content = content[:max_chars]
            fill_pdf_field(field['field_name'], line_content)
            content = content[max_chars:]  # 剩余内容

    # 4. 如果所有行都填满了还有内容，截断（或报警）
    if content:
        logger.warning(f"字段 {field_label} 内容过长，已截断")
```

---

### 规则2: Checkbox + Fill 组合识别

**特征**: 相同 `nearby_th_label` 下同时有 `checkbox` 和 `text` 类型

**处理逻辑**:
```python
def fill_checkbox_with_text(field_label, value, field_mappings):
    """
    填写checkbox + 文本字段组合

    Args:
        field_label: 字段标签
        value: 要填写的值
        field_mappings: CSV字段映射
    """
    # 1. 找出checkbox字段
    checkbox_field = next(
        (f for f in field_mappings
         if f['nearby_th_label'] == field_label
         and f['field_type'] == 'checkbox'),
        None
    )

    # 2. 找出text字段
    text_field = next(
        (f for f in field_mappings
         if f['nearby_th_label'] == field_label
         and f['field_type'] == 'text'),
        None
    )

    # 3. 如果有值，先勾选checkbox
    if value and checkbox_field:
        check_pdf_checkbox(checkbox_field['field_name'], True)

    # 4. 然后填写text内容
    if value and text_field:
        fill_pdf_field(text_field['field_name'], value)
```

---

## 📝 实际应用示例

### 场景1: 地址很长，需要两行

**表单数据** (form_data):
```json
{
  "maker_address": "เลขที่ 123/45 หมู่บ้านสวนดอกไม้ ซอยร่มเกล้า 15 ถนนลาดพร้าว แขวงจันทรเกษม เขตจตุจักร กรุงเทพมหานคร 10900"
}
```

**CSV映射**:
```csv
field_name,field_type,nearby_th_label,x,y,width,height
fill_5,text,๑.๒ ที่อยู่,100,200,400,20
fill_5_2,text,๑.๒ ที่อยู่,100,220,400,20
```

**填写结果**:
- `fill_5`: "เลขที่ 123/45 หมู่บ้านสวนดอกไม้ ซอยร่มเกล้า 15 ถนนลาดพร้าว"
- `fill_5_2`: "แขวงจันทรเกษม เขตจตุจักร กรุงเทพมหานคร 10900"

---

### 场景2: 职业字段需要勾选+填写

**表单数据**:
```json
{
  "maker_occupation": "ค้าขาย"
}
```

**CSV映射**:
```csv
field_name,field_type,nearby_th_label,x,y,width,height
checkbox_10,checkbox,๒.๓ อาชีพ,50,300,20,20
fill_10,text,๒.๓ อาชีพ,80,300,200,20
```

**填写结果**:
- `checkbox_10`: ✓ (勾选)
- `fill_10`: "ค้าขาย"

---

## 🛠️ 实现要求

### 必须实现的功能

1. **✅ 识别多行字段**
   - 通过 `nearby_th_label` 分组
   - 识别 `_2`, `_3` 后缀

2. **✅ 自动折行**
   - 计算每行最大字符数
   - 超出时自动折行到下一个字段

3. **✅ Checkbox + Text 组合**
   - 有值时勾选checkbox
   - 同时填写text内容

4. **✅ 字符宽度估算**
   - 英文/数字: 1个字符
   - 泰文: 1.2个字符
   - 中文: 2个字符

5. **✅ 内容截断处理**
   - 超出所有行时记录警告
   - 可选：抛出异常或静默截断

---

## 📊 CSV文件结构分析

### 1-01-field-map.csv 关键字段

| nearby_th_label | field_name 列表 | 说明 |
|-----------------|----------------|------|
| ๑.๒ ที่อยู่ | fill_5, fill_5_2 | 地址2行 |
| ๒.๓ อาชีพ | checkbox_10, fill_10 | 职业checkbox+text |
| ๒.๗ ประเภทธุรกิจ | checkbox_15, fill_15 | 业务类型checkbox+text |

### 1-02-field-map.csv 关键字段

(类似结构，需要分析具体字段)

### 1-03-field-map.csv 关键字段

(类似结构，需要分析具体字段)

---

## 🔍 代码实现位置

### 需要修改的文件

1. **`src/services/pdf/amlo_csv_field_loader.py`**
   - 添加字段分组逻辑
   - 识别多行字段和组合字段

2. **`src/services/pdf/amlo_pdf_service.py`**
   - 实现多行填写逻辑
   - 实现checkbox+text组合逻辑

3. **`src/services/pdf/amlo_form_filler.py`** (如果使用)
   - 字符宽度估算
   - 自动折行算法

---

## ⚠️ 注意事项

### 字段顺序

**重要**: 多行字段必须按顺序填写
- ❌ 错误: fill_5_2 → fill_5 (逆序)
- ✅ 正确: fill_5 → fill_5_2 (顺序)

### 字符计算

**泰文字符特殊性**:
- 泰文有声调符号（อักษรสระและวรรณยุกต์）
- 某些字符可能占用额外宽度
- 需要测试实际PDF渲染效果

### PDF模板限制

**如果PDF模板中的字段没有足够高度**:
- 内容可能被截断
- 需要调整PDF模板或字体大小

---

## 🧪 测试用例

### 测试1: 单行够用

```python
content = "123 Main Street"
expected_result = {
    'fill_5': '123 Main Street',
    'fill_5_2': ''  # 不填写
}
```

### 测试2: 需要两行

```python
content = "เลขที่ 123/45 หมู่บ้านสวนดอกไม้ ซอยร่มเกล้า 15 ถนนลาดพร้าว แขวงจันทรเกษม เขตจตุจักร กรุงเทพมหานคร 10900"
expected_result = {
    'fill_5': 'เลขที่ 123/45 หมู่บ้านสวนดอกไม้ ซอยร่มเกล้า 15 ถนนลาดพร้าว',
    'fill_5_2': 'แขวงจันทรเกษม เขตจตุจักร กรุงเทพมหานคร 10900'
}
```

### 测试3: Checkbox + Text

```python
occupation = "ค้าขาย"
expected_result = {
    'checkbox_10': True,  # 勾选
    'fill_10': 'ค้าขาย'   # 填写
}
```

### 测试4: 内容超出所有行

```python
content = "很长很长很长的内容..." * 100
# 应该记录警告并截断
```

---

## 📚 参考资料

### CSV文件位置
- `D:\Code\ExchangeNew\Re\1-01-field-map.csv`
- `D:\Code\ExchangeNew\Re\1-02-field-map.csv`
- `D:\Code\ExchangeNew\Re\1-03-field-map.csv`

### PDF模板位置
- `D:\Code\ExchangeNew\Re\1-01-fill.pdf`
- `D:\Code\ExchangeNew\Re\1-02-fill.pdf`
- `D:\Code\ExchangeNew\Re\1-03-fill.pdf`

---

**重要提醒**:
- ⭐ 多行字段是AMLO报告的核心功能
- ⭐ CSV映射必须100%准确
- ⭐ 需要大量测试验证

**状态**: 📝 待实现
**优先级**: 🔥 高优先级

---

**创建人员**: Claude Code Assistant
**创建日期**: 2025-10-28
**下一步**: 实现多行字段填写逻辑
