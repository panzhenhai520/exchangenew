# AMLO完整场景测试文档

## 测试目的

验证AMLO（反洗钱办公室）预约审核和报告提交的完整业务流程，包括：
1. 预约创建和审核流程
2. 交易执行和报告生成
3. 反审核功能
4. 超期提醒机制

## 测试场景

### 场景A: 完整的预约到交易流程（20步）

**业务流程**: 客户预约 → 审核批准 → 执行交易 → 生成报告

**详细步骤**:

#### 阶段1: 准备数据（步骤1-5）
1. **获取USD货币ID** - 查询系统货币列表
2. **设置USD汇率** - buy=33.5, sell=34.0 THB
3. **准备客户信息** - ID, 姓名, 国家, 地址
4. **准备交易数据** - 金额70,000 USD (本币2,380,000 THB)
5. **验证AMLO触发条件** - 确认超过2M THB阈值

#### 阶段2: 预约和审核（步骤6-10）
6. **创建预约记录** - POST /api/amlo/reservations
7. **查询预约记录** - 验证记录已创建
8. **验证初始状态** - status='pending'
9. **审核预约（批准）** - POST /api/amlo/reservations/{id}/audit
10. **验证审核后状态** - status='approved'，记录审核人和时间

#### 阶段3: 交易执行（步骤11-15）
11. **检查客户预约状态** - 交易前确认
12. **执行交易** - POST /api/exchange/transactions
13. **验证交易成功** - status='completed'
14. **完成预约** - 关联transaction_id
15. **生成PDF报告** - 自动或手动触发

#### 阶段4: 验证结果（步骤16-20）
16. **验证AMLOReport表** - 确认记录存在
17. **验证预约状态** - status='completed'
18. **测试PDF下载** - GET /api/amlo/reports/{id}/generate-pdf
19. **验证未上报状态** - is_reported=false
20. **测试总结** - 输出所有ID和状态

**预期结果**:
```json
{
  "reservation_id": 123,
  "reservation_no": "RSV20251013...",
  "reservation_status": "completed",
  "transaction_id": 456,
  "transaction_no": "A00520251013...",
  "transaction_status": "completed",
  "report_id": 789,
  "report_type": "AMLO-1-01",
  "is_reported": false
}
```

**关键验证点**:
- ✓ 预约状态流转: pending → approved → completed
- ✓ 审核记录: auditor_id, audit_time
- ✓ 交易关联: linked_transaction_id
- ✓ 报告生成: PDF文件存在
- ✓ 待上报状态: is_reported=false

---

### 场景B: 反审核流程（4步）

**业务场景**: 已审核的预约需要重新审核（发现错误或需要修改）

**详细步骤**:

1. **创建已审核的预约记录**
   ```python
   # 创建预约
   POST /api/amlo/reservations
   {
     "customer_id": "REVERSE_TEST_001",
     "amount": 70000,
     "status": "pending"
   }

   # 审核通过
   POST /api/amlo/reservations/{id}/audit
   {
     "action": "approve"
   }
   ```

2. **调用反审核API**
   ```python
   POST /api/amlo/reservations/{id}/reverse-audit
   {
     "remarks": "需要重新审核"
   }
   ```

3. **验证状态回退到pending**
   ```python
   GET /api/amlo/reservations?customer_id=REVERSE_TEST_001
   # 期望: status='pending'
   ```

4. **验证反审核元数据**
   - audit_time 被清除或更新
   - remarks 记录了反审核原因
   - 可以重新审核

**预期结果**:
```json
{
  "success": true,
  "message": "已反审核",
  "reservation": {
    "id": 123,
    "status": "pending",  // 从approved回退到pending
    "auditor_id": null,   // 审核人清除
    "audit_time": null,   // 审核时间清除
    "remarks": "需要重新审核"
  }
}
```

**业务规则**:
- 只有approved或rejected状态才能反审核
- completed状态不能反审核（已完成交易）
- 反审核后可以重新审核（approve/reject）

**使用场景**:
- 审核时发现信息填写错误
- 需要补充更多材料
- 客户要求修改交易信息

---

### 场景C: 超期提醒（5步）

**业务场景**: 已交易但超过1天未上报的AMLO报告显示红色警告

**详细步骤**:

1. **查找或创建超期报告**
   ```python
   # 查询2天前创建的未上报报告
   GET /api/amlo/reports?is_reported=false&start_date=2025-10-11&end_date=2025-10-12
   ```

2. **查询AMLO报告列表**
   ```python
   GET /api/amlo/reports?is_reported=false
   ```

3. **验证超期标记**
   ```python
   # 计算超期天数
   days_overdue = (now - created_at).days

   if days_overdue > 1:
       # 前端应显示红色警告
       alert_class = "overdue-warning"
       alert_text = f"超期 {days_overdue} 天"
   ```

4. **标记为已上报**
   ```python
   POST /api/amlo/reports/mark-reported
   {
     "ids": [789]
   }
   ```

5. **验证警告消失**
   ```python
   GET /api/amlo/reports?is_reported=false
   # 该报告不应出现在列表中
   ```

**前端实现示例**:
```vue
<template>
  <tr :class="getRowClass(report)">
    <td>{{ report.report_no }}</td>
    <td>{{ report.transaction_date }}</td>
    <td>
      <span v-if="isOverdue(report)" class="badge badge-danger">
        超期 {{ getDaysOverdue(report) }} 天
      </span>
    </td>
    <td>
      <button @click="markReported(report.id)">标记已上报</button>
    </td>
  </tr>
</template>

<script>
export default {
  methods: {
    isOverdue(report) {
      if (report.is_reported) return false;

      const created = new Date(report.created_at);
      const now = new Date();
      const days = Math.floor((now - created) / (1000 * 60 * 60 * 24));

      return days > 1;
    },

    getDaysOverdue(report) {
      const created = new Date(report.created_at);
      const now = new Date();
      return Math.floor((now - created) / (1000 * 60 * 60 * 24));
    },

    getRowClass(report) {
      return this.isOverdue(report) ? 'table-danger' : '';
    }
  }
}
</script>

<style scoped>
.table-danger {
  background-color: #f8d7da;
}

.badge-danger {
  background-color: #dc3545;
  color: white;
  padding: 4px 8px;
  border-radius: 4px;
}
</style>
```

**预期结果**:
```json
{
  "reports": [
    {
      "id": 789,
      "report_no": "AMLO20251011001",
      "created_at": "2025-10-11T10:00:00",
      "is_reported": false,
      "days_overdue": 2,
      "alert_level": "danger"  // 前端计算
    }
  ]
}
```

**业务规则**:
- 超期时间 = 当前时间 - 交易时间
- 超过1天（24小时）显示警告
- 已上报（is_reported=true）不显示警告
- 警告级别:
  - 1-2天: 黄色警告
  - 3天以上: 红色严重警告

---

## 数据库表结构

### Reserved_Transaction（预约表）
```sql
CREATE TABLE Reserved_Transaction (
    id INT PRIMARY KEY AUTO_INCREMENT,
    reservation_no VARCHAR(50) UNIQUE,
    customer_id VARCHAR(50),
    customer_name VARCHAR(100),
    currency_id INT,
    direction VARCHAR(10),      -- 'buy' / 'sell'
    amount DECIMAL(15,2),
    local_amount DECIMAL(15,2),
    rate DECIMAL(10,4),
    report_type VARCHAR(20),    -- 'AMLO-1-01' / 'AMLO-1-02' / 'AMLO-1-03'
    status VARCHAR(20),          -- 'pending' / 'approved' / 'rejected' / 'completed'
    branch_id INT,
    operator_id INT,
    auditor_id INT,              -- 审核人ID
    audit_time DATETIME,         -- 审核时间
    rejection_reason TEXT,
    remarks TEXT,
    linked_transaction_id INT,   -- 关联的交易ID
    created_at DATETIME,
    updated_at DATETIME
);
```

### AMLOReport（报告表）
```sql
CREATE TABLE AMLOReport (
    id INT PRIMARY KEY AUTO_INCREMENT,
    report_no VARCHAR(50) UNIQUE,
    report_type VARCHAR(20),
    reserved_id INT,             -- 关联的预约ID
    transaction_id INT,          -- 关联的交易ID
    customer_id VARCHAR(50),
    customer_name VARCHAR(100),
    transaction_amount DECIMAL(15,2),
    transaction_date DATE,
    pdf_filename VARCHAR(255),
    pdf_path VARCHAR(500),
    is_reported BOOLEAN DEFAULT FALSE,  -- 是否已上报
    report_time DATETIME,               -- 上报时间
    reporter_id INT,                    -- 上报人ID
    branch_id INT,
    operator_id INT,
    created_at DATETIME,
    updated_at DATETIME
);
```

## API接口清单

### 预约管理
| 方法 | 路径 | 说明 |
|-----|------|-----|
| POST | /api/amlo/reservations | 创建预约 |
| GET | /api/amlo/reservations | 查询预约列表 |
| GET | /api/amlo/check-customer-reservation | 检查客户预约状态 |
| POST | /api/amlo/reservations/{id}/audit | 审核预约 |
| POST | /api/amlo/reservations/{id}/reverse-audit | 反审核 |
| POST | /api/amlo/reservations/{id}/complete | 完成预约 |

### 报告管理
| 方法 | 路径 | 说明 |
|-----|------|-----|
| GET | /api/amlo/reports | 查询报告列表 |
| POST | /api/amlo/reports/mark-reported | 标记已上报 |
| POST | /api/amlo/reports/batch-report | 批量上报 |
| GET | /api/amlo/reports/{id}/generate-pdf | 生成PDF |
| POST | /api/amlo/reports/batch-generate-pdf | 批量生成PDF |

## 运行测试

### 前提条件
```bash
# 1. 启动后端服务
python src/main.py

# 2. 确保数据库已初始化
python src/init_db.py

# 3. 确保有测试用户
# 用户名: admin
# 密码: admin123
```

### 运行完整测试
```bash
cd D:\code\exchangenew
python src/tests/test_amlo_complete_scenarios.py
```

### 运行单个场景
```python
# 仅测试场景A
tester = AMLOScenarioTester()
tester.login()
tester.scenario_a_reservation_to_transaction()

# 仅测试场景B
tester.scenario_b_reverse_audit()

# 仅测试场景C
tester.scenario_c_overdue_alert()
```

## 预期输出

### 成功场景输出
```
================================================================================
AMLO Complete Scenario Tests
Time: 2025-10-13 14:30:00
================================================================================

[Login] Authenticating...
  [OK] Login successful

================================================================================
Scenario A: Complete Reservation to Transaction Flow
================================================================================

[Step 1/20] Get USD currency ID...
  [OK] USD currency ID: 2

[Step 2/20] Set USD exchange rate...
  [OK] USD rate set: buy=33.5, sell=34.0

[Step 3/20] Prepare customer information...
  [OK] Customer: Test Customer AMLO
  [OK] ID: TEST123456789

... (省略中间步骤) ...

[Step 20/20] Test summary...
  Reservation ID: 123
  Reservation No: RSV20251013143000
  Transaction ID: 456
  Transaction No: A00520251013143005
  Report ID: 789
  [PASS] Scenario A completed successfully!

================================================================================
Scenario B: Reverse Audit Flow
================================================================================

[Step 1/4] Create and approve a reservation...
  [OK] Reservation created: ID=124
  [OK] Reservation approved

[Step 2/4] Call reverse audit API...
  [OK] Reverse audit successful

[Step 3/4] Verify status changed to pending...
  [OK] Status reverted to 'pending'

[Step 4/4] Verify reverse audit metadata...
  [OK] Audit time cleared
  [OK] Remarks recorded: Test reverse audit
  [PASS] Scenario B completed successfully!

================================================================================
Scenario C: Overdue Alert Test
================================================================================

[Step 1/5] Create overdue AMLO report...
  [INFO] Checking existing reports...
  [OK] Found report: ID=785

[Step 2/5] Query AMLO report list...
  [OK] Found report: ID=785
  [OK] Created at: 2025-10-11T10:00:00
  [OK] Transaction date: 2025-10-11

[Step 3/5] Verify overdue indicator...
  [OK] Report is overdue: 2 days
  [OK] Should display red alert in UI

[Step 4/5] Mark report as submitted...
  [OK] Report marked as submitted
  [OK] Updated count: 1

[Step 5/5] Verify overdue alert cleared...
  [OK] Report no longer in unreported list
  [OK] Overdue alert should be cleared
  [PASS] Scenario C completed successfully!

================================================================================
Test Results Summary
================================================================================
  [PASS] Scenario A: Reservation to Transaction
  [PASS] Scenario B: Reverse Audit
  [PASS] Scenario C: Overdue Alert

Total: 3/3 scenarios passed (100%)

✓ All scenarios PASSED!
```

## 常见问题

### Q1: 场景A失败：交易未触发AMLO
**原因**: 金额未超过阈值或触发规则未配置
**解决方案**:
```bash
# 检查触发规则
python src/check_trigger_rules.py

# 确认阈值配置
# 本币金额应 > 2,000,000 THB
```

### Q2: 场景B失败：无法反审核
**原因**: 预约状态不正确或权限不足
**检查**:
- 只有approved/rejected状态可以反审核
- 确认用户有amlo_reservation_audit权限

### Q3: 场景C：无超期报告
**原因**: 测试数据库中没有旧报告
**解决方案**:
```sql
-- 手动创建测试数据（修改时间）
UPDATE AMLOReport
SET created_at = DATE_SUB(NOW(), INTERVAL 2 DAY)
WHERE id = 123;
```

### Q4: PDF生成失败
**原因**: 缺少PDF模板或字体文件
**检查**:
```bash
# 检查AMLO表单文件
ls src/static/amlo_forms/

# 检查字体文件
ls src/fonts/
```

## 扩展测试

### 额外测试场景建议

#### 场景D: 审核驳回流程
```python
def test_rejection_flow():
    """测试审核驳回"""
    # 1. 创建预约
    # 2. 审核驳回
    # 3. 验证：status='rejected'
    # 4. 验证：rejection_reason已记录
    # 5. 客户无法执行交易
```

#### 场景E: 批量上报
```python
def test_batch_report():
    """测试批量上报多个报告"""
    # 1. 创建3个未上报报告
    # 2. 批量上报
    # 3. 验证：所有报告is_reported=true
    # 4. 验证：report_time已记录
```

#### 场景F: 不同报告类型
```python
def test_different_report_types():
    """测试不同AMLO报告类型"""
    # 测试AMLO-1-01, AMLO-1-02, AMLO-1-03
    # 验证各类型的特定字段
```

## 维护说明

### 测试数据清理
```sql
-- 清理测试预约
DELETE FROM Reserved_Transaction
WHERE customer_id LIKE 'TEST%' OR customer_id LIKE 'REVERSE_TEST%';

-- 清理测试报告
DELETE FROM AMLOReport
WHERE customer_id LIKE 'TEST%';

-- 清理测试交易
DELETE FROM exchange_transactions
WHERE customer_id LIKE 'TEST%';
```

### 更新测试用例
当修改以下代码时需要更新测试：
1. AMLO触发规则：`src/services/amlo_trigger_service.py`
2. 预约审核逻辑：`src/routes/app_amlo.py`
3. PDF生成：`src/services/pdf/amlo_pdf_generator.py`
4. 超期计算逻辑：前端Vue组件

## 参考文档

- AMLO业务规范：泰国反洗钱办公室规定
- 系统架构：`CLAUDE.md`
- API文档：`src/routes/app_amlo.py`
- 数据库设计：`src/models/report_models.py`
