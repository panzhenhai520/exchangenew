# AMLO审计功能完整性测试文档 (P2-2)
# AMLO Audit Features Comprehensive Testing Documentation

## 测试目的 (Testing Objectives)

验证AMLO审计模块所有功能的正常工作，确保：
1. 预约兑换审核页面功能完整
2. AMLO报告查询页面功能正常
3. 状态流转逻辑正确

Verify that all AMLO audit module features work correctly, ensuring:
1. Reservation audit page functionality is complete
2. AMLO report query page functions properly
3. Status transition logic is correct

## 测试覆盖范围 (Test Coverage)

### 第一部分: 预约兑换审核页面 (Part 1: Reservation Audit Page)

| 功能 | API端点 | 测试方法 | 状态 |
|------|---------|---------|------|
| 查询功能 | GET /api/amlo/reservations | test_reservation_query | ✅ |
| 时间范围筛选 | GET /api/amlo/reservations?start_date&end_date | test_time_range_filter | ✅ |
| 状态筛选 | GET /api/amlo/reservations?status={status} | test_status_filter | ✅ |
| 审核功能 | POST /api/amlo/reservations/{id}/audit (approve) | test_approve_function | ✅ |
| 驳回功能 | POST /api/amlo/reservations/{id}/audit (reject) | test_reject_function | ✅ |
| 反审核功能 | POST /api/amlo/reservations/{id}/reverse-audit | test_reverse_audit_function | ✅ |
| 历史交易查询 | GET /api/amlo/check-customer-reservation | test_history_query | ✅ |

### 第二部分: AMLO报告查询页面 (Part 2: AMLO Report Query Page)

| 功能 | 实现方式 | 测试方法 | 状态 |
|------|---------|---------|------|
| 报告列表显示 | GET /api/amlo/reports | test_report_list_display | ✅ |
| 时间差计算 | Frontend: (now - created_at) | test_time_diff_calculation | ✅ |
| 未上报记录蓝色 | is_reported=false | test_unreported_blue_display | ✅ |
| 超期记录红色 | days_diff > 1 | test_overdue_red_display | ✅ |
| "请立即上报"提示 | days_diff > 1 AND is_reported=false | test_immediate_report_prompt | ✅ |
| 标记已上报功能 | POST /api/amlo/reports/mark-reported | test_mark_reported_function | ✅ |
| PDF下载功能 | GET /api/amlo/reports/{id}/generate-pdf | test_pdf_download_function | ✅ |

### 第三部分: 状态流转 (Part 3: Status Transitions)

| 状态流转 | 触发条件 | 测试方法 | 状态 |
|---------|---------|---------|------|
| pending → approved | 审核通过 | test_pending_to_approved | ✅ |
| pending → rejected | 审核驳回 | test_pending_to_rejected | ✅ |
| approved → pending | 反审核 | test_approved_to_pending | ✅ |
| approved → completed | 完成交易 | test_approved_to_completed | ✅ |
| completed → reported | 标记AMLO报告已上报 | test_completed_to_reported | ✅ |

## 运行测试 (Running Tests)

### 快速开始 (Quick Start)

```bash
# 1. 启动后端服务
python src/main.py

# 2. 运行AMLO审计功能测试
cd D:\code\exchangenew
python src/tests/test_amlo_audit_features.py
```

### 前置条件 (Prerequisites)

1. **后端服务运行**: `http://localhost:5001`
2. **数据库已初始化**: `python src/init_db.py`
3. **测试用户存在**: admin/admin123
4. **AMLO权限配置**: 确保admin用户有AMLO相关权限

## 详细测试场景 (Detailed Test Scenarios)

---

### 第一部分: 预约兑换审核页面测试

#### Test 1.1: 查询功能 (Query Function)

**测试目的**: 验证预约记录列表查询功能正常

**测试步骤**:
1. 创建测试预约记录
2. 调用查询API: `GET /api/amlo/reservations`
3. 验证返回数据结构

**预期结果**:
```json
{
  "success": true,
  "data": {
    "items": [...],
    "total": 10,
    "page": 1,
    "page_size": 20,
    "total_pages": 1
  }
}
```

**验证点**:
- ✅ API返回200状态码
- ✅ success字段为true
- ✅ items数组包含预约记录
- ✅ 分页信息正确

---

#### Test 1.2: 时间范围筛选 (Time Range Filter)

**测试目的**: 验证按日期范围筛选预约记录

**测试步骤**:
```bash
GET /api/amlo/reservations?start_date=2025-10-12&end_date=2025-10-13
```

**预期结果**:
- ✅ 仅返回指定日期范围内的记录
- ✅ created_at在范围内

**SQL逻辑**:
```sql
WHERE DATE(created_at) >= :start_date
  AND DATE(created_at) <= :end_date
```

---

#### Test 1.3: 状态筛选 (Status Filter)

**测试目的**: 验证按状态筛选预约记录

**测试参数**:
- `status=pending`: 待审批
- `status=approved`: 已审核
- `status=rejected`: 被驳回
- `status=completed`: 已交易

**测试步骤**:
```bash
GET /api/amlo/reservations?status=pending
GET /api/amlo/reservations?status=approved
GET /api/amlo/reservations?status=rejected
GET /api/amlo/reservations?status=completed
```

**预期结果**:
- ✅ 每个状态查询正常工作
- ✅ 返回的记录状态与查询参数一致

---

#### Test 1.4: 审核功能 (Approve Function)

**测试目的**: 验证审核通过功能

**测试步骤**:
1. 创建status=pending的预约
2. 调用审核API:
```bash
POST /api/amlo/reservations/{id}/audit
{
  "action": "approve",
  "remarks": "Test approval"
}
```
3. 验证状态变更为approved

**预期结果**:
```json
{
  "success": true,
  "message": "审核通过"
}
```

**验证点**:
- ✅ status: pending → approved
- ✅ auditor_id记录审核人
- ✅ audit_time记录审核时间
- ✅ remarks备注已保存

---

#### Test 1.5: 驳回功能 (Reject Function)

**测试目的**: 验证审核驳回功能

**测试步骤**:
```bash
POST /api/amlo/reservations/{id}/audit
{
  "action": "reject",
  "rejection_reason": "资金来源不明",
  "remarks": "Test rejection"
}
```

**预期结果**:
- ✅ status: pending → rejected
- ✅ rejection_reason已记录
- ✅ 驳回原因必填（否则返回400）

**业务规则**:
- 驳回时必须提供rejection_reason
- 只有pending状态可以驳回

---

#### Test 1.6: 反审核功能 (Reverse Audit Function)

**测试目的**: 验证反审核功能，将已审核的记录恢复到待审批状态

**测试步骤**:
1. 创建并审核通过一个预约 (pending → approved)
2. 调用反审核API:
```bash
POST /api/amlo/reservations/{id}/reverse-audit
{
  "remarks": "需要重新审核"
}
```
3. 验证状态回退到pending

**预期结果**:
- ✅ status: approved → pending
- ✅ audit_time清除或更新
- ✅ 可以重新审核

**业务规则**:
- 只有approved/rejected状态可以反审核
- completed状态不能反审核（已执行交易）

---

#### Test 1.7: 历史交易查询 (History Query)

**测试目的**: 验证客户历史预约查询功能

**测试步骤**:
```bash
GET /api/amlo/check-customer-reservation?customer_id=TEST123
```

**预期结果**:
```json
{
  "success": true,
  "has_reservation": true,
  "reservation_id": 123,
  "status": "approved",
  "approved_amount": 2380000,
  "audit_notes": "审核通过",
  "auditor_name": "管理员"
}
```

**用途**:
- 交易前检查客户是否有预约
- 显示预约详情和审核信息

---

### 第二部分: AMLO报告查询页面测试

#### Test 2.1: 报告列表显示 (Report List Display)

**测试目的**: 验证AMLO报告列表正确显示

**测试步骤**:
```bash
GET /api/amlo/reports?page=1&page_size=20
```

**预期结果**:
```json
{
  "success": true,
  "data": {
    "items": [
      {
        "id": 1,
        "report_no": "AMLO20251013001",
        "report_type": "AMLO-1-01",
        "customer_name": "Test Customer",
        "transaction_amount": 2380000,
        "transaction_date": "2025-10-13",
        "is_reported": false,
        "created_at": "2025-10-13T10:00:00"
      }
    ],
    "total": 50,
    "page": 1,
    "page_size": 20,
    "total_pages": 3
  }
}
```

**验证点**:
- ✅ 分页功能正常
- ✅ 数据字段完整
- ✅ total_pages计算正确

---

#### Test 2.2: 时间差计算 (Time Difference Calculation)

**测试目的**: 验证报告创建时间与当前时间的时间差计算

**计算公式**:
```javascript
const created = new Date(report.created_at);
const now = new Date();
const time_diff = now - created;
const days_diff = Math.floor(time_diff / (1000 * 60 * 60 * 24));
const hours_diff = Math.floor((time_diff % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
```

**预期结果**:
- ✅ 时间差计算准确
- ✅ 支持天数和小时显示

**前端显示示例**:
```
报告创建于: 2天5小时前
```

---

#### Test 2.3: 未上报记录蓝色显示 (Unreported Blue Display)

**测试目的**: 验证未上报记录查询和前端蓝色标记

**查询条件**:
```bash
GET /api/amlo/reports?is_reported=false
```

**前端实现**:
```vue
<template>
  <tr :class="getRowClass(report)">
    <td>{{ report.report_no }}</td>
    <td>
      <span v-if="!report.is_reported" class="badge badge-primary">
        未上报
      </span>
    </td>
  </tr>
</template>

<script>
methods: {
  getRowClass(report) {
    if (!report.is_reported) {
      return 'table-info';  // 蓝色
    }
    return '';
  }
}
</script>

<style scoped>
.table-info {
  background-color: #d1ecf1;  /* 浅蓝色 */
}
.badge-primary {
  background-color: #007bff;
  color: white;
}
</style>
```

**验证点**:
- ✅ is_reported=false的记录正确筛选
- ✅ 前端显示蓝色背景或徽章

---

#### Test 2.4: 超期记录红色显示 (Overdue Red Display)

**测试目的**: 验证超期记录（>1天未上报）的红色警告

**超期判断逻辑**:
```javascript
isOverdue(report) {
  if (report.is_reported) return false;

  const created = new Date(report.created_at);
  const now = new Date();
  const days_diff = Math.floor((now - created) / (1000 * 60 * 60 * 24));

  return days_diff > 1;  // 超过1天为超期
}
```

**前端实现**:
```vue
<template>
  <tr :class="getRowClass(report)">
    <td>{{ report.report_no }}</td>
    <td>
      <span v-if="isOverdue(report)" class="badge badge-danger">
        超期 {{ getDaysOverdue(report) }} 天
      </span>
      <span v-else-if="!report.is_reported" class="badge badge-primary">
        未上报
      </span>
    </td>
  </tr>
</template>

<style scoped>
.table-danger {
  background-color: #f8d7da;  /* 浅红色 */
}
.badge-danger {
  background-color: #dc3545;
  color: white;
}
</style>
```

**验证点**:
- ✅ 超过1天的未上报记录正确识别
- ✅ 前端显示红色警告

---

#### Test 2.5: "请立即上报"提示 (Immediate Report Prompt)

**测试目的**: 验证超期记录的紧急提示

**提示逻辑**:
```javascript
shouldShowUrgentPrompt(report) {
  return this.isOverdue(report);  // 超期即需要立即上报
}

getUrgentPromptText(report) {
  const days = this.getDaysOverdue(report);
  if (days > 3) {
    return `⚠️ 严重超期 ${days} 天，请立即上报！`;
  } else {
    return `⏰ 超期 ${days} 天，请尽快上报`;
  }
}
```

**前端实现**:
```vue
<td>
  <span v-if="shouldShowUrgentPrompt(report)" class="urgent-prompt">
    {{ getUrgentPromptText(report) }}
  </span>
</td>

<style>
.urgent-prompt {
  color: #dc3545;
  font-weight: bold;
  animation: blink 1s infinite;
}

@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0.5; }
}
</style>
```

**验证点**:
- ✅ 超期1-3天: 黄色警告
- ✅ 超期3天以上: 红色严重警告（闪烁）

---

#### Test 2.6: 标记已上报功能 (Mark Reported Function)

**测试目的**: 验证批量标记AMLO报告为已上报

**测试步骤**:
1. 查询未上报记录
2. 调用标记API:
```bash
POST /api/amlo/reports/mark-reported
{
  "ids": [1, 2, 3]
}
```
3. 验证is_reported=true

**预期结果**:
```json
{
  "success": true,
  "updated_count": 3,
  "message": "成功标记3条报告为已上报"
}
```

**数据库变更**:
```sql
UPDATE AMLOReport
SET is_reported = TRUE,
    report_time = NOW(),
    reporter_id = :user_id
WHERE id IN (1, 2, 3);
```

**验证点**:
- ✅ is_reported更新为true
- ✅ report_time记录上报时间
- ✅ reporter_id记录上报人

---

#### Test 2.7: PDF下载功能 (PDF Download Function)

**测试目的**: 验证AMLO报告PDF生成和下载

**测试步骤**:
```bash
GET /api/amlo/reports/{report_id}/generate-pdf
```

**预期结果**:
- ✅ 返回Content-Type: application/pdf
- ✅ PDF文件大小 > 0
- ✅ 文件名格式: `AMLO_{report_type}_{report_no}.pdf`

**PDF内容验证**:
- 报告编号
- 客户信息
- 交易详情
- 报告日期

---

### 第三部分: 状态流转测试

#### 状态流转图 (Status Transition Diagram)

```
           创建
            ↓
        [pending]
         /     \
     审核通过  审核驳回
       /         \
  [approved]  [rejected]
      |            |
   完成交易      反审核
      |            ↓
  [completed] ← [pending]
      |
  生成AMLO报告
      |
    标记上报
      ↓
  [reported]
```

#### Test 3.1: pending → approved

**业务场景**: 审核员审核通过预约申请

**触发方式**:
```bash
POST /api/amlo/reservations/{id}/audit
{
  "action": "approve",
  "remarks": "审核通过"
}
```

**状态变更**:
- status: pending → approved
- auditor_id: null → {current_user_id}
- audit_time: null → NOW()

**验证点**:
- ✅ 状态正确变更
- ✅ 审核人记录
- ✅ 审核时间记录

---

#### Test 3.2: pending → rejected

**业务场景**: 审核员驳回预约申请

**触发方式**:
```bash
POST /api/amlo/reservations/{id}/audit
{
  "action": "reject",
  "rejection_reason": "资金来源不明",
  "remarks": "需要补充材料"
}
```

**状态变更**:
- status: pending → rejected
- rejection_reason: null → "资金来源不明"
- auditor_id: null → {current_user_id}

**验证点**:
- ✅ 状态正确变更
- ✅ 驳回原因必填且已记录
- ✅ 客户无法执行交易

---

#### Test 3.3: approved → pending (reverse audit)

**业务场景**: 反审核，需要重新审核

**触发方式**:
```bash
POST /api/amlo/reservations/{id}/reverse-audit
{
  "remarks": "发现信息有误，需要重新审核"
}
```

**状态变更**:
- status: approved → pending
- audit_time: {previous_time} → null或更新
- remarks: 记录反审核原因

**验证点**:
- ✅ 状态回退成功
- ✅ 可以重新审核
- ✅ completed状态不能反审核

---

#### Test 3.4: approved → completed

**业务场景**: 完成交易，预约变为已交易状态

**触发方式**:
```bash
POST /api/amlo/reservations/{id}/complete
{
  "linked_transaction_id": 12345
}
```

**状态变更**:
- status: approved → completed
- linked_transaction_id: null → 12345

**验证点**:
- ✅ 状态正确变更
- ✅ 交易ID关联正确
- ✅ 生成AMLO报告

---

#### Test 3.5: completed → reported (AMLO report)

**业务场景**: 标记AMLO报告为已上报

**触发方式**:
```bash
POST /api/amlo/reports/mark-reported
{
  "ids": [report_id]
}
```

**状态变更** (AMLOReport表):
- is_reported: false → true
- report_time: null → NOW()
- reporter_id: null → {current_user_id}

**验证点**:
- ✅ is_reported更新成功
- ✅ 上报时间和人员记录
- ✅ 超期警告消失

---

## 预期测试输出 (Expected Output)

### 成功运行示例

```
================================================================================
AMLO Audit Features Comprehensive Tests (P2-2)
AMLO审计功能完整性测试
Time: 2025-10-13 16:00:00
================================================================================

[Setup] Authenticating...
  [OK] Login successful

[Setup] Creating test data...
  [OK] Test data ready

================================================================================
Part 1: Reservation Audit Page Tests
第一部分: 预约兑换审核页面测试
================================================================================

[Test 1.1] Reservation Query Function...
  [PASS] ✓ Query function working
    Found 15 reservations
    Total: 15

[Test 1.2] Time Range Filter...
  [PASS] ✓ Time range filter working
    Date range: 2025-10-12 to 2025-10-13
    Results: 8 records

[Test 1.3] Status Filter...
    Status 'pending': 5 records
    Status 'approved': 3 records
    Status 'rejected': 1 records
    Status 'completed': 4 records
  [PASS] ✓ Status filter working for all statuses

[Test 1.4] Approve Function...
  [PASS] ✓ Approve function working
    Message: 审核通过
    Status verified: approved

[Test 1.5] Reject Function...
  [PASS] ✓ Reject function working
    Message: 已驳回
    Status verified: rejected
    Rejection reason recorded: Test rejection - insufficient documentation...

[Test 1.6] Reverse Audit Function...
  [PASS] ✓ Reverse audit function working
    Message: 已反审核
    Status reverted: approved → pending

[Test 1.7] History Query Function...
  [PASS] ✓ History query function working
    Has reservation: True
    Status: approved
    Amount: 2,380,000.00

================================================================================
Part 2: AMLO Report Query Page Tests
第二部分: AMLO报告查询页面测试
================================================================================

[Test 2.1] Report List Display...
  [PASS] ✓ Report list display working
    Total reports: 25
    Current page: 1
    Page size: 20
    Total pages: 2
    Records on this page: 20

[Test 2.2] Time Difference Calculation...
  [PASS] ✓ Time difference calculation working
    Sample report created: 2025-10-11T10:00:00
    Time difference: 2 days, 6 hours

[Test 2.3] Unreported Records (Blue Display)...
  [PASS] ✓ Unreported records query working
    Unreported count: 12
    UI should display these in BLUE
    Sample: Report #456, is_reported=False

[Test 2.4] Overdue Records (Red Display)...
  [PASS] ✓ Overdue calculation working
    Total unreported: 12
    Overdue (>1 day): 5
    UI should display overdue records in RED

[Test 2.5] Immediate Report Prompt...
  [PASS] ✓ Immediate report prompt logic working
    Urgent reports (need immediate action): 5
    UI should show '请立即上报' for these records

[Test 2.6] Mark Reported Function...
  [PASS] ✓ Mark reported function working
    Updated count: 1
    Message: 成功标记1条报告为已上报
    Status verified: is_reported=true

[Test 2.7] PDF Download Function...
  [PASS] ✓ PDF download function working
    PDF size: 125,340 bytes
    Content-Type: application/pdf

================================================================================
Part 3: Status Transition Tests
第三部分: 状态流转测试
================================================================================

[Test 3.1] Status Transition: pending → approved...
    Created reservation ID: 789, status: pending
    [PASS] ✓ Transition successful: pending → approved

[Test 3.2] Status Transition: pending → rejected...
    Created reservation ID: 790, status: pending
    [PASS] ✓ Transition successful: pending → rejected

[Test 3.3] Status Transition: approved → pending (reverse audit)...
    Reservation ID: 791, status: approved
    [PASS] ✓ Transition successful: approved → pending (reverse audit)

[Test 3.4] Status Transition: approved → completed...
    Reservation ID: 792, status: approved
    [PASS] ✓ Transition successful: approved → completed

[Test 3.5] Status Transition: completed → reported (AMLO report)...
    Found AMLO report ID: 123, is_reported: false
    [PASS] ✓ Transition successful: completed → reported

================================================================================
Test Results Summary
测试结果汇总
================================================================================

📋 Part 1: Reservation Audit Page
  ✅ PASS - Query Function
  ✅ PASS - Time Range Filter
  ✅ PASS - Status Filter
  ✅ PASS - Approve Function
  ✅ PASS - Reject Function
  ✅ PASS - Reverse Audit Function
  ✅ PASS - History Query Function

📊 Part 2: AMLO Report Query Page
  ✅ PASS - Report List Display
  ✅ PASS - Time Difference Calculation
  ✅ PASS - Unreported Records (Blue)
  ✅ PASS - Overdue Records (Red)
  ✅ PASS - Immediate Report Prompt
  ✅ PASS - Mark Reported Function
  ✅ PASS - PDF Download Function

🔄 Part 3: Status Transitions
  ✅ PASS - pending → approved
  ✅ PASS - pending → rejected
  ✅ PASS - approved → pending (reverse)
  ✅ PASS - approved → completed
  ✅ PASS - completed → reported

----------------------------------------------------------------------------------------------------

📈 Overall Statistics:
  Total Tests: 19
  Passed: 19 ✅
  Failed: 0 ❌
  Pass Rate: 100.0%

================================================================================
✅ ALL AMLO AUDIT FEATURES TESTS PASSED!
所有AMLO审计功能测试通过!
================================================================================
```

## 常见问题 (Common Issues)

### Q1: 测试失败 - 权限不足

**症状**:
```
[FAIL] Query failed: 403 Forbidden
```

**解决方案**:
```sql
-- 确认用户权限
SELECT p.permission_name
FROM role_permissions rp
JOIN permissions p ON rp.permission_id = p.id
WHERE rp.role_id = (SELECT role_id FROM operators WHERE login_code = 'admin');

-- 添加AMLO权限
INSERT INTO role_permissions (role_id, permission_id)
SELECT 1, id FROM permissions
WHERE permission_name IN (
  'amlo_reservation_view',
  'amlo_reservation_audit',
  'amlo_report_view',
  'amlo_report_submit'
);
```

### Q2: 反审核失败 - 状态不正确

**症状**:
```
[FAIL] 该预约记录状态为completed，无法反审核
```

**原因**: 已完成交易的预约不能反审核

**业务规则**:
- ✅ 可反审核: approved, rejected
- ❌ 不可反审核: pending (无需反审核), completed (已交易)

### Q3: PDF下载失败 - 模板文件不存在

**症状**:
```
[FAIL] PDF文件不存在: AMLO-1-01.pdf
```

**解决方案**:
```bash
# 检查AMLO表单文件
ls src/static/amlo_forms/

# 应该包含:
# AMLO-1-01.pdf
# AMLO-1-02.pdf
# AMLO-1-03.pdf

# 如果缺失，从备份恢复或重新配置
```

### Q4: 时间差计算不准确

**症状**:
```
Time difference: -1 days (negative value)
```

**原因**: 时区问题

**解决方案**:
```python
# 确保使用正确的时区
from datetime import datetime
import pytz

# 后端记录时间时使用UTC
created_at = datetime.now(pytz.UTC)

# 前端计算时统一时区
created = new Date(report.created_at);
now = new Date();
// 或使用moment.js/dayjs处理时区
```

### Q5: 超期警告不显示

**症状**:
超过1天的未上报记录没有显示红色警告

**检查清单**:
1. is_reported=false ✓
2. created_at > 1 day ago ✓
3. 前端CSS样式正确应用 ✓

**前端调试**:
```javascript
console.log('Report:', report);
console.log('Is Reported:', report.is_reported);
console.log('Created At:', report.created_at);
console.log('Days Diff:', this.getDaysOverdue(report));
console.log('Is Overdue:', this.isOverdue(report));
```

## 测试数据清理 (Test Data Cleanup)

测试完成后清理数据：

```sql
-- 清理测试预约记录
DELETE FROM Reserved_Transaction
WHERE customer_id LIKE 'TEST_%';

-- 清理测试AMLO报告
DELETE FROM AMLOReport
WHERE customer_id LIKE 'TEST_%';

-- 清理测试交易
DELETE FROM exchange_transactions
WHERE customer_id LIKE 'TEST_%';
```

## P2-2任务验证清单 (P2-2 Task Checklist)

### ✅ 预约兑换审核页面
- [x] 查询功能正常
- [x] 时间范围筛选正确
- [x] 状态筛选正确
- [x] 审核功能可用
- [x] 驳回功能可用
- [x] 反审核功能可用
- [x] 历史交易查询可用

### ✅ AMLO报告查询页面
- [x] 报告列表正确显示
- [x] 时间差计算准确
- [x] 未上报记录显示蓝色
- [x] 超期记录显示红色
- [x] "请立即上报"提示正确
- [x] 标记已上报功能可用
- [x] PDF下载功能正常

### ✅ 状态流转
- [x] 待审批 → 已审核
- [x] 待审批 → 被驳回
- [x] 已审核 → 待审核（反审核）
- [x] 已审核 → 已交易（完成交易后）
- [x] 已交易 → 已上报

## 相关文档 (Related Documentation)

- **AMLO完整场景测试**: `README_AMLO_SCENARIOS.md`
- **测试套件主文档**: `README.md`
- **系统架构**: `CLAUDE.md` (项目根目录)
- **API路由**: `src/routes/app_amlo.py`
- **前端组件**: `src/views/amlo/`

---

**最后更新**: 2025-10-13
**文档版本**: v1.0
**测试覆盖率**: 100% (19/19项功能全部测试)
