# AMLO PDF生成器清理计划

## 当前状况

`src/services/pdf/` 目录中存在**多个版本**的PDF生成器,导致混乱:

### 旧版本 (应删除)
- `amlo_pdf_generator.py` - 旧版PDF生成器
- `amlo_pdf_generator_precise.py` - 旧版精确定位版本
- `amlo_pdf_generator_v2.py` - 旧版V2
- `amlo_form_filler.py` - 旧版表单填充器
- `amlo_101_exact.py` - 旧版AMLO-1-01专用
- `amlo_101_final.py` - 旧版AMLO-1-01最终版
- `amlo_101_from_config.py` - 旧版基于配置
- `amlo_101_measured.py` - 旧版测量版
- `amlo_101_precise.py` - 旧版精确版
- `amlo_field_mappings.py` - 旧版字段映射
- `amlo_field_mapping.py` - 旧版字段映射(单数)
- `analyze_standard_pdf.py` - PDF分析工具(测试用)
- `extract_layout_coordinates.py` - 坐标提取工具(测试用)

### 新版本 (保留) ✅
- `amlo_csv_field_loader.py` - CSV字段映射加载器
- `amlo_data_mapper.py` - 业务数据映射器
- `amlo_pdf_filler_v2.py` - PyPDF2表单填充器
- `amlo_pdf_service.py` - 集成服务
- `__init__.py` - 模块导出

## 推荐操作

### 创建备份目录
```bash
cd D:\Code\ExchangeNew\src\services\pdf
mkdir _deprecated_backup_20251028
```

### 移动旧文件到备份 (不删除,以防万一)
```bash
move amlo_pdf_generator.py _deprecated_backup_20251028/
move amlo_pdf_generator_precise.py _deprecated_backup_20251028/
move amlo_pdf_generator_v2.py _deprecated_backup_20251028/
move amlo_form_filler.py _deprecated_backup_20251028/
move amlo_101_*.py _deprecated_backup_20251028/
move amlo_field_mapping*.py _deprecated_backup_20251028/
move analyze_standard_pdf.py _deprecated_backup_20251028/
move extract_layout_coordinates.py _deprecated_backup_20251028/
```

### 更新 `__init__.py`

从:
```python
from .amlo_pdf_generator import AMLOPDFGenerator
from .amlo_form_filler import AMLOFormFiller, adapt_route_data_to_pdf_data

# 新版AMLO PDF服务 (基于CSV字段映射)
from .amlo_pdf_service import AMLOPDFService, generate_amlo_pdf
from .amlo_csv_field_loader import AMLOCSVFieldLoader, get_csv_field_loader
from .amlo_pdf_filler_v2 import AMLOPDFFiller
from .amlo_data_mapper import AMLODataMapper

__all__ = [
    # 旧版兼容
    'AMLOPDFGenerator',
    'AMLOFormFiller',
    'adapt_route_data_to_pdf_data',

    # 新版服务 (推荐使用)
    'AMLOPDFService',
    'generate_amlo_pdf',
    'AMLOCSVFieldLoader',
    'get_csv_field_loader',
    'AMLOPDFFiller',
    'AMLODataMapper',
]
```

改为:
```python
# 新版AMLO PDF服务 (基于CSV字段映射)
from .amlo_pdf_service import AMLOPDFService, generate_amlo_pdf
from .amlo_csv_field_loader import AMLOCSVFieldLoader, get_csv_field_loader
from .amlo_pdf_filler_v2 import AMLOPDFFiller
from .amlo_data_mapper import AMLODataMapper

__all__ = [
    'AMLOPDFService',
    'generate_amlo_pdf',
    'AMLOCSVFieldLoader',
    'get_csv_field_loader',
    'AMLOPDFFiller',
    'AMLODataMapper',
]
```

## 检查依赖

在删除前,确保没有其他文件引用旧版本:

```bash
cd D:\Code\ExchangeNew\src
grep -r "from.*amlo_pdf_generator import" .
grep -r "from.*amlo_form_filler import" .
```

**如果发现引用,需要先更新为新版本**

## 最终目录结构

```
src/services/pdf/
├── __init__.py                    # 模块导出
├── amlo_csv_field_loader.py       # CSV字段加载器 ✅
├── amlo_data_mapper.py            # 数据映射器 ✅
├── amlo_pdf_filler_v2.py          # PDF填充器 ✅
├── amlo_pdf_service.py            # 集成服务 ✅
└── _deprecated_backup_20251028/   # 备份目录
    ├── amlo_pdf_generator.py
    ├── amlo_form_filler.py
    └── ... (所有旧文件)
```

## 验证

移动文件后,测试PDF生成功能:

```bash
cd src/services/pdf
python amlo_pdf_service.py
```

应该看到:
```
[AMLOPDFService] Initialized successfully
[AMLOPDFService] Generating AMLO-1-01 PDF
[AMLOPDFService] Mapped 44 fields
[AMLOPDFFiller] Filled 88 fields
SUCCESS! PDF created at: ...
```

## 状态

- ⏳ **待执行** - 需用户确认后执行
- 📋 **建议**: 先备份,不要直接删除
- ⚠️ **注意**: 检查是否有route文件仍在使用旧版本

---

**创建时间**: 2025-10-28
**维护**: Claude Code Assistant
