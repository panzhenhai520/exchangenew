# Exchange System Test Suite
# 外汇管理系统测试套件

## 概述 (Overview)

本目录包含外汇管理系统的完整测试套件，涵盖AMLO合规性测试和BOT Provider报告测试。

This directory contains the comprehensive test suite for the Currency Exchange Management System, covering AMLO compliance and BOT Provider reporting tests.

## 测试文件结构 (Test File Structure)

```
src/tests/
├── run_all_tests.py                      # 🎯 主测试运行器 (Master Test Runner)
├── test_amlo_complete_scenarios.py       # AMLO完整场景测试
├── test_amlo_audit_features.py           # AMLO审计功能完整性测试
├── test_branch_isolation.py              # 网点数据完全隔离测试
├── test_all_bot_reports.py               # 所有BOT报告测试（4种类型）
├── test_bot_provider.py                  # BOT Provider集成测试
├── test_bot_provider_eur_adjustment.py   # BOT Provider EUR调节测试
├── README.md                             # 本文件 (This file)
├── README_AMLO_SCENARIOS.md              # AMLO场景测试详细文档
├── README_AMLO_AUDIT_FEATURES.md         # AMLO审计功能测试文档
├── README_BRANCH_ISOLATION.md            # 网点数据隔离测试文档
├── README_ALL_BOT_REPORTS.md             # BOT报告完整测试文档
└── README_BOT_PROVIDER_EUR_TEST.md       # BOT Provider EUR测试文档
```

## 快速开始 (Quick Start)

### 前置条件 (Prerequisites)

1. **启动后端服务** (Start Backend Service):
```bash
python src/main.py
```

2. **确保数据库已初始化** (Ensure Database is Initialized):
```bash
python src/init_db.py
```

3. **测试用户凭证** (Test User Credentials):
   - Username: `admin`
   - Password: `admin123`
   - Branch: `1`

### 运行所有测试 (Run All Tests)

```bash
# 方法1: 使用主测试运行器（推荐）
cd D:\code\exchangenew
python src/tests/run_all_tests.py

# 方法2: 使用详细输出模式
python src/tests/run_all_tests.py --verbose
```

### 运行特定测试套件 (Run Specific Test Suite)

```bash
# 仅运行AMLO场景测试
python src/tests/run_all_tests.py --suite amlo

# 仅运行AMLO审计功能测试
python src/tests/run_all_tests.py --suite amlo_audit

# 仅运行网点数据隔离测试
python src/tests/run_all_tests.py --suite branch_isolation

# 仅运行BOT报告测试
python src/tests/run_all_tests.py --suite bot
```

### 运行单个测试文件 (Run Individual Test Files)

```bash
# AMLO完整场景测试
python src/tests/test_amlo_complete_scenarios.py

# AMLO审计功能完整性测试
python src/tests/test_amlo_audit_features.py

# 网点数据完全隔离测试
python src/tests/test_branch_isolation.py

# 所有BOT报告测试
python src/tests/test_all_bot_reports.py

# BOT Provider EUR调节测试
python src/tests/test_bot_provider_eur_adjustment.py

# BOT Provider完整测试套件
python src/tests/test_bot_provider.py
```

## 测试场景详解 (Test Scenarios Explained)

### 1. AMLO合规性测试 (AMLO Compliance Tests)

**文件**: `test_amlo_complete_scenarios.py`
**文档**: `README_AMLO_SCENARIOS.md`

#### 场景A: 完整预约到交易流程 (Scenario A: Complete Reservation to Transaction Flow)

**步骤数**: 20步 (20 steps)

**业务流程**:
```
客户预约 → 审核批准 → 执行交易 → 生成报告
Customer Reservation → Audit Approval → Execute Transaction → Generate Report
```

**关键验证点**:
- ✅ 预约状态流转: pending → approved → completed
- ✅ 审核记录: auditor_id, audit_time
- ✅ 交易关联: linked_transaction_id
- ✅ 报告生成: PDF文件存在
- ✅ 待上报状态: is_reported=false

**触发条件**:
- 交易金额: 70,000 USD
- 本币金额: 2,380,000 THB (超过2M阈值)
- 报告类型: AMLO-1-01

#### 场景B: 反审核流程 (Scenario B: Reverse Audit Flow)

**步骤数**: 4步 (4 steps)

**业务场景**: 已审核的预约需要重新审核

**验证点**:
- ✅ 状态回退: approved → pending
- ✅ 审核人清除: auditor_id = null
- ✅ 审核时间清除: audit_time = null
- ✅ 反审核原因记录: remarks

**业务规则**:
- 只有approved/rejected状态才能反审核
- completed状态不能反审核（已完成交易）

#### 场景C: 超期提醒 (Scenario C: Overdue Alert)

**步骤数**: 5步 (5 steps)

**业务场景**: 已交易但超过1天未上报的AMLO报告显示红色警告

**验证点**:
- ✅ 超期计算: (当前时间 - 交易时间) > 1天
- ✅ 前端显示: 红色警告标记
- ✅ 标记上报: is_reported=true后警告消失

**警告级别**:
- 1-2天: 黄色警告
- 3天以上: 红色严重警告

### 2. AMLO审计功能完整性测试 (AMLO Audit Features Tests)

**文件**: `test_amlo_audit_features.py`
**文档**: `README_AMLO_AUDIT_FEATURES.md`

#### 测试覆盖范围 (Test Coverage)

**Part 1: 预约兑换审核页面 (Reservation Audit Page)** - 7项功能
- ✅ 查询功能: 预约记录列表查询，支持分页
- ✅ 时间范围筛选: 按日期范围筛选预约记录
- ✅ 状态筛选: pending/approved/rejected/completed状态过滤
- ✅ 审核功能: 审核通过预约申请
- ✅ 驳回功能: 审核驳回预约申请（需提供驳回原因）
- ✅ 反审核功能: 将已审核记录回退到待审批状态
- ✅ 历史交易查询: 查询客户的历史预约记录

**Part 2: AMLO报告查询页面 (AMLO Report Query Page)** - 7项功能
- ✅ 报告列表显示: 分页显示AMLO报告列表
- ✅ 时间差计算: 计算报告创建时间与当前时间的差值
- ✅ 未上报记录蓝色显示: is_reported=false的记录显示蓝色标记
- ✅ 超期记录红色显示: 超过1天未上报的记录显示红色警告
- ✅ "请立即上报"提示: 超期记录显示紧急提示
- ✅ 标记已上报功能: 批量标记报告为已上报
- ✅ PDF下载功能: 生成并下载AMLO报告PDF

**Part 3: 状态流转验证 (Status Transitions)** - 5种状态流转
- ✅ pending → approved: 审核通过
- ✅ pending → rejected: 审核驳回
- ✅ approved → pending: 反审核回退
- ✅ approved → completed: 完成交易
- ✅ completed → reported: 标记已上报

#### 关键API端点 (Key API Endpoints)

```bash
# 查询预约记录
GET /api/amlo/reservations?status={status}&start_date={date}&end_date={date}

# 审核预约
POST /api/amlo/reservations/{id}/audit
{
  "action": "approve",  # or "reject"
  "remarks": "审核备注"
}

# 反审核
POST /api/amlo/reservations/{id}/reverse-audit
{
  "remarks": "反审核原因"
}

# 查询AMLO报告
GET /api/amlo/reports?is_reported={true|false}

# 标记已上报
POST /api/amlo/reports/mark-reported
{
  "ids": [1, 2, 3]
}

# 生成PDF
GET /api/amlo/reports/{id}/generate-pdf
```

#### 前端实现要点 (Frontend Implementation)

**超期记录红色显示逻辑**:
```javascript
isOverdue(report) {
  if (report.is_reported) return false;
  const created = new Date(report.created_at);
  const now = new Date();
  const days_diff = Math.floor((now - created) / (1000 * 60 * 60 * 24));
  return days_diff > 1;  // 超过1天为超期
}
```

**Vue组件示例**:
```vue
<tr :class="{'table-info': !report.is_reported, 'table-danger': isOverdue(report)}">
  <td>{{ report.report_no }}</td>
  <td>
    <span v-if="isOverdue(report)" class="badge badge-danger">
      超期 {{ getDaysOverdue(report) }} 天 - 请立即上报
    </span>
    <span v-else-if="!report.is_reported" class="badge badge-primary">
      未上报
    </span>
  </td>
</tr>
```

### 3. BOT报告完整测试 (BOT Reports Tests)

**文件**: `test_all_bot_reports.py`
**文档**: `README_ALL_BOT_REPORTS.md`

#### 测试覆盖的4种BOT报告类型

| 报告类型 | 触发条件 | 数据库表 | 阈值 |
|---------|---------|---------|------|
| BOT_BuyFX | 买入外币 | BOT_BuyFX | > 20,000 USD等值 |
| BOT_SellFX | 卖出外币 | BOT_SellFX | > 20,000 USD等值 |
| BOT_FCD | 使用FCD账户 | BOT_FCD | > 50,000 USD等值 |
| BOT_Provider | 余额调节 | BOT_Provider | > 20,000 USD等值 |

**关键验证点**:
- ✅ 触发条件正确判断（基于USD等值）
- ✅ BOTflag和FCDflag正确设置
- ✅ 报告数据正确写入数据库
- ✅ 所有必填字段完整且准确
- ✅ USD等值计算正确（EUR/其他货币转USD）

### 4. 网点数据完全隔离测试 (Branch Data Isolation Tests)

**文件**: `test_branch_isolation.py`
**文档**: `README_BRANCH_ISOLATION.md`

#### 测试目标 (Test Objectives)

验证系统的多网点数据完全隔离功能：

**核心原则**: **Branch 1的数据，Branch 2完全看不到**

#### 隔离验证范围 (Isolation Scope)

| 数据类型 | 隔离要求 | 验证方法 |
|---------|---------|---------|
| 预约记录 | Branch间不可见 | 跨网点查询返回空 |
| AMLO报告 | Branch间不可见 | 跨网点查询返回空 |
| 交易记录 | Branch间不可见 | 跨网点查询返回空 |
| BOT报告 | Branch间不可见 | 跨网点查询返回空 |
| 直接访问 | 拒绝跨Branch访问 | 返回403/404 |

#### 测试场景 (Test Scenarios)

**Test 1: 预约数据隔离**
```
Branch 1创建预约 → Branch 1可查询 → Branch 2查询返回空
```

**Test 2: 报告数据隔离**
```
Branch 1生成AMLO报告 → Branch 1可查询 → Branch 2查询返回空
```

**Test 3: 交易数据隔离**
```
Branch 1执行交易 → Branch 1可查询 → Branch 2查询返回空
```

**Test 4: 触发规则网点隔离**
```
验证触发规则支持branch_id=NULL(全局)或branch_id=1,2,...(网点特定)
```

**Test 5: branch_id正确性**
```
验证所有创建的记录都包含正确的branch_id字段
```

**Test 6: 跨网点直接访问拒绝**
```
Branch 2尝试直接访问Branch 1的资源ID → 返回403 Forbidden
```

#### 业务背景 (Business Context)

**为什么需要网点隔离？**

1. **数据安全**: 各网点不应看到其他网点的客户数据
2. **隐私保护**: 防止客户信息跨网点泄露
3. **合规要求**: 符合数据保护法规（PDPA, GDPR等）
4. **审计追踪**: 每条记录必须明确归属到具体网点
5. **权限管理**: 用户只能操作自己网点的数据

#### 技术实现 (Technical Implementation)

**后端API层面**:
```python
# 所有查询API自动过滤branch_id
def get_reservations():
    reservations = db.query(Reservation).filter_by(
        branch_id=current_user.branch_id  # 关键: branch过滤
    ).all()
    return reservations

# 所有单记录API检查branch权限
def get_reservation(id):
    reservation = db.query(Reservation).get(id)
    if reservation.branch_id != current_user.branch_id:
        return 403, "您无权访问其他网点的数据"
    return 200, reservation
```

**数据库层面**:
```sql
-- 所有业务表必须包含branch_id
ALTER TABLE Reserved_Transaction ADD COLUMN branch_id INT NOT NULL;
ALTER TABLE AMLOReport ADD COLUMN branch_id INT NOT NULL;
ALTER TABLE exchange_transactions ADD COLUMN branch_id INT NOT NULL;

-- 创建索引提高查询性能
CREATE INDEX idx_reservations_branch ON Reserved_Transaction(branch_id);
CREATE INDEX idx_reports_branch ON AMLOReport(branch_id);
```

#### 前置条件 (Prerequisites)

测试需要两个不同网点的用户：

**Branch 1用户** (已存在):
- login_code: `admin`
- password: `admin123`
- branch_id: 1

**Branch 2用户** (测试会自动创建，或手动创建):
- login_code: `branch2_user`
- password: `branch2_pass`
- branch_id: 2

#### 预期结果 (Expected Results)

**成功的隔离**:
```
Branch 1: 创建10条预约
Branch 1查询: 返回10条预约 ✅
Branch 2查询: 返回0条预约 ✅ (完全隔离)
```

**失败的隔离** (需要修复):
```
Branch 1: 创建10条预约
Branch 1查询: 返回10条预约 ✅
Branch 2查询: 返回10条预约 ❌ (隔离失败！)
```

### 5. BOT Provider报告测试 (BOT Provider Tests)

**文件**: `test_bot_provider_eur_adjustment.py`
**文档**: `README_BOT_PROVIDER_EUR_TEST.md`

#### EUR转USD等值触发测试 (EUR to USD Equivalent Trigger Test)

**测试目的**: 验证非USD外币调节时，系统能正确：
1. 将外币金额转换为USD等值
2. 根据USD等值判断是否触发BOT_Provider报告
3. 在报告中正确记录USD等值金额

**测试参数**:
```python
EUR_BUY_RATE = 38.0         # EUR买入汇率（THB）
USD_SELL_RATE = 34.0        # USD卖出汇率（THB）
EUR_ADJUSTMENT_AMOUNT = 20000  # 调节EUR金额
```

**USD等值计算**:
```
USD等值 = 外币金额 × 外币买入汇率 ÷ USD卖出汇率
USD Equivalent = 20,000 EUR × 38.0 ÷ 34.0
              ≈ 22,352.94 USD
```

**预期结果**:
- ✅ 应该触发: 22,352.94 >= 20,000 (阈值)
- ✅ BOT_Provider报告生成
- ✅ 报告中usd_equivalent字段 ≈ 22,352.94

**验证步骤**:
1. 登录系统
2. 获取EUR和USD货币ID
3. 设置EUR买入汇率 = 38.0 THB
4. 设置USD卖出汇率 = 34.0 THB
5. 调节EUR余额 +20,000
6. 验证BOT_Provider触发
7. 验证usd_equivalent字段正确

## 预期输出 (Expected Output)

### 成功运行输出示例 (Successful Run Example)

```
====================================================================================================
                        Currency Exchange System - Comprehensive Test Suite
                                    外汇管理系统 - 综合测试套件
====================================================================================================

⏰ Start Time: 2025-10-13 14:30:00
📍 Working Directory: D:\code\exchangenew
🐍 Python Version: 3.11.5
====================================================================================================

====================================================================================================
  🔐 AMLO Compliance Tests
  AMLO合规性测试 - 预约、审核、交易、超期提醒
====================================================================================================

[Login] Authenticating...
  [OK] Login successful

================================================================================
Scenario A: Complete Reservation to Transaction Flow
================================================================================

[Step 1/20] Get USD currency ID...
  [OK] USD currency ID: 2

... (中间步骤省略) ...

[Step 20/20] Test summary...
  Reservation ID: 123
  Transaction ID: 456
  Report ID: 789
  [PASS] Scenario A completed successfully!

================================================================================
Scenario B: Reverse Audit Flow
================================================================================

... (测试输出) ...
  [PASS] Scenario B completed successfully!

================================================================================
Scenario C: Overdue Alert Test
================================================================================

... (测试输出) ...
  [PASS] Scenario C completed successfully!

====================================================================================================
  🏦 BOT Provider Tests
  BOT Provider报告测试 - EUR转USD等值触发
====================================================================================================

[Step 1] Login...
  [OK] Login successful

[Step 5] Adjust EUR balance by 20,000...
  Formula: USD equivalent = 20,000 * 38.0 / 34.0
  Calculated: 22,352.94 USD
  [OK] EUR adjustment successful
  BOT report generated: True

[Step 6] Verify BOT_Provider trigger...
  [PASS] ✓ BOT_Provider triggered as expected!

[Step 7] Verify usd_equivalent field...
  [PASS] ✓ USD equivalent field is correct!

====================================================================================================
                                       📊 Test Results Summary
                                           测试结果汇总
====================================================================================================

🔐 AMLO Compliance Tests:
  ✅ PASS - Login Authentication
  ✅ PASS - Scenario A: Reservation to Transaction (20 steps)
  ✅ PASS - Scenario B: Reverse Audit (4 steps)
  ✅ PASS - Scenario C: Overdue Alert (5 steps)

🔍 AMLO Audit Features Tests:
  ✅ PASS - Reservation Query Function
  ✅ PASS - Time Range Filter
  ✅ PASS - Status Filter
  ✅ PASS - Approve Function
  ✅ PASS - Reject Function
  ✅ PASS - Reverse Audit Function
  ✅ PASS - History Query Function
  ✅ PASS - Report List Display
  ✅ PASS - Time Difference Calculation
  ✅ PASS - Unreported Records (Blue)
  ✅ PASS - Overdue Records (Red)
  ✅ PASS - Immediate Report Prompt
  ✅ PASS - Mark Reported Function
  ✅ PASS - PDF Download Function
  ✅ PASS - Status: pending → approved
  ✅ PASS - Status: pending → rejected
  ✅ PASS - Status: approved → pending (reverse)
  ✅ PASS - Status: approved → completed
  ✅ PASS - Status: completed → reported

🏢 Branch Data Isolation Tests:
  ✅ PASS - Branch 1 Login
  ✅ PASS - Branch 2 Login
  ✅ PASS - Reservation Data Isolation
  ✅ PASS - Report Data Isolation
  ✅ PASS - Transaction Data Isolation
  ✅ PASS - Trigger Rule Branch Isolation
  ✅ PASS - Branch ID Correctness
  ✅ PASS - Cross-Branch Access Denied

🏦 BOT Reports Tests:
  ✅ PASS - BOT_BuyFX: 买入外币 > 20,000 USD
  ✅ PASS - BOT_SellFX: 卖出外币 > 20,000 USD
  ✅ PASS - BOT_FCD: FCD账户 > 50,000 USD
  ✅ PASS - BOT_Provider: 余额调节 > 20,000 USD
  ✅ PASS - BOT_Provider: EUR转USD等值测试

----------------------------------------------------------------------------------------------------

📈 Overall Statistics:
  Total Tests Run:    35
  Tests Passed:       35 ✅
  Tests Failed:       0 ❌
  Tests Skipped:      0 ⏭️
  Pass Rate:          100.0%
  Duration:           145.60 seconds

====================================================================================================
                              ✅ ALL TESTS PASSED! 所有测试通过！
====================================================================================================
```

## 常见问题 (Common Issues)

### Q1: 测试失败 - 无法连接到后端

**症状**:
```
[FAIL] Login failed: Connection refused
```

**解决方案**:
```bash
# 1. 确认后端服务运行在5001端口
python src/main.py

# 2. 检查端口是否被占用
netstat -ano | findstr :5001

# 3. 修改测试配置中的BASE_URL（如果使用不同端口）
```

### Q2: 测试失败 - 登录认证失败

**症状**:
```
[FAIL] Login failed: Invalid credentials
```

**解决方案**:
```bash
# 1. 确认数据库已初始化
python src/init_db.py

# 2. 确认测试用户存在
# 默认: admin/admin123

# 3. 检查数据库连接配置（.env文件）
```

### Q3: EUR或USD货币不存在

**症状**:
```
[FAIL] EUR currency not found
```

**解决方案**:
```bash
# 重新初始化数据库和基础货币
python src/init_db.py
```

### Q4: BOT_Provider未触发

**症状**:
```
[FAIL] BOT_Provider NOT triggered but SHOULD!
```

**可能原因**:
1. 汇率未正确设置
2. 触发规则配置错误
3. USD等值计算逻辑错误

**调试方法**:
```bash
# 1. 检查触发规则
python src/check_trigger_rules.py

# 2. 查看详细日志
python src/tests/test_bot_provider_eur_adjustment.py --verbose

# 3. 检查数据库中的汇率
SELECT * FROM exchange_rates WHERE currency_code IN ('EUR', 'USD');
```

### Q5: AMLO报告未生成

**症状**:
```
[WARN] No AMLO report found yet
```

**可能原因**:
1. 交易金额未超过阈值（2,000,000 THB）
2. AMLO触发规则未配置
3. PDF生成失败

**解决方案**:
```bash
# 1. 检查AMLO触发条件
python src/check_trigger_conditions.py

# 2. 检查AMLO表单文件
ls src/static/amlo_forms/

# 3. 检查字体文件
ls src/fonts/
```

## 测试数据清理 (Test Data Cleanup)

测试完成后，可以清理测试数据：

```sql
-- 清理AMLO场景测试数据
DELETE FROM Reserved_Transaction WHERE customer_id LIKE 'TEST%' OR customer_id LIKE 'REVERSE_TEST%';
DELETE FROM AMLOReport WHERE customer_id LIKE 'TEST%';

-- 清理AMLO审计功能测试数据
DELETE FROM Reserved_Transaction WHERE customer_id LIKE 'TEST_APPROVE_%' OR customer_id LIKE 'TEST_REJECT_%'
   OR customer_id LIKE 'TEST_REVERSE_%' OR customer_id LIKE 'TEST_TRANS_%';
DELETE FROM AMLOReport WHERE customer_id LIKE 'TEST_AUDIT_%';

-- 清理BOT报告测试数据
DELETE FROM BOT_BuyFX WHERE customer_id LIKE 'TEST_BOT_%';
DELETE FROM BOT_SellFX WHERE customer_id LIKE 'TEST_BOT_%';
DELETE FROM BOT_FCD WHERE customer_id LIKE 'TEST_BOT_%';
DELETE FROM BOT_Provider WHERE adjustment_reason LIKE 'BOT_Provider test%' OR adjustment_reason LIKE 'Test EUR to USD%';

-- 清理测试交易
DELETE FROM exchange_transactions WHERE customer_id LIKE 'TEST%';
```

或使用清理脚本（如果存在）:
```bash
python src/utils/cleanup_test_data.py
```

## 扩展测试 (Extended Testing)

### 添加新的测试场景

1. **创建测试文件**: `src/tests/test_your_feature.py`
2. **编写测试类**:
```python
class YourFeatureTester:
    def __init__(self):
        self.session = requests.Session()

    def test_scenario(self):
        # 测试逻辑
        pass
```

3. **集成到主运行器**: 在 `run_all_tests.py` 中添加:
```python
from tests.test_your_feature import YourFeatureTester

def run_your_tests(self):
    tester = YourFeatureTester()
    result = tester.test_scenario()
    self.results['your_feature'] = result
```

### 建议的额外测试场景

1. **AMLO场景D**: 审核驳回流程
2. **AMLO场景E**: 批量上报测试
3. **BOT场景**: 其他外币（GBP, JPY, CNY）测试
4. **边界值测试**: 正好20,000 USD的情况
5. **压力测试**: 大量并发预约和交易

## 相关文档 (Related Documentation)

- **AMLO场景测试详解**: `README_AMLO_SCENARIOS.md`
- **AMLO审计功能测试**: `README_AMLO_AUDIT_FEATURES.md`
- **BOT报告完整测试**: `README_ALL_BOT_REPORTS.md`
- **BOT Provider EUR测试**: `README_BOT_PROVIDER_EUR_TEST.md`
- **系统架构**: `CLAUDE.md` (项目根目录)
- **API文档**: `src/routes/app_*.py` 各路由文件
- **数据库设计**: `src/models/*_models.py`

## 技术支持 (Technical Support)

如遇到问题，请检查：
1. 后端日志文件
2. 数据库连接状态
3. 触发规则配置
4. 汇率数据完整性

调试工具：
- `src/check_compliance_status.py` - 检查合规性数据
- `src/check_trigger_conditions.py` - 检查触发条件
- `src/check_country_data.py` - 检查国家/货币数据

## 测试覆盖率 (Test Coverage)

当前测试覆盖的功能模块：

| 模块 | 覆盖场景 | 测试数量 | 状态 |
|------|---------|---------|------|
| AMLO预约系统 | 创建、审核、反审核、完成 | 3场景 | ✅ 完整 |
| AMLO审计功能 | 查询、筛选、审核、驳回、反审核、历史查询 | 19项功能 | ✅ 完整 |
| AMLO报告生成 | PDF生成、超期提醒、标记上报 | 7项功能 | ✅ 完整 |
| 网点数据隔离 | 预约、报告、交易、触发规则、权限控制 | 8项测试 | ✅ 完整 |
| BOT报告系统 | BuyFX, SellFX, FCD, Provider | 4种报告 | ✅ 完整 |
| BOT Provider | USD/EUR调节触发、USD等值计算 | 专项测试 | ✅ 完整 |
| 交易执行 | 大额交易AMLO联动 | 场景测试 | ✅ 完整 |
| 汇率管理 | USD等值计算、多货币支持 | 集成测试 | ✅ 完整 |

**总测试统计**:
- AMLO场景测试: 3个场景（29个步骤）
- AMLO审计功能测试: 19项功能验证
- 网点数据隔离测试: 8项隔离验证
- BOT报告测试: 5种触发场景
- 总覆盖率: 核心业务功能100%

## 持续集成 (CI/CD Integration)

可以将测试集成到CI/CD流程：

```yaml
# .github/workflows/test.yml 示例
name: Run Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Setup Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.11'
      - name: Install dependencies
        run: pip install -r requirements.txt
      - name: Run tests
        run: python src/tests/run_all_tests.py
```

---

**最后更新**: 2025-10-13
**维护者**: Exchange System Development Team
