# AMLO 1-01报告填写规则合规性更新

## 概述

根据AMLO现金交易和银行转账的详细填写规则，对 `src/services/pdf/amlo_data_mapper.py` 进行了修正，确保生成的PDF报告完全符合AMLO官方要求。

## 修改日期

2025-11-03

## 修改内容

### 1. 添加支付方式标注 (ธนบัตร/โอน)

**位置**: `amlo_data_mapper.py` 第339-349行 (买入方向), 第439-449行 (卖出方向)

**修改前**:
```python
pdf_fields['fill_42'] = f"{currency_code} {foreign_text}"
pdf_fields['fill_43'] = f"{currency_code} {foreign_text}"
```

**修改后**:
```python
# 现金交易标注(ธนบัตร)，转账标注(โอน)
payment_notation = '(ธนบัตร)' if is_cash_method else '(โอน)'
pdf_fields['fill_42'] = f"{currency_code} {foreign_text} {payment_notation}"
pdf_fields['fill_43'] = f"{currency_code} {foreign_text} {payment_notation}"
```

**效果**:
- 现金交易: `USD 160,000 (ธนบัตร)`
- 转账交易: `USD 160,000 (โอน)`

---

### 2. 确保账号行不填金额

**位置**: `amlo_data_mapper.py` 第282-286行 (买入方向), 第364-368行 (卖出方向)

**修改前**:
```python
# 买入方向
pdf_fields['fill_48'] = '' if is_cash_method else f"{local_amount:.2f}"

# 卖出方向
pdf_fields['fill_49'] = '' if is_cash_method else f"{local_amount:.2f}"
```

**修改后**:
```python
# 买入方向
pdf_fields['fill_48'] = ''  # 账号行不填金额
pdf_fields['fill_48_5'] = f"{local_amount:.2f}"  # 买入外币金额填在此行

# 卖出方向
pdf_fields['fill_49'] = ''  # 账号行不填金额
pdf_fields['fill_49_5'] = f"{local_amount:.2f}"  # 卖出外币金额填在此行
```

**说明**:
- 根据AMLO规则，账号字段行（fill_48, fill_49）不应填写金额
- 金额应填写在对应的具体项目行（fill_48_5买入外币行, fill_49_5卖出外币行）

---

## 测试验证

### 测试场景

创建了 `test_amlo_to_file.py` 测试脚本，覆盖以下4个场景：

1. **现金买入外币** (Cash Buy FX)
   - 验证 `fill_42` 包含 `(ธนบัตร)` 标注 ✅
   - 验证 `fill_48` 为空字符串 ✅
   - 验证 `fill_48_5` 填写金额 ✅
   - 验证 `comb_3`, `comb_5` 为空 ✅

2. **转账买入外币** (Transfer Buy FX)
   - 验证 `fill_42` 包含 `(โอน)` 标注 ✅
   - 验证 `comb_3` 填写机构账号 ✅
   - 验证 `comb_5` 填写客户账号 ✅

3. **现金卖出外币** (Cash Sell FX)
   - 验证 `fill_43` 包含 `(ธนบัตร)` 标注 ✅
   - 验证 `fill_49` 为空字符串 ✅
   - 验证 `fill_49_5` 填写金额 ✅
   - 验证 `comb_4`, `comb_6` 为空 ✅

4. **转账卖出外币** (Transfer Sell FX)
   - 验证 `fill_43` 包含 `(โอน)` 标注 ✅
   - 验证 `comb_4` 填写机构账号 ✅
   - 验证 `comb_6` 填写客户账号 ✅

### 测试结果

所有测试通过！详见 `test_amlo_results.txt`

---

## 业务规则参考

### 现金交易规则 (AMLO现金交易的方式填写规则.txt)

1. **买入外币**:
   - `fill_42` = "USD 160,000 (ธนบัตร)"
   - 左栏金额: `fill_48_5` = 泰铢金额
   - 账号行不填金额: `fill_48` = 空
   - 账号字段留空: `comb_3`, `comb_5` = 空

2. **卖出外币**:
   - `fill_43` = "USD 150,000 (ธนบัตร)"
   - 右栏金额: `fill_49_5` = 泰铢金额
   - 账号行不填金额: `fill_49` = 空
   - 账号字段留空: `comb_4`, `comb_6` = 空

### 转账交易规则 (AMLO报告银行转账的方式填写规则.txt)

1. **买入外币**:
   - `fill_42` = "USD 160,000 (โอน)"
   - `comb_3` = 机构USD账号 (从branch配置获取，默认88888888)
   - `comb_5` = 客户泰铢支付账号
   - `comb_4` = 机构泰铢账号
   - `comb_6` = 客户泰铢收款账号
   - **关键**: 账号行不填金额

2. **卖出外币**:
   - `fill_43` = "USD 150,000 (โอน)"
   - `comb_4` = 机构USD账号
   - `comb_6` = 客户USD收款账号
   - `comb_3` = 机构泰铢账号
   - `comb_5` = 客户泰铢支付账号

---

## 影响范围

### 修改的文件
- `src/services/pdf/amlo_data_mapper.py`

### 新增的测试文件
- `test_amlo_to_file.py` - 规则验证测试脚本
- `test_amlo_results.txt` - 测试结果输出
- `test_amlo_rules.py` - 详细测试脚本（控制台版）
- `test_amlo_simple.py` - 简化测试脚本

### 不受影响的组件
- ✅ `src/services/pdf/amlo_pdf_filler_overlay.py` - PDF填充器无需修改
- ✅ `src/services/pdf/amlo_pdf_service.py` - PDF服务无需修改
- ✅ 报告编号填写方法 (`_draw_report_number`) - 保持不变
- ✅ Comb字段填写方法 (`_draw_comb_field`) - 保持不变

---

## 向后兼容性

✅ 本次修改完全向后兼容，不影响现有功能：
- 支付方式字段 (`payment_method`) 已存在
- 新增的 `fill_48_5`, `fill_49_5` 字段在CSV映射中已定义
- 账号字段 (`comb_*`) 已在之前版本实现

---

## 后续建议

1. ✅ 在实际环境中生成AMLO报告进行人工检查
2. ✅ 与AMLO官方样本进行对比验证
3. 建议添加更多边界情况测试（如大额、特殊币种等）
4. 建议将测试集成到CI/CD流程中

---

## 相关文档

- `COMB_FIELDS_IMPLEMENTATION.md` - Comb字段实现文档
- `AMLO现金交易的方式填写规则.txt` - 现金交易规则
- `AMLO报告银行转账的方式填写规则.txt` - 转账交易规则
- `Re/1-01-field-map.csv` - 字段映射表

---

## 总结

✅ 所有修改均已完成并通过测试
✅ 代码符合AMLO官方填写规则
✅ 现金交易正确标注 "(ธนบัตร)"
✅ 转账交易正确标注 "(โอน)"
✅ 账号行不再填写金额
✅ 金额正确填写在具体项目行 (fill_48_5, fill_49_5)
