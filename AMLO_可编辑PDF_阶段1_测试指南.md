# AMLO 可编辑PDF - 阶段1测试指南

**实施时间**: 2025-11-08
**实施方案**: 方案1 - 浏览器原生PDF表单
**当前阶段**: 阶段1 - 后端返回可编辑PDF并测试基本可编辑性

---

## 已实现功能

### 后端 (src/routes/app_amlo.py)

1. **新端点**: `/api/amlo/reservations/<id>/editable-pdf`
   - 返回**可编辑的PDF**（保留AcroForm表单字段）
   - 使用用户标记的PDF模板 `Re/1-01-fill.pdf`
   - 自动填充已保存的reservation数据

2. **辅助函数**: `_fill_pdf_form_fields(doc, form_data)`
   - 使用PyMuPDF填充PDF表单字段
   - 支持文本框、复选框、下拉列表
   - 保持字段可编辑状态（不扁平化）

### 前端 (src/views/amlo/PDFViewerWindow.vue)

1. **智能PDF加载**:
   - 编辑模式：自动加载**可编辑PDF**
   - 预览模式：加载最终扁平化PDF

2. **模式切换**:
   - 点击"编辑模式"按钮：重新加载可编辑PDF
   - 点击"预览模式"按钮：重新加载最终PDF

---

## 测试步骤

### 准备工作

1. **启动后端**:
   ```bash
   python src/main.py
   ```

2. **启动前端**:
   ```bash
   npm run serve
   ```

### 测试流程

#### 步骤1：查看现有预约

1. 打开浏览器：`http://localhost:8080`
2. 登录系统
3. 导航到：**AMLO → 预约列表**
4. 选择任意一个状态为"pending"或"approved"的预约
5. 点击"查看PDF"按钮

#### 步骤2：进入编辑模式

1. 在PDF查看器窗口中，点击右上角的**"编辑模式"**按钮
2. 观察以下变化：
   - ✅ PDF会重新加载（显示loading动画）
   - ✅ 右侧出现编辑面板，显示所有字段
   - ✅ 按钮文字变为"预览模式"

#### 步骤3：测试PDF字段可编辑性

**🔍 关键测试**：直接在PDF上点击字段，看是否可以编辑

1. 在左侧PDF预览区域，**尝试点击**以下类型的字段：
   - 文本框（如客户姓名、地址）
   - 复选框（如交易类型选择）
   - 数字框（如金额输入框）

2. **预期行为**（取决于浏览器）:
   - ✅ **Firefox**: 应该可以直接在PDF上点击并编辑字段
   - ⚠️ **Chrome**: 可能不支持AcroForm编辑（需要PDF.js支持）
   - 📝 **如果无法编辑**: 这是正常的，需要在阶段2实施PDF.js增强

3. **检查控制台日志**:
   ```
   打开浏览器开发者工具 (F12)
   查看Console标签，应该看到：
   [PDFViewerWindow] Loading EDITABLE PDF from: /api/amlo/reservations/xxx/editable-pdf?refresh=...
   [PDFViewerWindow] PDF loaded successfully, size: XXXXX
   ```

#### 步骤4：验证后端返回的PDF

1. **直接访问端点**（在新标签页）:
   ```
   http://localhost:5001/api/amlo/reservations/{reservation_id}/editable-pdf
   ```
   替换 `{reservation_id}` 为实际的预约ID

2. **使用PDF工具验证**:
   - 下载返回的PDF
   - 用Adobe Acrobat Reader打开
   - **检查表单字段**：应该可以在Acrobat中直接编辑
   - **检查字段值**：应该已填充reservation的数据

#### 步骤5：退出编辑模式

1. 点击"预览模式"按钮
2. 观察PDF重新加载为最终版本（扁平化、不可编辑）

---

## 预期结果

### ✅ 成功标志

1. **后端日志显示**:
   ```
   [get_editable_pdf] Getting editable PDF for reservation XXX
   [get_editable_pdf] Opening template: D:\code\exchangenew\Re\1-01-fill.pdf
   [get_editable_pdf] Filled X form fields
   [get_editable_pdf] Returning editable PDF (XXXXX bytes)
   ```

2. **前端行为**:
   - 编辑模式加载可编辑PDF（URL包含`/editable-pdf`）
   - 预览模式加载最终PDF（URL包含`/generate-pdf`）
   - 右侧编辑面板正常显示所有字段

3. **PDF内容**:
   - 表单字段已填充数据
   - 字段在Adobe Acrobat中可编辑
   - 字段在Firefox中可编辑（Chrome可能不支持）

### ⚠️ 已知限制（待阶段2解决）

1. **Chrome浏览器**:
   - Chrome可能不支持原生AcroForm编辑
   - 需要使用PDF.js作为后备方案（阶段2实施）

2. **双向同步**:
   - PDF字段修改不会自动同步到右侧面板
   - 右侧面板修改不会自动同步到PDF
   - 这是预期的，将在阶段2实现

3. **签名集成**:
   - 签名功能尚未与可编辑PDF集成
   - 将在阶段3实现

---

## 调试技巧

### 如果PDF无法加载

1. **检查PDF模板文件**:
   ```bash
   # 确认模板存在
   ls Re/1-01-fill.pdf
   ```

2. **检查后端日志**:
   ```bash
   # 查看错误信息
   tail -f *.log
   ```

3. **检查数据库**:
   ```sql
   SELECT id, reservation_no, report_type, form_data
   FROM Reserved_Transaction
   WHERE id = {reservation_id};
   ```

### 如果PDF字段未填充

1. **检查form_data字段**:
   - 确认数据库中`form_data`字段有值
   - 检查字段名是否匹配PDF中的field name

2. **检查字段映射**:
   - 在`_fill_pdf_form_fields()`函数中添加日志
   - 查看哪些字段被填充，哪些被跳过

### 浏览器兼容性测试

1. **测试不同浏览器**:
   - ✅ Firefox (推荐) - 最佳AcroForm支持
   - ⚠️ Chrome - 有限支持
   - ⚠️ Edge - 类似Chrome
   - ⚠️ Safari - 不确定

2. **PDF.js后备方案**（阶段2）:
   - 如果浏览器不支持，将使用PDF.js渲染
   - 提供一致的编辑体验

---

## 下一步：阶段2 实施计划

**目标**: 实现PDF与右侧面板的双向同步

### 需要实现的功能

1. **PDF字段变化 → 右侧面板同步**:
   - 监听PDF中的表单字段change事件
   - 更新右侧面板的v-model绑定
   - 标记字段为已修改

2. **右侧面板变化 → PDF字段同步**:
   - 监听右侧面板输入框的input事件
   - 使用JavaScript更新PDF表单字段值
   - 保持双向同步

3. **修改追踪**:
   - 高亮已修改的字段
   - 显示修改计数
   - 提供重置功能

---

## 技术细节

### 后端实现要点

```python
# 关键代码：_fill_pdf_form_fields()
for widget in page.widgets():
    field_name = widget.field_name

    if field_type == pymupdf.PDF_WIDGET_TYPE_TEXT:
        widget.field_value = str(value)
        widget.update()  # 更新字段但不扁平化
```

### 前端实现要点

```javascript
// 根据编辑模式选择PDF端点
const endpoint = shouldLoadEditable
  ? `/amlo/reservations/${id}/editable-pdf`  // 可编辑
  : `/amlo/reservations/${id}/generate-pdf`  // 最终版
```

---

## 总结

阶段1已经成功实现了：
- ✅ 后端返回可编辑PDF（保留AcroForm字段）
- ✅ 前端根据模式智能加载不同PDF
- ✅ PDF字段已自动填充数据
- ⚠️ PDF可编辑性取决于浏览器支持（Firefox最佳）

**当前状态**: 阶段1完成 ✅
**下一步**: 实施阶段2 - 双向同步功能

**测试结果**: 请在测试后反馈，以便进入阶段2实施。
