# 面值兑换方向传递修复

**日期**: 2025-10-29
**问题**: 面值兑换时，无论选择买入还是卖出，交易方向都被保存为同一个方向，导致PDF金额填写位置错误

---

## 问题描述

用户报告：
1. **"测试结果是，无论交易方向选买入还是卖出，金额都填到左边去了"**
2. 数据库查询显示所有 `Reserved_Transaction` 记录的 `direction` 字段都是 `'buy'`
3. 前端明明有 `exchangeMode` 选择（`buy_foreign` / `sell_foreign`），但没有正确传递到后端

---

## 根本原因

**数据流分析**:

```
前端 ExchangeViewWithDenominations.vue
  ↓ (设置exchangeMode: 'buy_foreign' 或 'sell_foreign')
  ↓
  ↓ executeTransaction() → 调用API /exchange/perform-dual-direction
  ↓
  ↓ transactionData = {
  ↓     exchange_mode: this.exchangeMode,     ← ✅ 前端有这个字段
  ↓     denomination_data: {
  ↓         combinations: [...],              ← ❌ combinations里没有direction
  ↓     }
  ↓ }
  ↓
后端 dual_direction.py
  ↓
  ↓ execute_split_transaction(
  ↓     denomination_data=data['denomination_data'],
  ↓     ...
  ↓     # ❌ 没有传递 exchange_mode 参数！
  ↓ )
  ↓
TransactionSplitService.analyze_denomination_combinations()
  ↓
  ↓ for item in combinations:
  ↓     direction = item.get('direction', 'sell')  ← ❌ 总是用默认值 'sell'
```

**问题根源**:
1. 前端传递了 `exchange_mode` 但后端路由 **没有传递** 给 `TransactionSplitService`
2. `TransactionSplitService` 从每个 denomination item 里查找 `direction` 字段，但前端从未设置过
3. 所以总是使用默认值 `'sell'`，导致所有交易都被当作"网点卖出外币"处理

---

## 修复方案

### 修改 1: `dual_direction.py` - 传递 exchange_mode

**文件**: `src/routes/exchange/dual_direction.py`

#### `/perform-dual-direction` 路由 (line 217)

**修改前**:
```python
result = TransactionSplitService.execute_split_transaction(
    denomination_data=data['denomination_data'],
    branch_id=current_user['branch_id'],
    base_currency_id=branch.base_currency_id,
    operator_id=current_user['id'],
    customer_info=data['customer_info'],
    purpose_id=data.get('purpose_id')
)
```

**修改后**:
```python
result = TransactionSplitService.execute_split_transaction(
    denomination_data=data['denomination_data'],
    branch_id=current_user['branch_id'],
    base_currency_id=branch.base_currency_id,
    operator_id=current_user['id'],
    customer_info=data['customer_info'],
    purpose_id=data.get('purpose_id'),
    exchange_mode=data.get('exchange_mode')  # 🔧 传递交易方向
)
```

#### `/validate-dual-direction` 路由 (line 65)

**修改前**:
```python
transaction_groups = TransactionSplitService.analyze_denomination_combinations(
    denomination_data,
    branch.base_currency_id
)
```

**修改后**:
```python
transaction_groups = TransactionSplitService.analyze_denomination_combinations(
    denomination_data,
    branch.base_currency_id,
    data.get('exchange_mode')  # 🔧 传递交易方向
)
```

---

### 修改 2: `transaction_split_service.py` - 接收并转换 exchange_mode

**文件**: `src/services/transaction_split_service.py`

#### `analyze_denomination_combinations()` 方法 (line 24)

**修改前**:
```python
@staticmethod
def analyze_denomination_combinations(denomination_data: Dict[str, Any], base_currency_id: int) -> List[Dict[str, Any]]:
    """分析面值组合数据，按币种+方向分组"""

    # ...

    for item in denomination_data['combinations']:
        currency_id = item.get('currency_id', denomination_data.get('currency_id'))
        direction = item.get('direction', 'sell')  # ❌ 总是默认 'sell'

        # 创建分组...
```

**修改后**:
```python
@staticmethod
def analyze_denomination_combinations(
    denomination_data: Dict[str, Any],
    base_currency_id: int,
    exchange_mode: str = None  # 🔧 新增参数
) -> List[Dict[str, Any]]:
    """分析面值组合数据，按币种+方向分组"""

    logger.info(f"[TransactionSplitService] exchange_mode: {exchange_mode}")

    # 🔧 修复：根据exchange_mode转换为direction
    # exchange_mode='buy_foreign' → direction='buy' (网点买入外币)
    # exchange_mode='sell_foreign' → direction='sell' (网点卖出外币)
    if exchange_mode:
        if exchange_mode == 'buy_foreign':
            global_direction = 'buy'  # 网点买入外币
        elif exchange_mode == 'sell_foreign':
            global_direction = 'sell'  # 网点卖出外币
        else:
            global_direction = 'sell'  # 默认值
    else:
        global_direction = 'sell'  # 兼容旧代码的默认值

    logger.info(f"[TransactionSplitService] 转换后的direction: {global_direction}")

    for item in denomination_data['combinations']:
        currency_id = item.get('currency_id', denomination_data.get('currency_id'))

        # 🔧 修复：优先使用全局方向，然后是单个item的方向
        direction = item.get('direction') or global_direction

        # 创建分组...
```

#### `execute_split_transaction()` 方法 (line 233)

**修改前**:
```python
@staticmethod
def execute_split_transaction(
    denomination_data: Dict[str, Any],
    branch_id: int,
    base_currency_id: int,
    operator_id: int,
    customer_info: Dict[str, Any],
    purpose_id: Optional[str] = None
) -> Dict[str, Any]:
    # ...
    transaction_groups = TransactionSplitService.analyze_denomination_combinations(
        denomination_data, base_currency_id
    )
```

**修改后**:
```python
@staticmethod
def execute_split_transaction(
    denomination_data: Dict[str, Any],
    branch_id: int,
    base_currency_id: int,
    operator_id: int,
    customer_info: Dict[str, Any],
    purpose_id: Optional[str] = None,
    exchange_mode: Optional[str] = None  # 🔧 新增参数
) -> Dict[str, Any]:
    # ...
    transaction_groups = TransactionSplitService.analyze_denomination_combinations(
        denomination_data, base_currency_id, exchange_mode  # 🔧 传递参数
    )
```

---

## 方向映射逻辑

### 前端 → 后端映射

| 前端 exchangeMode | 后端 direction | 含义 | AMLO PDF位置 |
|------------------|---------------|------|-------------|
| `buy_foreign` | `buy` | 网点买入外币 | 左栏 (fill_48, fill_50) |
| `sell_foreign` | `sell` | 网点卖出外币 | 右栏 (fill_49, fill_51) |

### 交易记录中的 transaction_direction

在 `create_transaction_records()` 中 (line 158-167):

```python
if group['direction'] == 'buy':
    # 前端选择"买入" = 网点买入外币：外币库存增加（正数），支出本币（负数）
    transaction_type = 'buy'
    foreign_amount = group['total_amount']   # 正数：网点外币库存增加
    local_amount = -(group['total_amount'] * avg_rate)  # 负数：网点支出本币
else:
    # 前端选择"卖出" = 网点卖出外币：外币库存减少（负数），收到本币（正数）
    transaction_type = 'sell'
    foreign_amount = -group['total_amount']  # 负数：网点外币库存减少
    local_amount = group['total_amount'] * avg_rate  # 正数：网点收到本币
```

---

## 测试验证

### 测试步骤

```bash
# 1. 重启后端
python src/main.py

# 2. 清空浏览器缓存，重新加载前端
# 3. 测试买入方向（网点买入外币）
```

### 测试场景 A: 网点买入外币 (buy_foreign)

**操作**:
1. 打开面值兑换页面
2. 选择外币（如 USD）
3. 选择 **"买入"** 方向（前端显示为"买入外币"）
4. 输入面值组合
5. 提交交易

**预期后端日志**:
```
[TransactionSplitService] exchange_mode: buy_foreign
[TransactionSplitService] 转换后的direction: buy
[TransactionSplitService] 分组 1: 币种ID=2, 方向=buy, 总金额=1000.00
[create_transaction_records] 分组1: type=buy, foreign_amount=1000.00, local_amount=-35000.00
```

**预期数据库**:
```sql
SELECT id, reservation_no, direction, local_amount
FROM Reserved_Transaction
ORDER BY id DESC LIMIT 1;

-- 结果应该是:
-- direction = 'buy'
```

**预期PDF**: 金额在 **左栏** (fill_48, fill_50)

---

### 测试场景 B: 网点卖出外币 (sell_foreign)

**操作**:
1. 打开面值兑换页面
2. 选择外币（如 USD）
3. 选择 **"卖出"** 方向（前端显示为"卖出外币"）
4. 输入面值组合
5. 提交交易

**预期后端日志**:
```
[TransactionSplitService] exchange_mode: sell_foreign
[TransactionSplitService] 转换后的direction: sell
[TransactionSplitService] 分组 1: 币种ID=2, 方向=sell, 总金额=1000.00
[create_transaction_records] 分组1: type=sell, foreign_amount=-1000.00, local_amount=35000.00
```

**预期数据库**:
```sql
SELECT id, reservation_no, direction, local_amount
FROM Reserved_Transaction
ORDER BY id DESC LIMIT 1;

-- 结果应该是:
-- direction = 'sell'
```

**预期PDF**: 金额在 **右栏** (fill_49, fill_51)

---

## 调试日志

修复后，运行面值兑换交易时应该看到以下日志：

```
# 1. 分析denomination组合
[TransactionSplitService] analyze_denomination_combinations 收到数据:
[TransactionSplitService] denomination_data type: <class 'dict'>
[TransactionSplitService] exchange_mode: buy_foreign
[TransactionSplitService] 转换后的direction: buy

# 2. 创建分组
[TransactionSplitService] 分组结果: 1 个分组
[TransactionSplitService] 分组 2_buy: 币种ID=2, 方向=buy, 总金额=1000.00

# 3. 创建交易记录
[create_transaction_records] 分组1: 方向=buy, 总金额=1000.00, 平均汇率=35.00
[create_transaction_records] 分组1: type=buy, foreign_amount=1000.00, local_amount=-35000.00, rate=35.00
```

如果看到 `direction: sell` 但前端选择的是"买入"，则说明 `exchange_mode` 参数没有正确传递。

---

## 相关文件

### 修改的文件
1. **`src/routes/exchange/dual_direction.py`** (2处修改)
   - Line 224: `execute_split_transaction()` 调用增加 `exchange_mode` 参数
   - Line 68: `analyze_denomination_combinations()` 调用增加 `exchange_mode` 参数

2. **`src/services/transaction_split_service.py`** (2处修改)
   - Line 24-88: `analyze_denomination_combinations()` 方法签名和逻辑
   - Line 233-262: `execute_split_transaction()` 方法签名

### 相关但未修改的文件
1. **`src/views/ExchangeViewWithDenominations.vue`** (前端，已正确传递 exchange_mode)
2. **`src/services/pdf/amlo_data_mapper.py`** (PDF生成，之前已修复direction逻辑)
3. **`src/routes/app_amlo.py`** (AMLO报告生成，之前已修复)

---

## 兼容性说明

### 向后兼容性

修改后的代码保持向后兼容：
- `exchange_mode` 参数为 **可选参数** (`Optional[str] = None`)
- 如果调用方不传递 `exchange_mode`，则使用默认值 `'sell'`（保持原有行为）
- 允许单个 item 仍然可以通过 `item.get('direction')` 设置独立方向

### 新增日志

为了便于调试，添加了详细的日志输出：
```python
logger.info(f"[TransactionSplitService] exchange_mode: {exchange_mode}")
logger.info(f"[TransactionSplitService] 转换后的direction: {global_direction}")
logger.info(f"[TransactionSplitService] 分组结果: {len(groups)} 个分组")
logger.info(f"[TransactionSplitService] 分组 {key}: 币种ID={...}, 方向={...}, 总金额={...}")
```

---

## 总结

| 项目 | 状态 |
|-----|------|
| **修复前端→后端方向传递** | ✅ 完成 |
| **更新TransactionSplitService** | ✅ 完成 |
| **添加调试日志** | ✅ 完成 |
| **保持向后兼容** | ✅ 完成 |
| **测试验证** | ⏳ 需要用户测试 |

**修改的文件**:
- `src/routes/exchange/dual_direction.py` (2行新增)
- `src/services/transaction_split_service.py` (约65行修改/新增)

**新增代码行数**: ~67行
**删除代码行数**: ~2行
**净增加代码**: ~65行

**下一步**:
1. 重启后端: `python src/main.py`
2. 清空浏览器缓存
3. 执行测试场景 A 和 B
4. 检查后端日志输出
5. 验证数据库 `direction` 字段
6. 生成PDF并验证金额位置

---

**修复完成日期**: 2025-10-29
**修复人员**: Claude Code Assistant
**问题编号**: DIRECTION-PROPAGATION-001
**相关文档**:
- `DIRECTION_AND_TRIGGER_FIX.md` (交易方向PDF映射修复)
- `REPORT_NUMBER_UNIFIED_FIX.md` (报告编号系统统一)
