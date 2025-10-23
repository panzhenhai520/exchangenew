# AMLO触发器测试场景指南

## 清理完成
✅ 已清理 22 条预约记录
✅ 已清理 10 条AMLO报告记录
✅ 数据库已重置，可以开始测试

---

## 触发规则说明

系统配置了三条AMLO触发规则：

1. **CTR (Currency Transaction Report)**
   - 条件: `total_amount >= 2,000,000 THB`
   - 触发: AMLO-1-01
   - 说明: 普通大额现金交易报告

2. **ATR (Asset Transaction Report)**
   - 条件: `total_amount >= 8,000,000 THB` AND `exchange_type == 'asset_backed'`
   - 触发: AMLO-1-01 + AMLO-1-02
   - 说明: 资产抵押大额交易报告

3. **STR (Suspicious Transaction Report)**
   - 条件: `cumulative_amount_30d >= 5,000,000 THB`
   - 触发: AMLO-1-03
   - 说明: 30天累计交易可疑报告

---

## 场景1: CTR - 普通大额交易 💰

### 目标
触发 AMLO-1-01 报告（超过200万THB）

### 测试步骤

1. **登录系统**
   - 用户名: `admin`
   - 密码: `admin123`
   - 网点: 选择任意网点

2. **进入标准兑换页面**
   - 导航: 主菜单 → 标准兑换 / Standard Exchange

3. **输入交易信息**
   ```
   客户信息:
   - 客户姓名: 张三
   - 证件类型: 护照
   - 证件号码: P123456789
   - 国籍: 中国 (CHN)

   交易信息:
   - 交易方向: 买入外币 (Buy)
   - 外币币种: USD (美元)
   - 外币金额: 60,000 USD
   - 汇率: 35.00 THB/USD (系统自动获取当前汇率)
   - 本币金额: 2,100,000 THB (自动计算)

   交易类型:
   - exchange_type: normal (默认值)
   - 保持默认即可，不需要修改
   ```

4. **预期结果**
   - ✅ 系统检测到金额 >= 2,000,000 THB
   - ✅ 弹出"预约AMLO审核"模态框
   - ✅ 显示触发的报告类型: AMLO-1-01
   - ✅ 提示: "该交易需要AMLO合规审核"

5. **填写预约信息**
   ```
   - 资金来源: 工资收入
   - 交易目的: 海外购物
   - 备注: 正常购汇业务
   ```

6. **提交预约**
   - 点击"提交预约"按钮
   - 系统生成预约编号（格式: 001-001-68-XXXXXXX）

7. **验证结果**
   - 导航: AMLO审计 → 预约查询
   - 应该看到一条新的预约记录：
     - 状态: 待审核 (pending)
     - 报告类型: AMLO-1-01
     - 金额: 2,100,000 THB
     - 客户: 张三

---

## 场景2: ATR - 资产抵押大额交易 🏠

### 目标
触发 AMLO-1-01 + AMLO-1-02 报告（超过800万THB且是资产抵押）

### 测试步骤

1. **进入标准兑换页面**（同场景1）

2. **输入交易信息**
   ```
   客户信息:
   - 客户姓名: 李四
   - 证件类型: 护照
   - 证件号码: P987654321
   - 国籍: 中国 (CHN)

   交易信息:
   - 交易方向: 买入外币 (Buy)
   - 外币币种: USD (美元)
   - 外币金额: 250,000 USD
   - 汇率: 35.00 THB/USD
   - 本币金额: 8,750,000 THB (自动计算)

   交易类型:
   - exchange_type: 需要修改为 'asset_backed'
   ```

3. **⚠️ 重要: 修改交易类型**

   由于当前UI未提供资产抵押选项，需要通过开发者工具修改：

   **方法1: 使用浏览器开发者工具**
   ```
   1. 按F12打开开发者工具
   2. 切换到Console标签
   3. 在提交前执行以下代码:

   // 找到表单数据对象并修改exchange_type
   // 这个需要根据实际表单结构调整
   document.querySelector('[name="exchange_type"]').value = 'asset_backed';

   或者在提交时拦截请求：
   // 在Network标签中找到提交请求
   // 编辑并重新发送，将exchange_type改为'asset_backed'
   ```

   **方法2: 修改前端代码（临时测试）**
   ```javascript
   // 在src/views/ExchangeView.vue或类似文件中
   // 找到表单提交逻辑，临时添加：
   transactionData.exchange_type = 'asset_backed';
   ```

4. **预期结果**
   - ✅ 系统检测到金额 >= 8,000,000 THB
   - ✅ 系统检测到 exchange_type == 'asset_backed'
   - ✅ 弹出"预约AMLO审核"模态框
   - ✅ 显示触发的报告类型: AMLO-1-01, AMLO-1-02
   - ✅ 提示: "该交易需要AMLO合规审核（资产抵押大额交易）"

5. **填写预约信息**
   ```
   - 资金来源: 房产抵押贷款
   - 交易目的: 海外投资
   - 资产类型: 房产
   - 资产价值: 10,000,000 THB
   - 备注: 用于海外房产投资
   ```

6. **验证结果**
   - 预约记录应显示:
     - 状态: 待审核 (pending)
     - 报告类型: AMLO-1-01, AMLO-1-02
     - 金额: 8,750,000 THB
     - 客户: 李四
     - 交易类型: asset_backed

---

## 场景3: STR - 30天累计交易 📊

### 目标
触发 AMLO-1-03 报告（30天累计金额 >= 500万THB）

### 测试步骤

**方式A: 通过多笔交易累计（真实场景）**

1. **第1笔交易（第1天）**
   ```
   客户: 王五 (P111222333)
   金额: 1,800,000 THB
   说明: 不触发CTR（低于200万）
   ```

2. **第2笔交易（第5天）**
   ```
   客户: 王五 (同一客户)
   金额: 1,900,000 THB
   累计: 3,700,000 THB (还未达到500万)
   ```

3. **第3笔交易（第10天）**
   ```
   客户: 王五 (同一客户)
   金额: 1,500,000 THB
   累计: 5,200,000 THB
   触发: ✅ AMLO-1-03 (STR)
   ```

4. **预期结果**
   - 系统计算30天累计金额
   - 触发 AMLO-1-03 报告
   - 提示: "该客户30天累计交易金额超过500万THB"

**方式B: 使用测试脚本（快速测试）**

创建测试脚本模拟累计交易：

```python
# test_cumulative_trigger.py
import requests

BASE_URL = "http://192.168.0.17:5001"
token = "your_token_here"  # 登录后获取

headers = {
    "Authorization": f"Bearer {token}",
    "Content-Type": "application/json"
}

# 模拟累计金额
test_data = {
    "customer_id": "P111222333",
    "customer_name": "王五",
    "cumulative_amount_30d": 5200000,  # 伪造30天累计金额
    "current_amount": 1500000
}

response = requests.post(
    f"{BASE_URL}/api/amlo/check-trigger",
    headers=headers,
    json=test_data
)

print(response.json())
```

---

## 审核流程测试 ✅

### 1. 查看预约列表
- 导航: AMLO审计 → 预约查询
- 应该看到3条预约记录（对应3个场景）

### 2. 查看预约详情
- 点击任意预约的"查看详情"按钮
- 验证信息显示正确：
  - 基本信息（编号、类型、状态）
  - 客户信息（姓名、证件、国籍）
  - 交易信息（金额、币种、方向）

### 3. 审核通过
1. 选择"待审核"状态的预约
2. 点击"审核通过"按钮
3. 可选填写审核备注
4. 点击"确认通过"
5. 验证：
   - ✅ 列表自动刷新
   - ✅ 状态变为"已通过"（绿色徽章）
   - ✅ 显示"查看PDF"按钮

### 4. 审核拒绝
1. 选择另一条"待审核"状态的预约
2. 点击"审核拒绝"按钮
3. **必须填写拒绝原因**，例如：
   ```
   - 资金来源证明不完整
   - 客户身份信息需要进一步核实
   - 交易目的不明确
   ```
4. 可选填写审核备注
5. 点击"确认拒绝"
6. 验证：
   - ✅ 列表自动刷新
   - ✅ 状态变为"已拒绝"（红色徽章）
   - ✅ 查看详情可看到拒绝原因

---

## 测试检查清单 ☑️

### 场景1 (CTR) 检查项
- [ ] 金额输入 2,100,000 THB
- [ ] 触发 AMLO-1-01
- [ ] 弹出预约模态框
- [ ] 成功创建预约记录
- [ ] 预约状态为"待审核"
- [ ] 可以审核通过
- [ ] 可以审核拒绝

### 场景2 (ATR) 检查项
- [ ] 金额输入 8,750,000 THB
- [ ] exchange_type 设置为 'asset_backed'
- [ ] 触发 AMLO-1-01 + AMLO-1-02
- [ ] 弹出预约模态框
- [ ] 成功创建预约记录
- [ ] 预约记录包含资产信息

### 场景3 (STR) 检查项
- [ ] 多笔交易使用同一客户ID
- [ ] 30天累计金额 >= 5,000,000 THB
- [ ] 触发 AMLO-1-03
- [ ] 弹出预约模态框
- [ ] 成功创建预约记录

### 审核功能检查项
- [ ] 查看详情按钮正常工作
- [ ] 详情信息显示完整
- [ ] 审核通过流程正常
- [ ] 审核拒绝流程正常
- [ ] 拒绝原因必填验证生效
- [ ] 列表状态实时更新
- [ ] Toast通知显示正常

---

## 常见问题 ❓

### Q1: 输入金额后没有弹出预约模态框？
**A:** 检查以下几点：
1. 确认金额是否达到触发阈值（>= 2,000,000 THB）
2. 检查浏览器Console是否有错误
3. 确认触发规则是否已配置（查看 trigger_rules 表）
4. 检查后端日志是否有触发检测记录

### Q2: 场景2无法触发ATR？
**A:**
1. 确认金额 >= 8,000,000 THB
2. 确认 exchange_type = 'asset_backed'（这是关键）
3. 使用开发者工具检查提交的表单数据
4. 如果UI不支持，使用开发者工具修改

### Q3: 场景3累计金额如何计算？
**A:**
1. 系统会自动计算过去30天同一客户的交易总额
2. 可以通过查询 exchange_transactions 表验证
3. 也可以直接调用 `/api/amlo/check-trigger` API测试

### Q4: 审核后状态没有更新？
**A:**
1. 刷新浏览器页面
2. 检查Network标签确认API调用成功
3. 检查后端日志确认审核操作已执行

---

## 数据库验证 🔍

### 查询预约记录
```sql
SELECT
    id,
    reservation_no,
    customer_name,
    local_amount,
    report_type,
    status,
    created_at
FROM Reserved_Transaction
ORDER BY created_at DESC;
```

### 查询触发规则
```sql
SELECT
    id,
    rule_name,
    report_type,
    rule_expression,
    is_active
FROM trigger_rules
WHERE is_active = TRUE;
```

### 查询30天累计金额
```sql
SELECT
    customer_id,
    SUM(local_amount) as total_amount,
    COUNT(*) as transaction_count
FROM exchange_transactions
WHERE transaction_date >= DATE_SUB(CURDATE(), INTERVAL 30 DAY)
GROUP BY customer_id
HAVING total_amount >= 5000000;
```

---

## 测试完成后 ✅

测试完成后，你可以：
1. 导出测试结果截图
2. 记录发现的问题
3. 如需重新测试，再次运行清理脚本：
   ```bash
   python clear_amlo_test_data_auto.py
   ```

---

**祝测试顺利！** 🎉

如有任何问题，请及时反馈。
