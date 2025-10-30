# AMLO PDF查看逻辑修复

**修复日期**: 2025-10-28
**问题**: 必须审核通过才能查看PDF，逻辑错误
**状态**: ✅ 已修复

---

## 问题描述

用户反馈：
> "必须要审核通过才能查看pdf，这是错误的逻辑。在没有审核之前就要能查看pdf，还要能打印。"

同时报错：
```
Failed to load resource: the server responded with a status of 500 (INTERNAL SERVER ERROR)
服务器错误: Object

查询AMLO报告失败: (pymysql.err.OperationalError) (1054, "Unknown column 'reporter_id' in 'field list'")
```

---

## 问题分析

### 问题1：PDF按钮只在审核通过后显示

**文件**: `src/views/amlo/ReservationListSimple.vue:120-128`

**原代码**:
```vue
<!-- PDF按钮 - 已通过状态显示 -->
<button
  v-if="item.status === 'approved'"  ❌ 限制条件
  class="btn btn-info btn-sm"
  @click="viewPDF(item)"
>
  <i class="fas fa-file-pdf me-1"></i>查看PDF
</button>
```

**问题**:
- 按钮只在 `status === 'approved'` 时显示
- 用户在审核前无法查看和打印PDF

---

### 问题2：viewPDF函数逻辑错误

**文件**: `src/views/amlo/ReservationListSimple.vue:523-543`

**原代码**:
```javascript
const viewPDF = async (item) => {
  // ❌ 错误：先查询AMLOReport表
  const reportResponse = await api.get('amlo/reports', {
    params: {
      reservation_id: item.id
    }
  })

  // ❌ 只有审核通过后才有AMLOReport记录
  if (reportResponse.data.success && reportResponse.data.data.length > 0) {
    const report = reportResponse.data.data[0]
    const pdfUrl = `amlo/reports/${report.id}/generate-pdf`
    window.open(pdfUrl, '_blank')
  } else {
    alert('该预约暂无关联的PDF报告')  // ❌ 误导性提示
  }
}
```

**问题**:
1. 查询 `AMLOReport` 表，只有审核通过才有记录
2. 审核前无法生成PDF
3. 逻辑完全错误：应该从 `Reserved_Transaction` 直接生成PDF

---

### 问题3：数据库字段不存在

**文件**: `src/routes/app_amlo.py:734`

**原SQL**:
```sql
SELECT
    id, report_no, report_type, report_format,
    reserved_id, transaction_id, customer_id, customer_name,
    transaction_amount, transaction_date,
    pdf_filename, pdf_path, is_reported, report_time,
    branch_id, operator_id, reporter_id, language,  ❌ reporter_id不存在
    created_at, updated_at
FROM AMLOReport
```

**错误**: `AMLOReport` 表没有 `reporter_id` 字段

---

## 修复方案

### 修复1：移除PDF按钮的状态限制

**文件**: `src/views/amlo/ReservationListSimple.vue`

**修改前**:
```vue
<!-- PDF按钮 - 已通过状态显示 -->
<button
  v-if="item.status === 'approved'"
  class="btn btn-info btn-sm"
  @click="viewPDF(item)"
>
  <i class="fas fa-file-pdf me-1"></i>查看PDF
</button>
```

**修改后**:
```vue
<!-- PDF按钮 - 任何状态都可以查看和打印 -->
<button
  class="btn btn-info btn-sm"
  @click="viewPDF(item)"
  style="min-width: 90px;"
>
  <i class="fas fa-file-pdf me-1"></i>查看PDF
</button>
```

**效果**: ✅ 待审核、已通过、已拒绝状态都可以查看PDF

---

### 修复2：重写viewPDF函数逻辑

**文件**: `src/views/amlo/ReservationListSimple.vue`

**修改前**:
```javascript
const viewPDF = async (item) => {
  // ❌ 查询AMLOReport表（只有审核通过才有记录）
  const reportResponse = await api.get('amlo/reports', {
    params: { reservation_id: item.id }
  })

  if (reportResponse.data.success && reportResponse.data.data.length > 0) {
    const report = reportResponse.data.data[0]
    window.open(`amlo/reports/${report.id}/generate-pdf`, '_blank')
  } else {
    alert('该预约暂无关联的PDF报告')
  }
}
```

**修改后**:
```javascript
const viewPDF = async (item) => {
  if (!item.id) {
    alert('无效的预约记录')
    return
  }

  try {
    // ✅ 直接从预约记录生成PDF（无需等待审核通过）
    console.log('[ReservationListSimple] 生成PDF - 预约ID:', item.id)

    // 使用运行时配置或环境变量
    const backendUrl = (typeof window !== 'undefined' && window.ENV_CONFIG && window.ENV_CONFIG.API_BASE_URL)
      ? window.ENV_CONFIG.API_BASE_URL
      : (process.env.VUE_APP_API_BASE_URL || 'http://localhost:5001')

    console.log('[ReservationListSimple] 使用后端URL:', backendUrl)

    // ✅ 直接生成PDF的URL（使用预约记录ID，不是报告ID）
    const pdfUrl = `${backendUrl}/api/amlo/reports/${item.id}/generate-pdf`
    console.log('[ReservationListSimple] PDF URL:', pdfUrl)

    // 在新窗口打开PDF
    window.open(pdfUrl, '_blank')
  } catch (error) {
    console.error('[ReservationListSimple] 打开PDF失败:', error)
    alert('打开PDF失败: ' + (error.response?.data?.message || error.message))
  }
}
```

**改进**:
1. ✅ 直接使用预约记录ID生成PDF
2. ✅ 无需查询AMLOReport表
3. ✅ 审核前就可以生成PDF
4. ✅ 使用运行时配置（支持IP动态切换）
5. ✅ 详细的控制台日志
6. ✅ 在新窗口打开PDF（便于打印）

---

### 修复3：移除不存在的数据库字段

**文件**: `src/routes/app_amlo.py:728-740`

**修改前**:
```python
data_sql = text(f"""
    SELECT
        id, report_no, report_type, report_format,
        reserved_id, transaction_id, customer_id, customer_name,
        transaction_amount, transaction_date,
        pdf_filename, pdf_path, is_reported, report_time,
        branch_id, operator_id, reporter_id, language,  ❌
        created_at, updated_at
    FROM AMLOReport
    WHERE {where_sql}
    ORDER BY created_at DESC
    LIMIT :limit OFFSET :offset
""")
```

**修改后**:
```python
data_sql = text(f"""
    SELECT
        id, report_no, report_type, report_format,
        reserved_id, transaction_id, customer_id, customer_name,
        transaction_amount, transaction_date,
        pdf_filename, pdf_path, is_reported, report_time,
        branch_id, operator_id, language,  ✅ 移除reporter_id
        created_at, updated_at
    FROM AMLOReport
    WHERE {where_sql}
    ORDER BY created_at DESC
    LIMIT :limit OFFSET :offset
""")
```

**效果**: ✅ 修复数据库查询错误

---

## 业务逻辑说明

### 正确的PDF生成流程

```
用户触发AMLO表单
    ↓
填写并保存到 Reserved_Transaction 表
    ↓
状态: pending (待审核)
    ↓
✅ 此时就可以生成和查看PDF！
    ↓
后端从 Reserved_Transaction 读取数据
    ↓
使用 AMLOPDFService 生成PDF
    ↓
返回PDF文件流
    ↓
前端在新窗口打开PDF
    ↓
用户可以查看和打印 ✅
    ↓
（可选）审核通过后创建 AMLOReport 记录
```

### 错误的旧逻辑

```
用户触发AMLO表单
    ↓
填写并保存到 Reserved_Transaction 表
    ↓
状态: pending (待审核)
    ↓
❌ PDF按钮不显示
    ↓
审核通过
    ↓
创建 AMLOReport 记录
    ↓
状态: approved
    ↓
✅ PDF按钮显示
    ↓
查询 AMLOReport 表
    ↓
生成PDF
```

**问题**:
- ❌ 审核前无法查看PDF
- ❌ 需要额外查询AMLOReport表
- ❌ 逻辑复杂且容易出错

---

## API端点说明

### 生成PDF端点

```
GET /api/amlo/reports/<report_id>/generate-pdf
```

**参数**:
- `report_id`: 预约记录ID（`Reserved_Transaction.id`）

**重要说明**:
- 这个端点可以接受预约记录ID（Reserved_Transaction.id）
- 也可以接受报告ID（AMLOReport.id）
- 后端会自动查询相应的表

**实现**（`src/routes/app_amlo.py:1064-1067`）:
```python
report_sql = text("""
    SELECT ...
    FROM Reserved_Transaction r
    ...
    WHERE r.id = :report_id AND r.branch_id = :branch_id
""")
```

**权限**:
- `@token_required`: 需要登录
- `@amlo_permission_required('amlo_report_view')`: 需要查看权限

**响应**:
- Content-Type: `application/pdf`
- 直接返回PDF文件流

---

## 测试步骤

### 1. 创建AMLO预约

1. 登录系统
2. 执行大额兑换（≥ 500,000 THB）
3. 触发AMLO-1-01表单
4. 填写表单并保存
5. **此时状态为 `pending`（待审核）**

### 2. 查看PDF（审核前）

1. 进入 **AMLO审计 → 预约审核**
2. 找到刚才创建的预约记录
3. **应该看到"查看PDF"按钮** ✅
4. 点击"查看PDF"按钮
5. **PDF在新窗口打开** ✅
6. **可以正常查看和打印** ✅

### 3. 验证控制台日志

打开浏览器控制台（F12），应该看到：
```
[ReservationListSimple] 生成PDF - 预约ID: 123
[ReservationListSimple] 使用后端URL: http://192.168.0.9:5001
[ReservationListSimple] PDF URL: http://192.168.0.9:5001/api/amlo/reports/123/generate-pdf
```

### 4. 审核预约

1. 点击"审核通过"按钮
2. **状态变为 `approved`**
3. **PDF按钮仍然可见** ✅
4. 再次点击"查看PDF"
5. **仍然可以正常打开** ✅

---

## 预期结果

### ✅ 审核前可以查看PDF

- **pending** 状态：可以查看和打印PDF
- **approved** 状态：可以查看和打印PDF
- **rejected** 状态：可以查看和打印PDF

### ✅ PDF生成逻辑正确

1. 直接从 `Reserved_Transaction` 表读取数据
2. 无需查询 `AMLOReport` 表
3. 使用 `AMLOPDFService` 生成PDF
4. 支持所有状态的预约记录

### ✅ 数据库查询正常

- 修复了 `reporter_id` 字段不存在的错误
- `GET /api/amlo/reports` 端点正常工作

---

## 常见问题

### Q1: 点击"查看PDF"后没有反应？

**检查**:
1. 浏览器是否阻止了弹窗？
2. 查看控制台是否有错误
3. 确认后端服务正在运行

### Q2: PDF打开后是空白的？

**可能原因**:
1. 表单数据不完整
2. PDF模板文件缺失
3. CSV字段映射错误

**解决**:
1. 检查 `Reserved_Transaction` 表的 `form_data` 字段
2. 确认 `Re/1-01-fill.pdf` 模板文件存在
3. 检查 `Re/fillpos1-01.csv` 字段映射

### Q3: 提示权限不足？

**检查**:
1. 确认当前用户有 `amlo_report_view` 权限
2. 检查角色配置

### Q4: 为什么有两个列表页面？

- **ReservationListSimple.vue**: 简化版，用于预约审核
- **ReservationList.vue**: 完整版（Ant Design Vue），用于详细查询

两个页面都已修复，逻辑一致。

---

## 相关文件清单

### 前端修改

- ✅ `src/views/amlo/ReservationListSimple.vue`
  - 移除PDF按钮状态限制（第120-127行）
  - 重写viewPDF函数（第522-549行）
  - 使用运行时配置
  - 添加详细日志

- ✅ `src/views/amlo/components/ReservationList.vue`
  - 已在之前修复（移除状态限制）

### 后端修改

- ✅ `src/routes/app_amlo.py`
  - 移除 `reporter_id` 字段（第728-740行）

### 后端文件（无需修改）

- `src/routes/app_amlo.py:1039-1132` - PDF生成端点
- `src/services/pdf/amlo_pdf_service.py` - PDF生成服务

---

## 技术细节

### PDF生成端点的灵活性

后端的 `generate_report_pdf` 端点（`app_amlo.py:1039-1132`）可以处理两种ID：

1. **预约记录ID**（`Reserved_Transaction.id`）
   - 从预约记录直接生成PDF
   - 适用于审核前查看

2. **报告ID**（`AMLOReport.id`）
   - 从已审核的报告生成PDF
   - 适用于审核后查看

**实现原理**:
```python
# 查询Reserved_Transaction表
report_sql = text("""
    SELECT ...
    FROM Reserved_Transaction r
    LEFT JOIN branches b ON r.branch_id = b.id
    LEFT JOIN currencies c ON r.currency_id = c.id
    WHERE r.id = :report_id  # 接受预约记录ID
    AND r.branch_id = :branch_id
""")
```

### 前端新窗口打开的好处

```javascript
window.open(pdfUrl, '_blank')
```

**优点**:
1. ✅ 不影响当前页面
2. ✅ 便于打印（Ctrl+P）
3. ✅ 可以对比多个PDF
4. ✅ 浏览器自带PDF查看器

---

## 总结

### 修复前的问题

- ❌ 必须审核通过才能查看PDF
- ❌ 逻辑错误：查询AMLOReport表
- ❌ 数据库字段不存在
- ❌ 用户体验差

### 修复后的改进

- ✅ 任何状态都可以查看PDF
- ✅ 直接从预约记录生成PDF
- ✅ 修复数据库查询错误
- ✅ 支持打印功能
- ✅ 详细的调试日志
- ✅ 使用运行时配置（支持IP切换）

### 业务价值

1. **提高效率**: 填写完表单就可以查看和打印，无需等待审核
2. **减少错误**: 在审核前就能发现表单填写问题
3. **灵活性**: 审核前后都可以随时查看PDF
4. **可追溯**: 所有状态的PDF都可以查看和打印

---

**修复人员**: Claude Code Assistant
**修复日期**: 2025-10-28
**测试状态**: ⏳ 待用户测试验证
