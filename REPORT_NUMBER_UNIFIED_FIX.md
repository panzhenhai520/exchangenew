# 报告编号系统统一修复

**日期**: 2025-10-29
**问题**: 报告编号跳过所有偶数（新旧两套系统冲突）
**解决方案**: 完全移除旧系统，统一使用 `ReportNumberGenerator`

---

## 修复内容

### 1. 统一报告编号生成逻辑

**之前**: 两套系统并存导致双重消耗序列号
- **新系统**: `ReportNumberGenerator` (正确的实现)
- **旧系统**: `ReportDataService._generate_reservation_no` (遗留代码) ❌

**现在**: 只使用一套系统
- **唯一系统**: `ReportNumberGenerator` ✅

---

## 修改文件清单

### 文件 1: `src/services/repform/report_data_service.py`

#### 修改 1: 改进 `save_reservation()` 方法 (lines 40-83)

**改进点**:
1. 正确解析 `form_data`（支持dict和JSON字符串）
2. 如果前端未提供 `report_number`，使用 `ReportNumberGenerator` 生成
3. 添加详细日志输出

**修改后代码**:
```python
# 优先使用前端已生成的报告编号
form_data = reservation_data.get('form_data', {})

# form_data可能是dict或JSON字符串
if isinstance(form_data, str):
    try:
        form_data = json.loads(form_data)
    except:
        form_data = {}

reservation_no = form_data.get('report_number')

if reservation_no:
    print(f"[ReportDataService] 使用前端已生成的报告编号: {reservation_no}")
else:
    # 使用新的ReportNumberGenerator生成
    print(f"[ReportDataService] 前端未提供报告编号，使用ReportNumberGenerator生成...")

    from services.report_number_generator import ReportNumberGenerator

    # 获取币种代码
    currency_code = reservation_data.get('currency_code')
    if not currency_code:
        # 从currency_id查询
        currency_id = reservation_data.get('currency_id')
        if currency_id:
            currency_query = text("SELECT code FROM currencies WHERE id = :currency_id")
            result = db_session.execute(currency_query, {'currency_id': currency_id}).fetchone()
            if result:
                currency_code = result[0]

    if not currency_code:
        currency_code = 'USD'  # 默认币种

    # 生成报告编号
    reservation_no = ReportNumberGenerator.generate_amlo_report_number(
        session=db_session,
        branch_id=reservation_data.get('branch_id'),
        currency_code=currency_code,
        operator_id=reservation_data.get('operator_id'),
        transaction_id=reservation_data.get('transaction_id')
    )
    print(f"[ReportDataService] 使用ReportNumberGenerator生成的报告编号: {reservation_no}")
```

#### 修改 2: 删除旧的报告编号生成方法 (lines 172-178)

**删除的方法**:
- `_sanitize_code()` - 代码格式化工具
- `_fetch_branch_codes()` - 获取网点代码（旧版）
- `_next_report_sequence()` - 序列号递增（旧版，使用 `sequence_date`）
- `_generate_reservation_no()` - 报告编号生成（旧版）

**替换为注释**:
```python
# ========== 旧的报告编号生成方法已删除 ==========
# 统一使用 ReportNumberGenerator (src/services/report_number_generator.py)
# 移除的方法:
# - _sanitize_code
# - _fetch_branch_codes
# - _next_report_sequence
# - _generate_reservation_no
```

---

### 文件 2: `src/routes/app_amlo.py`

#### 修改: 使用新的网点代码获取方法 (lines 111-125)

**修改前**:
```python
institution_code, branch_code = ReportDataService._fetch_branch_codes(session, branch_id)
```

**修改后**:
```python
# 使用ReportNumberGenerator获取网点代码
from services.report_number_generator import ReportNumberGenerator
branch_codes = ReportNumberGenerator.get_branch_codes(session, branch_id)
institution_code = branch_codes['institution_code']
branch_code = branch_codes['branch_code']
```

---

## 技术细节

### ReportNumberGenerator 的优势

1. **使用 `year_month` 分组** (不是 `sequence_date`)
   - 更灵活的月度序列管理
   - 便于跨天序列号连续

2. **币种维度分离**
   - 每个币种独立序列号
   - 避免不同币种交易混淆

3. **完整的日志记录**
   - `report_number_logs` 表记录每次生成
   - 可追溯每个编号的使用历史

4. **更好的并发控制**
   - 唯一约束 `uk_branch_currency_month`
   - 原子性操作防止冲突

5. **统一的API接口**
   - `/api/report-numbers/amlo/generate` - 生成AMLO编号
   - `/api/report-numbers/bot/generate` - 生成BOT编号
   - `/api/report-numbers/validate` - 验证编号格式
   - `/api/report-numbers/statistics` - 查询序列号统计

### 数据表结构 (新版)

```sql
CREATE TABLE `amlo_report_sequences` (
    `id` INT AUTO_INCREMENT PRIMARY KEY,
    `branch_id` INT NOT NULL COMMENT '网点ID',
    `currency_code` VARCHAR(3) NOT NULL COMMENT '币种代码',
    `year_month` VARCHAR(7) NOT NULL COMMENT '年月(YYYY-MM)',
    `current_sequence` INT NOT NULL DEFAULT 0,
    `last_used_at` DATETIME,
    `created_at` DATETIME,
    `updated_at` DATETIME,

    UNIQUE KEY `uk_branch_currency_month` (`branch_id`, `currency_code`, `year_month`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
```

---

## 测试验证

### 测试步骤

```bash
# 1. 重启后端
python src/main.py

# 2. 在前端创建新的AMLO预约
#    - 交易币种: USD
#    - 交易金额: 超过阈值

# 3. 查看后端日志
```

### 预期日志输出

**情况A**: 前端已生成报告编号
```
[ReportDataService] 使用前端已生成的报告编号: 001-001-68-100081USD
[DEBUG] 保存预约记录 - reservation_no: 001-001-68-100081USD
[DEBUG] 预约记录保存成功 - reservation_id: 123
```

**情况B**: 前端未提供报告编号（后端生成）
```
[ReportDataService] 前端未提供报告编号，使用ReportNumberGenerator生成...
[ReportDataService] form_data keys: ['maker_id', 'maker_name', 'transaction_purpose', ...]
[AMLO编号生成] 成功生成报告编号: 001-001-68-100081USD
[ReportDataService] 使用ReportNumberGenerator生成的报告编号: 001-001-68-100081USD
[DEBUG] 保存预约记录 - reservation_no: 001-001-68-100081USD
```

### 验证结果

查询数据库验证编号连续性：

```sql
SELECT
    id,
    reservation_no,
    customer_id,
    direction,
    local_amount,
    created_at
FROM Reserved_Transaction
ORDER BY id DESC
LIMIT 10;
```

**预期结果**: 编号应该是连续的
```
100081USD
100082USD
100083USD
100084USD
...
```

**不应该出现**: 跳号现象
```
❌ 100081USD → 100083USD (跳过100082)
```

---

## 系统架构改进

### 之前: 双系统架构 (有问题)

```
前端生成编号
    ↓
ReportNumberGenerator (新系统)
    ↓ (序列号 +1)
  100071
    ↓
前端提交表单 (form_data.report_number = 100071)
    ↓
后端 save_reservation()
    ↓
_generate_reservation_no (旧系统) ← ❌ 又生成一次！
    ↓ (序列号再 +1)
  100072 (被浪费)
    ↓
使用 100071，下次跳到 100073
```

### 现在: 单一系统架构 (正确)

```
前端生成编号
    ↓
ReportNumberGenerator
    ↓ (序列号 +1)
  100071
    ↓
前端提交表单 (form_data.report_number = 100071)
    ↓
后端 save_reservation()
    ↓
使用前端提供的 100071 ✅
    ↓
下次继续 100072 (连续！)
```

---

## 数据库迁移说明

### 检查当前表结构

```sql
DESCRIBE amlo_report_sequences;
```

**如果看到 `sequence_date` 字段** (旧结构):
```
+----------------+-------------+------+-----+---------+
| Field          | Type        | Null | Key | Default |
+----------------+-------------+------+-----+---------+
| sequence_date  | date        | NO   | MUL | NULL    |  ← 旧字段
| report_type    | varchar(20) | NO   |     | NULL    |
| branch_id      | int         | NO   |     | NULL    |
| last_sequence  | int         | NO   |     | 0       |
+----------------+-------------+------+-----+---------+
```

**需要运行迁移脚本**:
```bash
# 方式1: 运行SQL迁移
mysql -u root -p exchangedb < src/migrations/007_report_number_sequences.sql

# 方式2: 使用Python迁移工具
python src/migrations/run_migration_007.py
```

**如果看到 `year_month` 字段** (新结构):
```
+------------------+-------------+------+-----+---------+
| Field            | Type        | Null | Key | Default |
+------------------+-------------+------+-----+---------+
| branch_id        | int         | NO   | MUL | NULL    |
| currency_code    | varchar(3)  | NO   |     | NULL    |
| year_month       | varchar(7)  | NO   |     | NULL    |  ← 新字段
| current_sequence | int         | NO   |     | 0       |
+------------------+-------------+------+-----+---------+
```
✅ 表结构已是最新版本，无需迁移

---

## 相关文件清单

### 修改的文件
1. `src/services/repform/report_data_service.py` - 移除旧系统，统一使用新系统
2. `src/routes/app_amlo.py` - 更新网点代码获取方法

### 核心文件（无需修改）
1. `src/services/report_number_generator.py` - 新的报告编号生成器
2. `src/models/report_number_models.py` - 数据模型定义
3. `src/routes/app_report_numbers.py` - API路由定义
4. `src/migrations/007_report_number_sequences.sql` - 数据表结构

### 前端文件（无需修改）
1. `src/components/amlo/DynamicForm/DynamicFormImproved.vue` - 调用生成编号API

---

## 总结

| 项目 | 状态 |
|-----|------|
| **移除旧系统** | ✅ 完成 |
| **统一使用新系统** | ✅ 完成 |
| **修改调用代码** | ✅ 完成 |
| **添加日志输出** | ✅ 完成 |
| **测试验证** | ⏳ 需要用户测试 |

**修改的文件**:
- `src/services/repform/report_data_service.py` (删除90行旧代码，添加30行新代码)
- `src/routes/app_amlo.py` (更新网点代码获取逻辑)

**删除的代码行数**: ~90行
**新增的代码行数**: ~30行
**净减少代码**: ~60行

**下一步**:
1. 重启后端: `python src/main.py`
2. 创建新AMLO预约
3. 验证编号连续性
4. 检查日志输出

---

**修复完成日期**: 2025-10-29
**修复人员**: Claude Code Assistant
**问题编号**: REPORT-NUMBER-001
