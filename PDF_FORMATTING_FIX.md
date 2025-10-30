# PDF格式修复 - 报告编号和复选框

**日期**: 2025-10-28
**修复文件**: `src/services/pdf/amlo_pdf_filler_pymupdf.py`

---

## 问题1: 报告编号字符挤在一起

### 问题描述
报告编号 `001-001-68-100071USD` 在PDF中显示为连续文本，没有分散到各个字符框中。

### 原因
Comb字段（组合字段）是一种特殊的文本字段，有多个独立的字符框。默认填充会把整个字符串放在第一个框中。

### 解决方案
在字符之间添加空格，让PyMuPDF将每个字符分配到对应的框中。

**修复代码** (lines 150-155):
```python
# 检查是否是comb字段（组合框 - 每个字符一个框）
if field_type == 'comb' or 'comb' in field_name.lower():
    # 在每个字符之间添加空格，分散到各个框中
    str_value = ' '.join(str_value)
    # "001-001-68-100071USD" → "0 0 1 - 0 0 1 - 6 8 - 1 0 0 0 7 1 U S D"
```

### 预期效果
```
修复前: [001-001-68-100071USD              ]
修复后: [0][0][1][-][0][0][1][-][6][8][-][1][0][0][0][7][1][U][S][D]
```

### 影响字段
- `comb_1`: 身份证号字段
- `comb_3`: 其他组合字段
- `comb_5`: 其他组合字段
- 所有包含 "comb" 的字段名

---

## 问题2: 复选框显示星号而不是勾选标记

### 问题描述
复选框被选中时显示为星号 `*`，而不是标准的勾选标记 `✓`。

### 原因
PyMuPDF的checkbox需要使用字符串值 `"Yes"` 或 `"Off"`，而不是布尔值 `True`/`False`。

### 解决方案
将布尔值转换为PyMuPDF期望的字符串格式。

**修复代码** (lines 162-170):
```python
elif widget.field_type == fitz.PDF_WIDGET_TYPE_CHECKBOX:
    # 复选框 - 使用字符串 "Yes" 或 "Off"
    if value in (True, 'true', '1', 1, 'yes', 'Yes', '/Yes'):
        widget.field_value = "Yes"  # ✓ 显示勾选标记
    else:
        widget.field_value = "Off"  # 空白
    widget.update()
```

### 预期效果
```
修复前: [*] 报告原版    [ ] 报告修订版
修复后: [✓] 报告原版    [ ] 报告修订版
```

### 影响字段
- `Check Box2`: 报告原版
- `Check Box3`: 报告修订版
- `Check Box4` ~ `Check Box33`: 所有复选框字段

---

## 技术细节

### PyMuPDF Checkbox值规范
| 输入值 | widget.field_value | PDF显示 |
|--------|-------------------|---------|
| True (布尔) | "Yes" | ✓ |
| False (布尔) | "Off" | 空白 |
| ~~True~~ | ~~True~~ | ~~*（错误）~~ |

### Comb字段处理逻辑
1. 检测comb字段（通过字段类型或字段名）
2. 将字符串转换为带空格的格式：`' '.join(str_value)`
3. PyMuPDF自动将每个字符（包括空格）分配到对应的框
4. 空格占用一个框但不显示，造成字符分散效果

---

## 测试检查清单

### 报告编号字段测试
- [ ] `fill_52` (报告编号): 字符是否分散在各个框中？
- [ ] `comb_1` (身份证号): 数字是否均匀分布？
- [ ] 字符之间是否有适当的间距？
- [ ] 特殊字符（如 `-`）是否正确显示？

### 复选框测试
- [ ] `Check Box2` (报告原版=True): 显示 ✓
- [ ] `Check Box3` (报告修订版=False): 显示空白
- [ ] `Check Box4` (交易人类别): 根据数据正确显示
- [ ] 所有复选框都显示为勾选标记，而不是星号

### 预期日志
```
[AMLOPDFFillerPyMuPDF] COMB field detected: comb_1, spacing characters
[AMLOPDFFillerPyMuPDF] Filled TEXT field: comb_1 = 111234567890
[AMLOPDFFillerPyMuPDF] Filled CHECKBOX field: Check Box2 = Yes
[AMLOPDFFillerPyMuPDF] Filled CHECKBOX field: Check Box3 = Off
```

---

## 重启测试步骤

```bash
# 1. 重启后端
python src/main.py

# 2. 访问AMLO预约审核页面
# http://192.168.0.9:8080/amlo/reservations

# 3. 生成新的PDF报告

# 4. 检查PDF:
#    - 报告编号字符是否分散？
#    - 复选框是否显示为 ✓ ？
```

---

## 修改摘要

**文件**: `src/services/pdf/amlo_pdf_filler_pymupdf.py`

**修改位置**:
- Lines 150-155: 添加comb字段字符间距处理
- Lines 162-170: 修复复选框值为字符串格式

**新增逻辑**:
1. Comb字段检测和空格插入
2. Checkbox字符串值转换

**向后兼容**: ✅ 不影响其他字段类型

---

## 相关字段列表

### Comb字段（需要字符间距）
- `comb_1`: 身份证号 (13位)
- `comb_3`: 其他组合字段
- `comb_5`: 其他组合字段

### Checkbox字段（需要勾选标记）
- `Check Box2`: 报告原版
- `Check Box3`: 报告修订版
- `Check Box4`: 个人
- `Check Box5`: 法人
- `Check Box6` ~ `Check Box9`: 交易人类别
- `Check Box18` ~ `Check Box33`: 其他选项

---

**修复状态**: ✅ 已完成
**待测试**: ⏳ 需要重启后端验证
