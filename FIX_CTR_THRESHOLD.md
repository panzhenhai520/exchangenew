# CTR触发阈值问题诊断与修复

**问题**: 1,948,299 THB触发了CTR报告
**标准阈值**: 2,000,000 THB (200万)
**差距**: 51,701 THB

---

## 🔍 诊断步骤

### 步骤1: 检查数据库中的实际规则

**SQL查询**:
```sql
SELECT
    id,
    rule_name,
    rule_expression,
    is_active,
    priority,
    warning_message_cn
FROM trigger_rules
WHERE report_type = 'AMLO-1-01'
ORDER BY priority DESC, id;
```

**在MySQL客户端中运行**:
```bash
mysql -u root -p -D exchangenew
```

然后执行上面的SQL。

---

### 步骤2: 查看规则详情

**检查要点**:

1. **`rule_expression` 字段的JSON内容**:
   ```json
   {
     "logic": "AND",
     "conditions": [{
       "field": "total_amount",
       "operator": ">=",
       "value": 2000000
     }]
   }
   ```

2. **`is_active` 字段**: 应该是 `1` (激活)

3. **`priority` 字段**: 优先级高的先匹配

---

### 步骤3: 检查是否有多条规则

可能存在多条AMLO-1-01规则，其中一条阈值较低：

```sql
SELECT
    id,
    rule_name,
    JSON_EXTRACT(rule_expression, '$.conditions[0].value') as threshold_value,
    is_active
FROM trigger_rules
WHERE report_type = 'AMLO-1-01'
  AND is_active = 1
ORDER BY CAST(JSON_EXTRACT(rule_expression, '$.conditions[0].value') AS UNSIGNED);
```

这会按阈值从低到高排序，找出最低的阈值。

---

## 🛠️ 修复方法

### 方法1: 重新配置标准规则（推荐）

运行标准配置脚本：

```bash
python src/migrations/configure_amlo_trigger_rules.py
```

这会：
1. 删除所有旧的AMLO-1-01规则
2. 创建标准的200万THB阈值规则

---

### 方法2: 手动更新SQL

如果只想修改阈值而不删除其他配置：

```sql
UPDATE trigger_rules
SET rule_expression = JSON_SET(
    rule_expression,
    '$.conditions[0].value',
    2000000
)
WHERE report_type = 'AMLO-1-01'
  AND JSON_EXTRACT(rule_expression, '$.conditions[0].field') = 'total_amount';
```

---

### 方法3: 通过管理界面修改

1. 登录系统
2. 进入 **系统维护** → **标准设置** → **触发规则**
3. 找到AMLO-1-01规则
4. 修改阈值为 2,000,000
5. 保存

---

## 📋 验证修复

### 1. 检查规则是否正确

```sql
SELECT
    rule_name,
    JSON_EXTRACT(rule_expression, '$.conditions[0].value') as threshold,
    is_active
FROM trigger_rules
WHERE report_type = 'AMLO-1-01';
```

**预期输出**:
```
rule_name: AMLO-1-01单笔大额
threshold: 2000000
is_active: 1
```

---

### 2. 测试交易

**测试用例**:

| 金额 (THB) | 应该触发CTR? | 说明 |
|-----------|------------|------|
| 1,948,299 | ❌ 否 | 低于200万 |
| 1,999,999 | ❌ 否 | 低于200万 |
| 2,000,000 | ✅ 是 | 等于200万 |
| 2,000,001 | ✅ 是 | 超过200万 |
| 2,500,000 | ✅ 是 | 超过200万 |

---

## 🔍 深入诊断：检查触发日志

### 查看实际触发的规则ID

如果您的预约记录ID是54：

```sql
SELECT
    r.id,
    r.reservation_no,
    r.local_amount,
    r.report_type,
    r.form_data
FROM Reserved_Transaction r
WHERE r.id = 54;
```

检查：
1. `local_amount` 字段的实际值
2. `report_type` 是否确实是 AMLO-1-01
3. `form_data` 中是否有额外的金额累计信息

---

### 查看触发日志（如果有）

检查系统日志表：

```sql
SELECT
    action_type,
    details,
    created_at
FROM system_logs
WHERE action_type LIKE '%AMLO%'
  AND details LIKE '%1948299%'
ORDER BY created_at DESC
LIMIT 10;
```

---

## 🎯 标准阈值参考

根据泰国AMLO监管要求：

| 报告类型 | 阈值 | 说明 |
|---------|------|------|
| **AMLO-1-01 (CTR)** | **≥ 2,000,000 THB** | **现金交易报告** |
| AMLO-1-02 (ATR) | ≥ 8,000,000 THB | 资产交易报告 |
| AMLO-1-03 (STR) | ≥ 5,000,000 THB | 30天累计可疑交易 |

**注意**:
- CTR是**单笔交易**阈值
- STR是**累计交易**阈值

---

## ⚠️ 可能的问题场景

### 场景1: 累计触发而非单笔

如果客户在**同一天**或**短时间内**有多笔交易：

例如：
- 第1笔: 500,000 THB
- 第2笔: 800,000 THB
- 第3笔: 648,299 THB
- **累计**: 1,948,299 THB

如果系统配置了"当日累计触发"规则，那么可能是累计金额达到了某个阈值。

**检查方法**:
```sql
SELECT
    customer_id,
    SUM(local_amount) as daily_total,
    COUNT(*) as transaction_count,
    DATE(created_at) as transaction_date
FROM exchange_transactions
WHERE customer_id = '您的客户ID'
  AND DATE(created_at) = '2025-10-28'  -- 交易日期
GROUP BY customer_id, DATE(created_at);
```

---

### 场景2: 规则表达式错误

可能规则配置成了：
```json
{
  "conditions": [{
    "field": "total_amount",
    "operator": "<=",  // ❌ 错误：小于等于
    "value": 2000000
  }]
}
```

这样会导致低于200万的也触发。

---

## 🚀 快速修复脚本

创建修复脚本：

```bash
python src/migrations/configure_amlo_trigger_rules.py
```

输出应该显示：
```
配置的规则:
  1. AMLO-1-01 (CTR-现金交易报告): 单笔 >= 200万THB
  2. AMLO-1-02 (ATR-资产交易报告): 金额 >= 800万THB
  3. AMLO-1-03 (STR-可疑交易报告): 30天累计 >= 500万THB
```

---

## 📞 需要提供的信息

为了更准确诊断，请提供：

1. **数据库查询结果**:
   ```sql
   SELECT * FROM trigger_rules WHERE report_type = 'AMLO-1-01';
   ```

2. **预约记录详情**:
   ```sql
   SELECT * FROM Reserved_Transaction WHERE id = 54;
   ```

3. **触发时的后端日志** (包含触发规则的日志)

4. **客户当天的所有交易**:
   ```sql
   SELECT * FROM exchange_transactions
   WHERE customer_id = '您的客户ID'
     AND DATE(created_at) = '2025-10-28';
   ```

---

**总结**: 1,948,299 THB **不应该触发标准的CTR报告**（标准阈值200万）。如果触发了，说明数据库中的规则被修改过或有其他累计规则。
