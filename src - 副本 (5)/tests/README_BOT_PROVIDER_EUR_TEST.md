# BOT Provider EUR调节测试文档

## 测试目的

验证当调节**非USD外币**（如EUR）余额时，系统能正确：
1. 将外币金额转换为USD等值
2. 根据USD等值判断是否触发BOT_Provider报告
3. 在报告中正确记录USD等值金额

## 测试场景

### 场景参数
- **调节货币**: EUR（欧元）
- **调节金额**: 20,000 EUR
- **EUR买入汇率**: 38.0 THB/EUR
- **USD卖出汇率**: 34.0 THB/USD
- **BOT_Provider阈值**: 20,000 USD

### USD等值计算公式

```
USD等值 = 外币金额 × 外币买入汇率 ÷ USD卖出汇率
USD等值 = 20,000 EUR × 38.0 ÷ 34.0
USD等值 ≈ 22,352.94 USD
```

### 预期结果

- **应该触发**: ✓ 是（22,352.94 >= 20,000）
- **BOT_Provider报告**: 应该生成
- **报告中usd_equivalent字段**: 应该约等于 22,352.94

## 代码实现位置

### 后端实现

**触发检查逻辑**: `src/routes/app_balance.py` 第344-420行

```python
# 第369-370行：USD等值计算
usd_equivalent = float(amount) * float(adj_currency_rate.buy_rate) / float(usd_rate.sell_rate)
```

**关键代码片段**:
```python
# 获取USD对本币的汇率
usd_rate = session.query(ExchangeRate).filter(
    ExchangeRate.branch_id == current_user['branch_id'],
    ExchangeRate.currency_code == 'USD',
    ExchangeRate.is_active == True
).order_by(ExchangeRate.updated_at.desc()).first()

# 获取调节币种对本币的汇率
adj_currency_rate = session.query(ExchangeRate).filter(
    ExchangeRate.branch_id == current_user['branch_id'],
    ExchangeRate.currency_code == currency.currency_code,
    ExchangeRate.is_active == True
).order_by(ExchangeRate.updated_at.desc()).first()

# 计算USD等值
if currency.currency_code == 'USD':
    usd_equivalent = float(amount)
elif adj_currency_rate and usd_rate:
    usd_equivalent = float(amount) * float(adj_currency_rate.buy_rate) / float(usd_rate.sell_rate)
```

**报告生成**: `src/services/bot_report_service.py` 第341-429行

```python
@staticmethod
def generate_bot_provider(
    db_session: Session,
    adjustment_id: int,
    adjustment_data: Dict[str, Any]
) -> Optional[int]:
    """生成BOT Provider报告（余额调节触发）"""
    # 插入BOT_Provider表，包含usd_equivalent字段
```

### 触发规则引擎

**规则检查**: `src/services/repform/rule_engine.py`

```python
RuleEngine.check_triggers(
    session, 'BOT_Provider',
    {
        'adjustment_type': 'increase',
        'usd_equivalent': usd_equivalent,
        'currency_code': currency.currency_code,
        'adjustment_amount': float(amount)
    },
    current_user['branch_id']
)
```

## 运行测试

### 方法1: 独立测试脚本

```bash
# 启动后端服务
python src/main.py

# 在另一个终端运行测试
cd src/tests
python test_bot_provider_eur_adjustment.py
```

### 方法2: 作为完整测试套件的一部分

```bash
# 运行所有BOT Provider测试（包括EUR场景）
python src/tests/test_bot_provider.py
```

## 测试步骤详解

### Step 1: 登录
- 使用admin/admin123登录
- 获取JWT token

### Step 2: 获取货币ID
- 查询系统中的EUR和USD货币
- 获取currency_id用于后续操作

### Step 3: 设置EUR买入汇率
```json
{
  "currency_id": <EUR_ID>,
  "buy_rate": 38.0,
  "sell_rate": 39.0,
  "rate_date": "2025-10-13"
}
```

### Step 4: 设置USD卖出汇率
```json
{
  "currency_id": <USD_ID>,
  "buy_rate": 33.5,
  "sell_rate": 34.0,
  "rate_date": "2025-10-13"
}
```

### Step 5: 调节EUR余额
```json
{
  "currency_id": <EUR_ID>,
  "adjustment_amount": 20000,
  "adjustment_type": "increase",
  "reason": "Test EUR to USD equivalent conversion"
}
```

**API端点**: `POST /api/balance-management/adjust`

**返回字段验证**:
```json
{
  "success": true,
  "bot_report_generated": true,  // 应该为true
  "transaction": {
    "id": 123,
    "transaction_no": "ADJ20251013..."
  }
}
```

### Step 6: 验证触发结果
- 检查`bot_report_generated`标志
- 对比实际触发与预期触发

### Step 7: 验证USD等值字段
- 查询BOT_Provider表
- 验证usd_equivalent字段 ≈ 22,352.94
- 允许±1 USD的浮点误差

## 数据库表结构

### BOT_Provider表
```sql
CREATE TABLE bot_provider (
    id INT AUTO_INCREMENT PRIMARY KEY,
    adjustment_id INT,
    currency_code VARCHAR(10),
    currency_name VARCHAR(100),
    provider_amount DECIMAL(15,2),
    local_amount_thb DECIMAL(15,2),
    usd_equivalent DECIMAL(15,2),  -- 重点验证字段
    adjustment_reason TEXT,
    adjustment_date DATE,
    json_data JSON,
    branch_id INT,
    operator_id INT,
    is_reported BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

## 预期输出

### 成功场景输出示例

```
================================================================================
BOT_Provider EUR Adjustment Test
================================================================================

Test Configuration:
  EUR Buy Rate: 38.0 THB
  USD Sell Rate: 34.0 THB
  EUR Adjustment Amount: 20,000 EUR
  Expected USD Equivalent: 22,352.94 USD
  BOT_Provider Threshold: 20,000 USD
  Expected Result: TRIGGER
================================================================================

[Step 1] Login...
  [OK] Login successful

[Step 2] Get EUR and USD currency IDs...
  [OK] EUR currency found: id=3
  [OK] USD currency found: id=2

[Step 3] Set EUR buy rate = 38.0 THB...
  [OK] EUR rate set successfully

[Step 4] Set USD sell rate = 34.0 THB...
  [OK] USD rate set successfully

[Step 5] Adjust EUR balance by 20,000...
  Formula: USD equivalent = 20,000 * 38.0 / 34.0
  Calculated: 22,352.94 USD
  [OK] EUR adjustment successful
  Transaction ID: 456
  Transaction No: ADJ20251013123456
  BOT report generated: True

[Step 6] Verify BOT_Provider trigger...
  [PASS] ✓ BOT_Provider triggered as expected!
  Reason: USD equivalent (22,352.94) >= threshold (20,000)

[Step 7] Verify usd_equivalent field in BOT_Provider report...
  [OK] BOT_Provider report found
  Report ID: 78
  Currency: EUR
  Adjustment Amount: 20,000.00
  USD Equivalent: 22,352.94
  Expected: 22,352.94
  Difference: 0.00
  [PASS] ✓ USD equivalent field is correct!

================================================================================
Test Result
================================================================================
✓ TEST PASSED!

Summary:
  - EUR adjustment: 20,000 EUR
  - EUR buy rate: 38.0 THB
  - USD sell rate: 34.0 THB
  - USD equivalent: 22,352.94 USD
  - BOT_Provider triggered: YES
```

## 常见问题

### Q1: 测试失败：EUR或USD货币不存在
**解决方案**: 确保数据库中已初始化EUR和USD货币
```bash
python src/init_db.py  # 初始化数据库和基础货币
```

### Q2: 测试失败：汇率设置失败
**原因**: 可能没有相应的API端点或权限不足
**检查**:
- 确认`/api/rates/set`端点存在
- 确认admin用户有汇率管理权限

### Q3: USD等值计算不正确
**检查要点**:
1. 确认使用的是**EUR买入汇率**（bank_buy_rate）
2. 确认使用的是**USD卖出汇率**（bank_sell_rate）
3. 计算公式: `EUR金额 × EUR买入汇率 ÷ USD卖出汇率`

### Q4: 触发了但usd_equivalent字段为0
**原因**: 可能在写入数据库时未传递usd_equivalent
**检查**: `bot_report_service.py`的`generate_bot_provider`方法

## 相关测试

### 其他BOT Provider测试场景

1. **Scenario A**: USD小额调节（15,000 USD，不触发）
2. **Scenario B**: USD大额调节（25,000 USD，触发）
3. **Scenario C**: 减少调节（不触发，仅增加才触发）
4. **Scenario D**: EUR转USD等值触发（本测试）

### 扩展测试建议

- 测试其他外币（GBP, JPY, CNY等）
- 测试边界值（正好20,000 USD）
- 测试汇率变化对计算的影响
- 测试多次调节累计触发

## 维护说明

### 当修改相关代码时需要重新测试

1. **汇率计算逻辑变更**: `app_balance.py` 第369-370行
2. **触发条件变更**: 规则引擎或阈值配置
3. **报告生成逻辑变更**: `bot_report_service.py`
4. **USD等值字段变更**: 数据库schema或字段名

### 测试数据清理

```sql
-- 清理测试生成的调节记录
DELETE FROM exchange_transactions WHERE customer_name LIKE 'Test EUR to USD%';

-- 清理测试生成的BOT报告
DELETE FROM bot_provider WHERE adjustment_reason LIKE 'Test EUR to USD%';
```

## 参考文档

- BOT报告规范: 泰国央行外汇报告要求
- USD等值计算标准: IMF SDR计算方法
- 系统架构文档: `CLAUDE.md`
