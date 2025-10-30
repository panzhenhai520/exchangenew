# AMLO PDF生成调试指南

**创建日期**: 2025-10-28
**目的**: 诊断PDF生成500错误但终端无错误信息的问题

---

## 问题描述

用户反馈：
1. 点击"查看PDF"按钮后出现500错误
2. 后端终端没有显示任何错误信息
3. `amlo_pdfs`文件夹没有被创建

---

## 已添加的调试日志

### 完整的12步调试日志

我在 `src/routes/app_amlo.py` 的 `generate_report_pdf` 函数中添加了详细的步骤日志：

| 步骤 | 日志消息 | 说明 |
|------|----------|------|
| STEP 1 | `[AMLO PDF STEP 1] 收到PDF生成请求` | 函数被调用 |
| STEP 2 | `[AMLO PDF STEP 2] 数据库会话已创建` | SessionLocal()成功 |
| STEP 3 | `[AMLO PDF STEP 3] 开始查询数据库...` | 开始查询Reserved_Transaction |
| STEP 4 | `[AMLO PDF STEP 4] 数据库查询完成` | 查询完成（成功/失败） |
| STEP 5 | `[AMLO PDF STEP 5] 准备文件路径...` | 设置临时文件和项目目录路径 |
| STEP 6 | `[AMLO PDF STEP 6] 创建amlo_pdfs目录...` | os.makedirs()调用 |
| STEP 7 | `[AMLO PDF STEP 7] 开始生成PDF...` | 调用AMLOPDFService |
| STEP 8 | `[AMLO PDF STEP 8] 构建预约数据...` | 准备reservation_data字典 |
| STEP 9 | `[AMLO PDF STEP 9] 调用PDF生成服务...` | service.generate_pdf_from_reservation() |
| STEP 10 | `[AMLO PDF STEP 10] PDF生成完成` | PDF文件已创建 |
| STEP 11 | `[AMLO PDF STEP 11] 复制PDF到项目目录...` | shutil.copy2()到amlo_pdfs/ |
| STEP 12 | `[AMLO PDF STEP 12] 准备返回PDF文件...` | send_file()调用 |

---

## 诊断步骤

### 1. 重启后端服务

```bash
# 停止当前运行的main.py (Ctrl+C)

# 重新启动
python src/main.py
```

**期望看到**:
```
[OK] 环境配置已同步
...
 * Running on http://192.168.0.9:5001
```

---

### 2. 重启前端服务（新终端）

```bash
# 停止当前运行的npm服务 (Ctrl+C)

# 重新启动
npm run serve
```

**期望看到**:
```
  App running at:
  - Local:   http://localhost:8080/
  - Network: http://192.168.0.9:8080/
```

---

### 3. 测试PDF生成并观察终端输出

**操作步骤**:
1. 登录系统
2. 进入 **AMLO审计** → **预约审核**
3. 找到一条预约记录（任何状态都可以）
4. 点击 **"查看PDF"** 按钮

**关键：立即查看后端终端窗口！**

---

## 可能的输出情况

### 情况A：完全没有任何输出

**说明**: 请求根本没有到达后端

**可能原因**:
1. ❌ 前端API调用的URL仍然错误
2. ❌ 浏览器CORS阻止
3. ❌ 网络连接问题

**检查方法**:
- 打开浏览器开发者工具（F12）
- 切换到 **Network** 标签
- 点击"查看PDF"
- 查看是否有请求发出
- 查看请求的URL是否正确：`http://192.168.0.9:5001/api/amlo/reports/[ID]/generate-pdf`

---

### 情况B：只看到STEP 1，然后就没有了

**输出示例**:
```
================================================================================
[AMLO PDF STEP 1] 收到PDF生成请求
[AMLO PDF] 报告ID: 53
[AMLO PDF] 用户: xxx
[AMLO PDF] 用户branch_id: 1
================================================================================
```

**说明**: 请求到达了，但在创建数据库会话时失败

**可能原因**:
1. ❌ 数据库连接失败
2. ❌ SessionLocal()配置错误

**解决方法**:
- 检查 `.env` 中的数据库配置
- 确认MySQL服务正在运行

---

### 情况C：看到STEP 1-4，然后报错"报告不存在"

**输出示例**:
```
[AMLO PDF STEP 4] 数据库查询完成
[AMLO PDF] 查询结果: 未找到记录
[AMLO PDF] ERROR: 报告不存在 - ID: 53, branch_id: 1
```

**说明**: 数据库中找不到该预约记录

**可能原因**:
1. ❌ 预约记录的branch_id与当前用户的branch_id不匹配
2. ❌ 预约记录ID错误

**解决方法**:
- 使用其他预约记录测试
- 检查数据库中的 `Reserved_Transaction` 表

---

### 情况D：看到STEP 1-6，显示目录创建完成

**输出示例**:
```
[AMLO PDF STEP 6] 创建amlo_pdfs目录...
[AMLO PDF] 目录创建完成: True
[AMLO PDF] 项目PDF路径: D:\Code\ExchangeNew\amlo_pdfs\AMLO-1-01_A001-2025-001.pdf
```

**说明**: 目录创建成功！请检查项目根目录

**检查**:
- 打开 `D:\Code\ExchangeNew\`
- 应该看到 `amlo_pdfs` 文件夹存在
- 如果看到了，说明代码运行到这里了

---

### 情况E：在STEP 9时报错

**输出示例**:
```
[AMLO PDF STEP 9] 调用PDF生成服务...
[AMLO PDF] 目标路径: C:\Users\...\Temp\AMLO-1-01_53.pdf

================================================================================
[ERROR] AMLO PDF生成失败！
================================================================================
错误类型: FileNotFoundError
错误信息: 生成PDF失败: [Errno 2] No such file or directory: 'D:\\Code\\ExchangeNew\\Re\\1-01-fill.pdf'
...
```

**说明**: PDF模板文件缺失

**解决方法**:
- 检查 `D:\Code\ExchangeNew\Re\` 目录
- 确认存在 `1-01-fill.pdf`、`1-02-fill.pdf`、`1-03-fill.pdf` 三个模板文件

---

### 情况F：在STEP 9时报错 - CSV文件问题

**输出示例**:
```
错误类型: FileNotFoundError
错误信息: 生成PDF失败: [Errno 2] No such file or directory: 'D:\\Code\\ExchangeNew\\Re\\1-01-field-map.csv'
```

**说明**: CSV字段映射文件缺失

**解决方法**:
- 检查 `D:\Code\ExchangeNew\Re\` 目录
- 确认存在以下文件：
  - `1-01-field-map.csv`
  - `1-02-field-map.csv`
  - `1-03-field-map.csv`

**重要**:
- ✅ 使用 `1-01-field-map.csv` 等文件（正确）
- ❌ **不要使用** `fillpos1-01.csv` 等文件（已作废）

---

### 情况G：成功生成PDF

**输出示例**:
```
[AMLO PDF STEP 10] PDF生成完成
[AMLO PDF] 返回路径: C:\Users\...\Temp\AMLO-1-01_A001-2025-001.pdf
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
[AMLO PDF] 使用send_file发送: C:\Users\...\Temp\AMLO-1-01_A001-2025-001.pdf
```

**说明**: PDF生成成功！✅

**验证**:
1. 打开 `D:\Code\ExchangeNew\amlo_pdfs\`
2. 应该看到新生成的PDF文件
3. 双击打开验证内容

---

## CSV文件使用验证

### 代码已确认使用正确的CSV文件

文件: `src/services/pdf/amlo_csv_field_loader.py` (第42-46行)

```python
csv_files = {
    'AMLO-1-01': '1-01-field-map.csv',  # ✅ 正确
    'AMLO-1-02': '1-02-field-map.csv',  # ✅ 正确
    'AMLO-1-03': '1-03-field-map.csv'   # ✅ 正确
}
```

**确认**: 代码**已经使用**正确的CSV文件，**没有使用**fillpos系列文件。

---

## 前端Network调试

### 检查请求URL是否正确

**步骤**:
1. 打开浏览器开发者工具（F12）
2. 切换到 **Network** 标签
3. 点击"查看PDF"按钮
4. 找到 `generate-pdf` 请求
5. 检查以下信息：

**正确的请求**:
```
Request URL: http://192.168.0.9:5001/api/amlo/reports/53/generate-pdf
Request Method: GET
Status Code: 200 OK
Request Headers:
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
Response Headers:
  Content-Type: application/pdf
  Content-Disposition: attachment; filename=AMLO-1-01_A001-2025-001.pdf
```

**错误的请求（已修复）**:
```
Request URL: http://192.168.0.9:5001/apiamlo/reports/53/generate-pdf  ❌ 错误
# 缺少斜杠：/api 和 amlo 连在一起了
```

---

## 浏览器控制台调试

### 检查前端JavaScript日志

**步骤**:
1. 打开浏览器开发者工具（F12）
2. 切换到 **Console** 标签
3. 点击"查看PDF"按钮
4. 查看以下日志：

**正确的日志**:
```
[ReservationListSimple] 生成PDF - 预约ID: 53
[ReservationListSimple] PDF响应: {data: Blob, status: 200, ...}
[ReservationListSimple] PDF文件大小: 123456 bytes
```

**错误的日志**:
```
[ReservationListSimple] 生成PDF - 预约ID: 53
[ReservationListSimple] 打开PDF失败: Error: Request failed with status code 500
```

---

## 文件名格式说明

### 当前PDF文件名格式

```
{报告类型}_{预约编号}.pdf
```

**示例**:
- `AMLO-1-01_A001-2025-001.pdf` （有预约编号）
- `AMLO-1-01_53.pdf` （没有预约编号，使用ID）

**字段来源**:
- `报告类型`: `Reserved_Transaction.report_type` (如 AMLO-1-01)
- `预约编号`: `Reserved_Transaction.reservation_no` (如 A001-2025-001)
- `ID`: `Reserved_Transaction.id` (如 53)

**逻辑**:
```python
pdf_filename = f"{result.report_type}_{result.reservation_no or result.id}.pdf"
```

如果 `reservation_no` 存在，使用它；否则使用 `id`。

---

## 需要检查的文件清单

### PDF模板文件（必需）

```
D:\Code\ExchangeNew\Re\1-01-fill.pdf  ← AMLO-1-01模板
D:\Code\ExchangeNew\Re\1-02-fill.pdf  ← AMLO-1-02模板
D:\Code\ExchangeNew\Re\1-03-fill.pdf  ← AMLO-1-03模板
```

### CSV字段映射文件（必需）

```
D:\Code\ExchangeNew\Re\1-01-field-map.csv  ← AMLO-1-01字段映射
D:\Code\ExchangeNew\Re\1-02-field-map.csv  ← AMLO-1-02字段映射
D:\Code\ExchangeNew\Re\1-03-field-map.csv  ← AMLO-1-03字段映射
```

### 生成的PDF文件（运行后）

```
D:\Code\ExchangeNew\amlo_pdfs\AMLO-1-01_*.pdf  ← 生成的PDF
D:\Code\ExchangeNew\amlo_pdfs\AMLO-1-02_*.pdf
D:\Code\ExchangeNew\amlo_pdfs\AMLO-1-03_*.pdf
```

---

## 常见问题排查

### Q1: 终端完全没有任何输出？

**检查清单**:
- [ ] 后端服务是否正在运行？
- [ ] 浏览器Network标签是否看到请求发出？
- [ ] 请求URL是否正确（有 `/api/` 而不是 `/apiamlo/`）？
- [ ] 是否有CORS错误（控制台红色错误）？

---

### Q2: 看到STEP 1但之后就没了？

**可能原因**: 数据库连接失败

**检查**:
```bash
# 检查MySQL是否运行
# Windows任务管理器 → 服务 → MySQL

# 或使用命令
mysql -u root -p
# 如果能连接，说明MySQL正常
```

---

### Q3: 报错"报告不存在"？

**检查数据库**:
```sql
-- 查询预约记录
SELECT id, reservation_no, report_type, branch_id, status
FROM Reserved_Transaction
WHERE id = 53;  -- 替换为实际ID

-- 检查用户的branch_id
SELECT id, username, branch_id
FROM operators
WHERE username = 'admin';  -- 替换为实际用户名
```

**确认**:
- 预约记录的 `branch_id` 必须与当前用户的 `branch_id` 匹配

---

### Q4: 报错找不到PDF模板文件？

**检查文件是否存在**:
```bash
# Windows文件管理器
打开: D:\Code\ExchangeNew\Re\

# 应该看到:
1-01-fill.pdf
1-02-fill.pdf
1-03-fill.pdf
1-01-field-map.csv
1-02-field-map.csv
1-03-field-map.csv
```

如果文件不存在，需要从备份或其他地方恢复这些文件。

---

### Q5: PDF生成了但内容是空白或乱码？

**可能原因**:
1. CSV字段映射坐标不正确
2. form_data字段为空或格式错误
3. 字体文件缺失（泰文/中文字符）

**检查form_data**:
```sql
SELECT id, reservation_no, form_data
FROM Reserved_Transaction
WHERE id = 53;
```

`form_data` 应该是有效的JSON字符串，包含表单数据。

---

## 下一步操作

### 请按以下步骤测试并报告：

1. **重启后端和前端服务**
2. **点击"查看PDF"按钮**
3. **立即查看后端终端输出**
4. **将终端的完整输出复制给我**

**重要**: 即使没有错误，也请把所有 `[AMLO PDF]` 开头的日志都复制给我。这些日志会告诉我程序执行到哪一步了。

---

**创建人员**: Claude Code Assistant
**修改日期**: 2025-10-28
**目的**: 帮助诊断PDF生成500错误但无终端日志的问题
