# 报告编号跳号问题修复

**日期**: 2025-10-29
**问题**: AMLO报告编号跳过所有偶数（100071 → 100079, 跳过100078）
**根本原因**: 新旧两套序列系统同时使用，导致每个预约消耗2个序列号

---

## 问题分析

### 现象
Reserved_Transaction表中的所有reservation_no都是**奇数**:
```
100019, 100021, 100027, 100031, 100035, 100041, 100043, 100045, ...
100071, 100073, 100075, 100077, 100079
```

跳过所有偶数: 100020, 100022-100026, 100028-100030, 100078等

### 根本原因

系统中存在**两套不同的报告编号生成逻辑**：

1. **新系统** - `ReportNumberGenerator` (推荐使用)
   - 文件: `src/services/report_number_generator.py`
   - 数据表: `amlo_report_sequences` (使用 `year_month` VARCHAR(7) 字段)
   - API端点: `/api/report-numbers/amlo/generate`
   - 序列增长: `current_sequence += 1` (line 138)

2. **旧系统** - `ReportDataService._generate_reservation_no` (遗留代码)
   - 文件: `src/services/repform/report_data_service.py`
   - 数据表: `amlo_report_sequences` (使用 `sequence_date` DATE 字段)
   - 序列增长: `next_seq = (last_sequence or 0) + 1` (line 186)

### 双重消耗序列号的流程

#### 当前错误流程:

1. **前端** (`DynamicFormImproved.vue:277`):
   ```javascript
   const generatedReportNumber = await generateReportNumber()
   // 调用 POST /api/report-numbers/amlo/generate
   // → 新系统生成: 001-001-68-100071USD
   // → 序列号从 100071 增加到 100072 ✅
   data.report_number = generatedReportNumber
   ```

2. **前端** 提交表单:
   ```javascript
   await api.post('/repform/save-reservation', {
     ...data,
     form_data: {
       report_number: '001-001-68-100071USD',  // 已生成的编号
       ...其他字段
     }
   })
   ```

3. **后端** (`app_repform.py:475`):
   ```python
   reservation_id = ReportDataService.save_reservation(
       session,
       request_data  # request_data['form_data']['report_number'] = '001-001-68-100071USD'
   )
   ```

4. **后端** (`report_data_service.py:41`) - **问题所在**:
   ```python
   # 尝试从form_data中获取report_number
   reservation_no = reservation_data.get('form_data', {}).get('report_number')

   # ❌ BUG: 如果获取失败（例如form_data是字符串而不是dict）
   if not reservation_no:
       # 又生成一次！
       reservation_no = ReportDataService._generate_reservation_no(...)
       # → 旧系统生成: 001-001-68-100072
       # → 序列号从 100072 增加到 100073 ❌❌
   ```

5. **结果**:
   - 前端生成的 `100071` 被使用 ✅
   - 但序列号已经跳到 `100073` ❌
   - 下次生成时直接是 `100073`，`100072`永远被跳过

---

## 修复方案

### 修复 1: 改进 `report_data_service.py` 中的 `form_data` 解析

**文件**: `src/services/repform/report_data_service.py`
**位置**: `save_reservation()` 方法 (lines 40-64)

**修改前**:
```python
reservation_no = reservation_data.get('form_data', {}).get('report_number')

if not reservation_no:
    reservation_no = ReportDataService._generate_reservation_no(...)
```

**修改后**:
```python
# 获取form_data（可能是dict或JSON字符串）
form_data = reservation_data.get('form_data', {})

# 如果是字符串，先解析为dict
if isinstance(form_data, str):
    import json
    try:
        form_data = json.loads(form_data)
    except:
        form_data = {}

reservation_no = form_data.get('report_number')

if reservation_no:
    print(f"[ReportDataService] 使用前端已生成的报告编号: {reservation_no}")
else:
    print(f"[ReportDataService] 前端未提供报告编号，开始生成新编号...")
    print(f"[ReportDataService] form_data keys: {list(form_data.keys())}")
    reservation_no = ReportDataService._generate_reservation_no(...)
    print(f"[ReportDataService] 生成的新报告编号: {reservation_no}")
```

### 为什么这个修复有效?

1. **正确处理JSON字符串**: 如果`form_data`是字符串（数据库存储为TEXT），先解析为dict
2. **详细日志**: 打印是否使用了前端生成的编号，方便调试
3. **键名检查**: 如果前端没有传`report_number`，日志会显示实际传了哪些键

### 测试验证

修复后，重启后端并测试：

```bash
# 1. 重启后端
python src/main.py

# 2. 创建新的AMLO预约
# 前端会调用 /api/report-numbers/amlo/generate 获取报告编号

# 3. 提交预约表单
# 后端应该显示:
[ReportDataService] 使用前端已生成的报告编号: 001-001-68-100081USD

# 4. 查看数据库 Reserved_Transaction 表
# 应该看到连续的编号: 100081, 100082, 100083 (无跳号)
```

### 预期日志输出

**正确情况** (使用前端编号):
```
[ReportDataService] 使用前端已生成的报告编号: 001-001-68-100081USD
[DEBUG] 保存预约记录 - reservation_no: 001-001-68-100081USD
```

**如果前端未传report_number** (才生成新编号):
```
[ReportDataService] 前端未提供报告编号，开始生成新编号...
[ReportDataService] form_data keys: ['maker_id', 'maker_name', ...]
[ReportDataService] 生成的新报告编号: 001-001-68-100081
```

---

## 附加优化建议（可选）

### 1. 统一到新系统

建议长期逐步迁移到新的 `ReportNumberGenerator` 系统：

**优点**:
- 更清晰的年月分组 (`year_month` 字段)
- 更好的并发控制 (唯一约束 `uk_branch_currency_month`)
- 支持币种维度的序列号分离
- 完整的日志记录 (`report_number_logs` 表)

**迁移计划**:
1. 确保所有前端都调用 `/api/report-numbers/amlo/generate` 生成编号
2. 验证 `form_data.report_number` 始终被正确传递
3. 移除旧的 `_generate_reservation_no()` 方法
4. 统一数据表结构为新版本

### 2. 数据库表结构冲突

当前存在两个不兼容的 `amlo_report_sequences` 表定义：

**旧版本** (实际使用中):
```sql
CREATE TABLE amlo_report_sequences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    sequence_date DATE NOT NULL,           -- ← 使用日期
    report_type VARCHAR(20) NOT NULL,
    branch_id INT NOT NULL,
    last_sequence INT NOT NULL DEFAULT 0,
    ...
    UNIQUE KEY (sequence_date, report_type, branch_id)
);
```

**新版本** (migration 007):
```sql
CREATE TABLE amlo_report_sequences (
    id INT AUTO_INCREMENT PRIMARY KEY,
    branch_id INT NOT NULL,
    currency_code VARCHAR(3) NOT NULL,      -- ← 使用币种
    year_month VARCHAR(7) NOT NULL,         -- ← 使用年月字符串
    current_sequence INT NOT NULL DEFAULT 0,
    ...
    UNIQUE KEY (branch_id, currency_code, year_month)
);
```

**建议**: 运行数据库迁移脚本更新表结构：
```bash
python src/migrations/007_report_number_sequences.sql
```

---

## 总结

| 项目 | 状态 |
|-----|------|
| **问题识别** | ✅ 完成 |
| **根本原因** | ✅ 双重序列号生成 |
| **修复代码** | ✅ 已修改 `report_data_service.py` |
| **测试验证** | ⏳ 需要用户测试 |
| **长期优化** | 📋 建议统一到新系统 |

**修复文件**: `src/services/repform/report_data_service.py` (lines 40-64)

**下一步**: 重启后端，创建新预约，检查编号是否连续
