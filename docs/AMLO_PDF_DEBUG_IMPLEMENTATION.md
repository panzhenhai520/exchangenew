# AMLO PDF生成调试日志实现

**实施日期**: 2025-10-28
**状态**: ✅ 已完成
**目的**: 添加详细的步骤日志以诊断PDF生成500错误但终端无错误的问题

---

## 问题背景

### 用户反馈的问题

1. 点击"查看PDF"按钮后出现500错误
2. **后端终端没有显示任何错误信息** ← 关键问题
3. `amlo_pdfs`文件夹没有被创建
4. PDF文件名应该和报告编号一致
5. 必须使用正确的CSV文件（`1-01-field-map.csv`，不是fillpos系列）

### 问题诊断难点

由于没有错误日志，无法确定：
- 请求是否到达后端？
- 在哪一步失败的？
- 是认证问题、数据库问题还是文件问题？

---

## 解决方案：添加12步调试日志

### 实施文件

**文件**: `src/routes/app_amlo.py`
**函数**: `generate_report_pdf` (行 1039-1220)
**修改**: 在整个PDF生成流程的每个关键步骤添加详细日志

---

## 添加的调试日志详情

### STEP 1: 请求接收确认

**位置**: 函数入口 (行 1052-1057)

```python
print(f"\n{'='*80}")
print(f"[AMLO PDF STEP 1] 收到PDF生成请求")
print(f"[AMLO PDF] 报告ID: {report_id}")
print(f"[AMLO PDF] 用户: {current_user}")
print(f"[AMLO PDF] 用户branch_id: {g.current_user.get('branch_id')}")
print(f"{'='*80}\n")
```

**目的**:
- 确认函数被调用
- 显示请求参数
- 确认用户身份和权限

**如果看不到这个日志**:
→ 说明请求根本没到达这个函数
→ 可能是认证/权限问题或URL错误

---

### STEP 2: 数据库会话创建

**位置**: 行 1060

```python
session = SessionLocal()
print(f"[AMLO PDF STEP 2] 数据库会话已创建")
```

**目的**: 确认数据库连接正常

**如果卡在这里**:
→ 数据库连接配置错误
→ MySQL服务未运行

---

### STEP 3-4: 数据库查询

**位置**: 行 1064-1098

```python
print(f"[AMLO PDF STEP 3] 开始查询数据库...")
# ... SQL查询 ...
print(f"[AMLO PDF] 查询参数: {query_params}")

result = session.execute(report_sql, query_params).fetchone()

print(f"[AMLO PDF STEP 4] 数据库查询完成")
print(f"[AMLO PDF] 查询结果: {'找到记录' if result else '未找到记录'}")

if not result:
    print(f"[AMLO PDF] ERROR: 报告不存在 - ID: {report_id}, branch_id: {g.current_user.get('branch_id')}")
    return jsonify({'success': False, 'message': '报告不存在'}), 404

print(f"[AMLO PDF] 报告类型: {result.report_type}")
print(f"[AMLO PDF] 预约编号: {result.reservation_no}")
```

**目的**:
- 显示查询参数（report_id, branch_id）
- 显示是否找到记录
- 如果没找到，显示详细原因

**如果报错"报告不存在"**:
→ 预约记录的branch_id与用户不匹配
→ 或该ID的记录不存在

---

### STEP 5-6: 文件路径设置和目录创建

**位置**: 行 1101-1119

```python
print(f"[AMLO PDF STEP 5] 准备文件路径...")
temp_dir = tempfile.gettempdir()
pdf_filename = f"{result.report_type}_{result.reservation_no or result.id}.pdf"
pdf_path = os.path.join(temp_dir, pdf_filename)
print(f"[AMLO PDF] 临时文件路径: {pdf_path}")

# 项目目录路径
project_root = os.path.dirname(os.path.dirname(os.path.dirname(__file__)))
amlo_pdf_dir = os.path.join(project_root, 'amlo_pdfs')
print(f"[AMLO PDF] 项目根目录: {project_root}")
print(f"[AMLO PDF] PDF保存目录: {amlo_pdf_dir}")
print(f"[AMLO PDF] 目录是否存在: {os.path.exists(amlo_pdf_dir)}")

print(f"[AMLO PDF STEP 6] 创建amlo_pdfs目录...")
os.makedirs(amlo_pdf_dir, exist_ok=True)
print(f"[AMLO PDF] 目录创建完成: {os.path.exists(amlo_pdf_dir)}")

project_pdf_path = os.path.join(amlo_pdf_dir, pdf_filename)
print(f"[AMLO PDF] 项目PDF路径: {project_pdf_path}")
```

**目的**:
- 显示所有路径信息
- **确认amlo_pdfs目录是否被创建**
- 显示PDF文件名格式

**关键输出**:
```
[AMLO PDF] PDF保存目录: D:\Code\ExchangeNew\amlo_pdfs
[AMLO PDF] 目录是否存在: False  ← 创建前
[AMLO PDF] 目录创建完成: True   ← 创建后
```

**如果目录创建失败**:
→ 可能是权限问题
→ 或磁盘空间不足

---

### STEP 7-10: PDF生成

**位置**: 行 1122-1160

```python
print(f"[AMLO PDF STEP 7] 开始生成PDF...")
logger.info(f"生成AMLO PDF - 记录ID: {report_id}, 类型: {result.report_type}")

from services.pdf import AMLOPDFService
print(f"[AMLO PDF] 导入AMLOPDFService成功")
service = AMLOPDFService()
print(f"[AMLO PDF] AMLOPDFService实例化成功")

print(f"[AMLO PDF STEP 8] 构建预约数据...")
reservation_data = { ... }
print(f"[AMLO PDF] 预约数据: ID={reservation_data['id']}, 类型={reservation_data['report_type']}")

print(f"[AMLO PDF STEP 9] 调用PDF生成服务...")
print(f"[AMLO PDF] 目标路径: {pdf_path}")
result_path = service.generate_pdf_from_reservation(reservation_data, pdf_path)

print(f"[AMLO PDF STEP 10] PDF生成完成")
print(f"[AMLO PDF] 返回路径: {result_path}")
print(f"[AMLO PDF] 文件存在: {os.path.exists(result_path)}")
if os.path.exists(result_path):
    print(f"[AMLO PDF] 文件大小: {os.path.getsize(result_path)} bytes")
```

**目的**:
- 确认AMLOPDFService导入成功
- 显示传递给PDF生成器的数据
- 确认PDF文件是否生成
- 显示文件大小

**如果在STEP 9失败**:
→ 可能是模板文件缺失（`Re/1-01-fill.pdf`）
→ 或CSV映射文件缺失（`Re/1-01-field-map.csv`）
→ 或form_data格式错误

---

### STEP 11: 复制PDF到项目目录

**位置**: 行 1165-1184

```python
print(f"[AMLO PDF STEP 11] 复制PDF到项目目录...")
try:
    import shutil
    shutil.copy2(result_path, project_pdf_path)
    print(f"[AMLO PDF] 复制成功")
    print(f"[AMLO PDF] 副本存在: {os.path.exists(project_pdf_path)}")
    if os.path.exists(project_pdf_path):
        print(f"[AMLO PDF] 副本大小: {os.path.getsize(project_pdf_path)} bytes")

    # 成功提示框
    print(f"\n{'='*80}")
    print(f"[OK] AMLO PDF生成成功！")
    print(f"{'='*80}")
    print(f"临时文件: {result_path}")
    print(f"项目副本: {project_pdf_path}")
    print(f"文件名: {pdf_filename}")
    print(f"{'='*80}\n")
except Exception as copy_error:
    print(f"[AMLO PDF] WARNING: 复制失败: {copy_error}")
```

**目的**:
- 确认文件复制成功
- **显示PDF保存的最终路径**（用户要求）
- 显示文件名（确认格式正确）

**成功输出示例**:
```
================================================================================
[OK] AMLO PDF生成成功！
================================================================================
临时文件: C:\Users\Administrator\AppData\Local\Temp\AMLO-1-01_A001-2025-001.pdf
项目副本: D:\Code\ExchangeNew\amlo_pdfs\AMLO-1-01_A001-2025-001.pdf
文件名: AMLO-1-01_A001-2025-001.pdf
================================================================================
```

---

### STEP 12: 返回PDF文件

**位置**: 行 1187-1194

```python
print(f"[AMLO PDF STEP 12] 准备返回PDF文件...")
print(f"[AMLO PDF] 使用send_file发送: {result_path}")
return send_file(
    result_path,
    mimetype='application/pdf',
    as_attachment=True,
    download_name=pdf_filename
)
```

**目的**:
- 确认send_file被调用
- 显示返回的文件路径

---

### 异常处理增强

**位置**: 行 1196-1215

```python
except Exception as e:
    error_msg = f"生成PDF失败: {str(e)}"
    error_type = type(e).__name__
    logger.error(f"Error in generate_report_pdf: {error_msg}")

    print(f"\n{'='*80}")
    print(f"[ERROR] AMLO PDF生成失败！")
    print(f"{'='*80}")
    print(f"错误类型: {error_type}")
    print(f"错误信息: {error_msg}")
    print(f"报告ID: {report_id}")
    print(f"详细堆栈:")
    traceback.print_exc()
    print(f"{'='*80}\n")

    return jsonify({
        'success': False,
        'message': error_msg,
        'error_type': error_type
    }), 500
```

**改进**:
- 添加错误类型（如 `FileNotFoundError`、`KeyError`）
- 显示报告ID
- 完整的traceback堆栈
- 返回给前端的错误也包含类型

---

### Finally块增强

**位置**: 行 1217-1220

```python
finally:
    print(f"[AMLO PDF] 关闭数据库会话")
    session.close()
    print(f"[AMLO PDF] 请求处理完成\n")
```

**目的**: 确认清理工作完成

---

## CSV文件验证

### 已确认代码使用正确的文件

**文件**: `src/services/pdf/amlo_csv_field_loader.py` (行 42-46)

```python
csv_files = {
    'AMLO-1-01': '1-01-field-map.csv',  # ✅ 正确
    'AMLO-1-02': '1-02-field-map.csv',  # ✅ 正确
    'AMLO-1-03': '1-03-field-map.csv'   # ✅ 正确
}
```

**结论**:
- ✅ 代码已使用正确的CSV文件
- ❌ 没有使用fillpos系列文件
- **无需修改**

---

## PDF文件名格式

### 当前实现

**代码** (行 1103):
```python
pdf_filename = f"{result.report_type}_{result.reservation_no or result.id}.pdf"
```

**逻辑**:
- 使用 `report_type` (如 AMLO-1-01)
- 优先使用 `reservation_no` (如 A001-2025-001)
- 如果 `reservation_no` 为空，使用 `id` (如 53)

**示例**:
- `AMLO-1-01_A001-2025-001.pdf` （有预约编号）
- `AMLO-1-01_53.pdf` （无预约编号，使用ID）

**符合用户要求**: ✅ 文件名与报告编号一致

---

## 预期终端输出

### 成功案例的完整输出

```
================================================================================
[AMLO PDF STEP 1] 收到PDF生成请求
[AMLO PDF] 报告ID: 53
[AMLO PDF] 用户: {'id': 1, 'username': 'admin'}
[AMLO PDF] 用户branch_id: 1
================================================================================

[AMLO PDF STEP 2] 数据库会话已创建
[AMLO PDF STEP 3] 开始查询数据库...
[AMLO PDF] 查询参数: {'report_id': 53, 'branch_id': 1}
[AMLO PDF STEP 4] 数据库查询完成
[AMLO PDF] 查询结果: 找到记录
[AMLO PDF] 报告类型: AMLO-1-01
[AMLO PDF] 预约编号: A001-2025-001
[AMLO PDF STEP 5] 准备文件路径...
[AMLO PDF] 临时文件路径: C:\Users\Administrator\AppData\Local\Temp\AMLO-1-01_A001-2025-001.pdf
[AMLO PDF] 项目根目录: D:\Code\ExchangeNew
[AMLO PDF] PDF保存目录: D:\Code\ExchangeNew\amlo_pdfs
[AMLO PDF] 目录是否存在: False
[AMLO PDF STEP 6] 创建amlo_pdfs目录...
[AMLO PDF] 目录创建完成: True
[AMLO PDF] 项目PDF路径: D:\Code\ExchangeNew\amlo_pdfs\AMLO-1-01_A001-2025-001.pdf
[AMLO PDF STEP 7] 开始生成PDF...
[AMLO PDF] 导入AMLOPDFService成功
[AMLO PDF] AMLOPDFService实例化成功
[AMLO PDF STEP 8] 构建预约数据...
[AMLO PDF] 预约数据: ID=53, 类型=AMLO-1-01
[AMLO PDF STEP 9] 调用PDF生成服务...
[AMLO PDF] 目标路径: C:\Users\Administrator\AppData\Local\Temp\AMLO-1-01_A001-2025-001.pdf
[AMLO PDF STEP 10] PDF生成完成
[AMLO PDF] 返回路径: C:\Users\Administrator\AppData\Local\Temp\AMLO-1-01_A001-2025-001.pdf
[AMLO PDF] 文件存在: True
[AMLO PDF] 文件大小: 123456 bytes
[AMLO PDF STEP 11] 复制PDF到项目目录...
[AMLO PDF] 复制成功
[AMLO PDF] 副本存在: True
[AMLO PDF] 副本大小: 123456 bytes

================================================================================
[OK] AMLO PDF生成成功！
================================================================================
临时文件: C:\Users\Administrator\AppData\Local\Temp\AMLO-1-01_A001-2025-001.pdf
项目副本: D:\Code\ExchangeNew\amlo_pdfs\AMLO-1-01_A001-2025-001.pdf
文件名: AMLO-1-01_A001-2025-001.pdf
================================================================================

[AMLO PDF STEP 12] 准备返回PDF文件...
[AMLO PDF] 使用send_file发送: C:\Users\Administrator\AppData\Local\Temp\AMLO-1-01_A001-2025-001.pdf
192.168.0.9 - - [28/Oct/2025 14:32:15] "GET /api/amlo/reports/53/generate-pdf HTTP/1.1" 200 -
[AMLO PDF] 关闭数据库会话
[AMLO PDF] 请求处理完成
```

### 失败案例示例（模板文件缺失）

```
================================================================================
[AMLO PDF STEP 1] 收到PDF生成请求
[AMLO PDF] 报告ID: 53
...
[AMLO PDF STEP 9] 调用PDF生成服务...
[AMLO PDF] 目标路径: C:\Users\...\Temp\AMLO-1-01_53.pdf

================================================================================
[ERROR] AMLO PDF生成失败！
================================================================================
错误类型: FileNotFoundError
错误信息: 生成PDF失败: [Errno 2] No such file or directory: 'D:\\Code\\ExchangeNew\\Re\\1-01-fill.pdf'
报告ID: 53
详细堆栈:
Traceback (most recent call last):
  File "D:\Code\ExchangeNew\src\routes\app_amlo.py", line 1155, in generate_report_pdf
    result_path = service.generate_pdf_from_reservation(reservation_data, pdf_path)
  File "D:\Code\ExchangeNew\src\services\pdf\amlo_pdf_service.py", line 123, in generate_pdf_from_reservation
    template_pdf = PdfReader(open(template_path, 'rb'))
FileNotFoundError: [Errno 2] No such file or directory: 'D:\\Code\\ExchangeNew\\Re\\1-01-fill.pdf'
================================================================================

[AMLO PDF] 关闭数据库会话
[AMLO PDF] 请求处理完成
```

---

## 测试步骤

### 1. 重启服务

```bash
# 终端1: 重启后端
# Ctrl+C 停止当前服务
python src/main.py

# 终端2: 重启前端
# Ctrl+C 停止当前服务
npm run serve
```

### 2. 测试PDF生成

1. 登录系统
2. 进入 **AMLO审计** → **预约审核**
3. 点击任一记录的 **"查看PDF"** 按钮
4. **立即查看后端终端窗口**

### 3. 报告结果

**请将后端终端的完整输出复制给我**，包括：
- 所有 `[AMLO PDF]` 开头的日志
- 任何错误信息
- 如果成功，应该看到 `[OK] AMLO PDF生成成功！`

---

## 成功标志

### 如果一切正常，应该看到：

1. **终端输出**: 所有12个STEP都完成，最后显示 `[OK] AMLO PDF生成成功！`

2. **文件系统**: `D:\Code\ExchangeNew\amlo_pdfs\` 目录存在且包含PDF文件

3. **浏览器**: PDF在新窗口打开或自动下载

---

## 相关文件

### 修改的文件

- ✅ `src/routes/app_amlo.py` (行 1039-1220)
  - 添加12步调试日志
  - 增强异常处理
  - 确认CSV文件使用正确

### 创建的文档

- ✅ `docs/AMLO_PDF_DEBUG_GUIDE.md` - 用户调试指南
- ✅ `docs/AMLO_PDF_DEBUG_IMPLEMENTATION.md` - 技术实现文档（本文档）

---

## 下一步

等待用户测试并提供：
1. 后端终端完整输出
2. 浏览器控制台错误（如果有）
3. 是否看到 `amlo_pdfs` 文件夹
4. 如果成功，PDF内容是否正确

根据输出，可以精确定位问题所在。

---

**实施人员**: Claude Code Assistant
**实施日期**: 2025-10-28
**状态**: ✅ 已部署，待测试验证
