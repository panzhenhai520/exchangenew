# AMLO PDF下载功能修复报告

**修复日期**: 2025-10-28
**问题**: AMLO预约查询页面看不到PDF下载按钮
**状态**: ✅ 已修复

---

## 问题描述

用户反馈：
> "我测试，面值兑换，触发了AMLO表单，填写就保存，到AMLO审计的预约查询页面，没有看到pdf在哪里查看。"

---

## 问题分析

### 发现的问题

1. **字段名称不匹配**:
   - 后端API返回的是 `id` 字段
   - 前端表格配置使用的是 `reservation_id`
   - 导致行key错误，数据无法正确绑定

2. **API URL配置错误**:
   - 前端使用了 `import.meta.env.VITE_API_BASE_URL`
   - 应该使用 `window.ENV_CONFIG.API_BASE_URL`（运行时配置）
   - 导致IP更换后无法正确访问

3. **按钮显示条件过于严格**:
   - 原代码只在 `status === 'approved' || status === 'completed'` 时显示
   - 用户可能还在 `pending` 状态就想查看PDF
   - 限制了可用性

4. **缺少翻译**:
   - `common.downloadPdf`, `common.view` 等翻译缺失
   - 影响多语言显示

5. **错误信息不详细**:
   - 只显示 "PDF生成失败"
   - 无法诊断具体问题

---

## 修复方案

### 1. 修复字段名称不匹配

**文件**: `src/views/amlo/components/ReservationList.vue`

**修改前**:
```vue
<a-table
  :columns="columns"
  :data-source="reservations"
  row-key="reservation_id"
>
```

```javascript
const columns = [
  {
    title: t('amlo.reservation.id'),
    dataIndex: 'reservation_id',
    key: 'reservation_id',
    width: 100
  },
  ...
]
```

**修改后**:
```vue
<a-table
  :columns="columns"
  :data-source="reservations"
  row-key="id"
>
```

```javascript
const columns = [
  {
    title: t('amlo.reservation.id'),
    dataIndex: 'id',
    key: 'id',
    width: 100
  },
  ...
]
```

**原因**: 后端 `app_amlo.py:339` 返回的字段是 `id`，不是 `reservation_id`

---

### 2. 修复API URL配置

**文件**: `src/views/amlo/components/ReservationList.vue`

**修改前**:
```javascript
const backendUrl = import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001'
const url = `${backendUrl}/api/amlo/reports/${record.id}/generate-pdf`
```

**修改后**:
```javascript
// 使用运行时配置（优先）或环境变量（回退）
const backendUrl = (typeof window !== 'undefined' && window.ENV_CONFIG && window.ENV_CONFIG.API_BASE_URL)
  ? window.ENV_CONFIG.API_BASE_URL
  : (import.meta.env.VITE_API_BASE_URL || 'http://localhost:5001')

console.log('[ReservationList] 下载PDF - 使用后端URL:', backendUrl)
const url = `${backendUrl}/api/amlo/reports/${record.id}/generate-pdf`
console.log('[ReservationList] 请求URL:', url)
```

**优势**:
- ✅ 使用运行时配置，无需重新编译
- ✅ 支持IP动态切换
- ✅ 添加调试日志

---

### 3. 放宽PDF下载按钮显示条件

**文件**: `src/views/amlo/components/ReservationList.vue`

**修改前**:
```vue
<a-button
  v-if="record.status === 'approved' || record.status === 'completed'"
  type="link"
  size="small"
  @click="handleDownloadPdf(record)"
  :loading="downloadingPdf[record.id]"
>
  <DownloadOutlined /> {{ $t('common.downloadPdf') }}
</a-button>
```

**修改后**:
```vue
<!-- PDF下载按钮 - 任何状态都显示，便于调试 -->
<a-button
  type="link"
  size="small"
  @click="handleDownloadPdf(record)"
  :loading="downloadingPdf[record.id]"
>
  <DownloadOutlined /> {{ $t('common.downloadPdf') }}
</a-button>
```

**说明**:
- 移除了状态限制
- 后端会检查权限和数据有效性
- 便于调试和测试

---

### 4. 增强错误处理和日志

**文件**: `src/views/amlo/components/ReservationList.vue`

**修改前**:
```javascript
if (!response.ok) {
  throw new Error('PDF生成失败')
}

const blob = await response.blob()
// ... 下载逻辑
message.success(t('common.downloadSuccess'))
```

**修改后**:
```javascript
if (!response.ok) {
  const errorText = await response.text()
  console.error('[ReservationList] PDF生成失败 - 状态码:', response.status)
  console.error('[ReservationList] 错误内容:', errorText)
  throw new Error(`PDF生成失败 (${response.status}): ${errorText}`)
}

// 检查响应类型
const contentType = response.headers.get('content-type')
console.log('[ReservationList] 响应Content-Type:', contentType)

// 下载PDF文件
const blob = await response.blob()
console.log('[ReservationList] PDF文件大小:', blob.size, 'bytes')

// ... 下载逻辑

console.log('[ReservationList] PDF下载成功')
message.success(t('common.downloadSuccess'))
```

**错误处理改进**:
```javascript
} catch (error) {
  console.error('[ReservationList] 下载PDF失败:', error)
  message.error(`下载失败: ${error.message}`)  // 显示详细错误
}
```

---

### 5. 添加翻译

**文件**:
- `src/locales/zh-CN/common.json`
- `src/locales/en-US/common.json`
- `src/locales/th-TH/common.json`

**添加的翻译键**:
```json
{
  "view": "查看 / View / ดู",
  "downloadPdf": "下载PDF / Download PDF / ดาวน์โหลด PDF",
  "downloadSuccess": "下载成功 / Download successful / ดาวน์โหลดสำเร็จ",
  "downloadFailed": "下载失败 / Download failed / ดาวน์โหลดล้มเหลว"
}
```

---

## 后端API说明

### 端点

```
GET /api/amlo/reports/<report_id>/generate-pdf
```

### 参数

- `report_id`: AMLO预约记录的ID（整数）

### 权限

- 需要登录 (`@token_required`)
- 需要权限 `amlo_report_view` (`@amlo_permission_required`)

### 响应

**成功**:
- Content-Type: `application/pdf`
- 返回PDF文件流，浏览器自动下载

**失败**:
```json
{
  "success": false,
  "message": "错误信息"
}
```

### 实现逻辑

**文件**: `src/routes/app_amlo.py:1039-1132`

1. 查询 `Reserved_Transaction` 表获取预约记录
2. 检查记录是否属于当前用户的分支
3. 构建预约数据对象
4. 调用 `AMLOPDFService.generate_pdf_from_reservation()` 生成PDF
5. 返回PDF文件流

---

## 测试步骤

### 1. 触发AMLO表单

1. 登录系统
2. 执行一笔大额兑换（≥ 500,000 THB）
3. 系统自动触发AMLO-1-01表单
4. 填写表单并保存

### 2. 查看预约列表

1. 进入 `AMLO审计 → 预约查询`
2. 应该看到刚才创建的预约记录
3. 在操作列应该能看到以下按钮：
   - **查看** (所有记录)
   - **审核** (pending状态)
   - **下载PDF** (所有记录) ✅ **新增**

### 3. 下载PDF

1. 点击 **下载PDF** 按钮
2. 按钮显示加载状态
3. 打开浏览器控制台（F12）查看日志：
   ```
   [ReservationList] 下载PDF - 使用后端URL: http://192.168.0.9:5001
   [ReservationList] 请求URL: http://192.168.0.9:5001/api/amlo/reports/1/generate-pdf
   [ReservationList] 响应Content-Type: application/pdf
   [ReservationList] PDF文件大小: 123456 bytes
   [ReservationList] PDF下载成功
   ```
4. 浏览器自动下载PDF文件，文件名格式：`AMLO-1-01_A001-2025-001.pdf`

### 4. 验证PDF内容

1. 打开下载的PDF文件
2. 检查字段是否正确填充：
   - 报告编号
   - 客户姓名和证件号
   - 交易金额
   - 交易日期
   - 机构代码
   - 等等

---

## 预期结果

### ✅ 功能正常

1. **PDF下载按钮可见**: 所有预约记录都显示"下载PDF"按钮
2. **API请求成功**: 使用正确的IP地址（从运行时配置读取）
3. **PDF生成成功**: 后端成功生成并返回PDF文件
4. **浏览器自动下载**: 文件名正确，内容完整
5. **多语言支持**: 按钮文字根据语言设置显示

### 📋 调试信息

浏览器控制台应显示详细日志：
```
[ReservationList] 下载PDF - 使用后端URL: http://192.168.0.9:5001
[ReservationList] 请求URL: http://192.168.0.9:5001/api/amlo/reports/1/generate-pdf
[ReservationList] 响应Content-Type: application/pdf
[ReservationList] PDF文件大小: 123456 bytes
[ReservationList] PDF下载成功
```

---

## 常见问题排查

### Q1: 点击"下载PDF"按钮没有反应？

**检查**:
1. 打开浏览器控制台（F12）查看错误信息
2. 检查是否有网络错误（Network标签）
3. 确认后端服务正在运行

**可能原因**:
- 后端未启动
- IP配置错误
- 权限不足

---

### Q2: 提示"PDF生成失败 (404)"？

**原因**: 记录不存在或不属于当前分支

**检查**:
1. 确认记录ID正确
2. 确认当前用户的branch_id与记录的branch_id一致
3. 查看后端日志

---

### Q3: 提示"PDF生成失败 (403)"？

**原因**: 权限不足

**检查**:
1. 确认当前用户有 `amlo_report_view` 权限
2. 检查角色配置

---

### Q4: 提示"PDF生成失败 (500)"？

**原因**: 后端生成PDF时出错

**检查**:
1. 查看后端控制台日志
2. 检查PDF模板文件是否存在
3. 检查CSV字段映射文件是否正确

**常见错误**:
```python
FileNotFoundError: Re/1-01-fill.pdf
```
**解决**: 确认PDF模板文件存在于 `Re/` 目录

---

### Q5: 下载的PDF文件打不开或损坏？

**可能原因**:
1. PDF生成过程中出错
2. 文件传输不完整

**检查**:
1. 查看文件大小是否正常（> 0 bytes）
2. 对比控制台显示的文件大小
3. 查看后端日志确认PDF是否成功生成

---

## 技术细节

### 前端下载流程

```javascript
handleDownloadPdf(record)
  ↓
获取后端URL (window.ENV_CONFIG.API_BASE_URL)
  ↓
构建请求URL: /api/amlo/reports/{id}/generate-pdf
  ↓
发送GET请求 (带Authorization header)
  ↓
接收响应 (检查状态码和Content-Type)
  ↓
创建Blob对象
  ↓
创建临时下载链接
  ↓
触发下载
  ↓
清理资源
```

### 后端生成流程

```python
generate_report_pdf(report_id)
  ↓
查询Reserved_Transaction记录
  ↓
检查权限和branch_id
  ↓
构建reservation_data对象
  ↓
调用AMLOPDFService.generate_pdf_from_reservation()
  ↓
  加载CSV字段映射
  ↓
  映射业务数据到PDF字段
  ↓
  使用PyPDF2填充PDF表单
  ↓
  保存到临时文件
  ↓
返回PDF文件流 (send_file)
```

---

## 相关文件清单

### 前端修改

- ✅ `src/views/amlo/components/ReservationList.vue` - 主要修改文件
  - 修复字段名称 (`id` vs `reservation_id`)
  - 修复API URL配置（使用运行时配置）
  - 移除PDF按钮显示条件限制
  - 增强错误处理和日志

### 翻译文件

- ✅ `src/locales/zh-CN/common.json` - 添加中文翻译
- ✅ `src/locales/en-US/common.json` - 添加英文翻译
- ✅ `src/locales/th-TH/common.json` - 添加泰文翻译

### 后端文件（无需修改）

- `src/routes/app_amlo.py:1039-1132` - PDF生成API端点
- `src/services/pdf/amlo_pdf_service.py` - PDF生成服务
- `src/services/pdf/amlo_csv_field_loader.py` - CSV字段加载器
- `src/services/pdf/amlo_pdf_filler_v2.py` - PyPDF2表单填充器
- `src/services/pdf/amlo_data_mapper.py` - 数据映射器

### CSV字段映射

- `Re/fillpos1-01.csv` - AMLO-1-01字段坐标
- `Re/fillpos1-02.csv` - AMLO-1-02字段坐标
- `Re/fillpos1-03.csv` - AMLO-1-03字段坐标

### PDF模板

- `Re/1-01-fill.pdf` - AMLO-1-01空白模板
- `Re/1-02-fill.pdf` - AMLO-1-02空白模板
- `Re/1-03-fill.pdf` - AMLO-1-03空白模板

---

## 总结

### ✅ 修复完成

1. ✅ 字段名称匹配问题
2. ✅ API URL运行时配置
3. ✅ PDF按钮始终可见
4. ✅ 详细错误日志
5. ✅ 多语言翻译

### 🎯 用户体验改进

**修复前**:
- ❌ 看不到PDF下载按钮
- ❌ 不知道为什么无法下载
- ❌ IP更换后无法访问

**修复后**:
- ✅ 所有记录都显示PDF下载按钮
- ✅ 详细的错误提示和日志
- ✅ 自动适配IP变化
- ✅ 多语言支持

---

**修复人员**: Claude Code Assistant
**修复日期**: 2025-10-28
**测试状态**: ⏳ 待用户测试验证
