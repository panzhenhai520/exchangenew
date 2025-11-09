#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查动态表单生成逻辑是否完整
验证: 字段管理中有N个字段 → 表单应该有N个输入框 → PDF应该有N个数据
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from sqlalchemy import text

def check_field_counts():
    """检查每种报告类型的字段数量"""
    session = DatabaseService.get_session()
    
    try:
        print("="*80)
        print("检查字段管理中每种报告类型的字段数量")
        print("="*80)
        
        report_types = ['AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03']
        
        for report_type in report_types:
            sql = text("""
                SELECT COUNT(*) as total_fields
                FROM report_fields
                WHERE report_type = :report_type
                AND is_active = 1
            """)
            
            result = session.execute(sql, {'report_type': report_type}).fetchone()
            total = result[0] if result else 0
            
            print(f"\n{report_type}: {total} 个字段")
            
            # 查询字段详情
            sql_detail = text("""
                SELECT 
                    id,
                    field_name,
                    field_cn_name,
                    field_th_name,
                    field_type,
                    fill_order,
                    is_required
                FROM report_fields
                WHERE report_type = :report_type
                AND is_active = 1
                ORDER BY fill_order
                LIMIT 10
            """)
            
            results = session.execute(sql_detail, {'report_type': report_type}).fetchall()
            
            if results:
                print(f"\n  前10个字段示例:")
                for idx, row in enumerate(results, 1):
                    print(f"    {idx}. {row[1]} - {row[2]} ({row[4]})")
                
                if total > 10:
                    print(f"    ... 还有 {total - 10} 个字段")
        
        print("\n" + "="*80)
        print("结论:")
        print("="*80)
        print("\n如果字段管理中定义了N个字段，")
        print("那么动态表单应该生成N个输入框，")
        print("PDF报告应该填充N个数据字段。")
        print("\n现在需要检查前端和后端的代码逻辑是否正确实现了这一点。")
        
    finally:
        DatabaseService.close_session(session)

def trace_api_flow():
    """追踪API数据流"""
    print("\n" + "="*80)
    print("追踪数据流: 字段管理 → API → 前端 → PDF")
    print("="*80)
    
    print("\n【步骤1】后端API查询")
    print("-" * 80)
    print("文件: src/routes/app_repform.py")
    print("API: GET /api/repform/form-definition/<report_type>")
    print()
    print("代码逻辑:")
    print("  1. 调用 FieldManager.get_form_definition(session, report_type, language)")
    print("  2. 返回 {'success': True, 'data': form_definition}")
    print()
    print("问题检查:")
    print("  ❓ FieldManager是否返回所有字段？")
    print("  ❓ 是否有过滤逻辑？")
    
    print("\n【步骤2】FieldManager查询逻辑")
    print("-" * 80)
    print("文件: src/services/repform/field_manager.py")
    print()
    print("代码逻辑:")
    print("  get_form_definition():")
    print("    1. fields = get_fields_by_report_type(report_type, language)")
    print("    2. 按field_group分组: grouped_fields = {}")
    print("    3. 返回 {'field_groups': field_groups, 'total_fields': len(fields)}")
    print()
    print("  get_fields_by_report_type():")
    print("    1. SELECT * FROM report_fields")
    print("    2. WHERE report_type = :report_type")
    print("    3. AND is_active = TRUE")
    print("    4. ORDER BY fill_order")
    print()
    print("问题检查:")
    print("  ✅ 查询所有字段（无LIMIT）")
    print("  ✅ 只过滤is_active=TRUE")
    print("  ✅ 按fill_order排序")
    print("  结论: 后端API应该返回所有启用的字段")
    
    print("\n【步骤3】前端Store接收")
    print("-" * 80)
    print("文件: src/stores/amlo.js")
    print()
    print("代码逻辑:")
    print("  async fetchFormDefinition(reportType, language):")
    print("    1. response = await axios.get('/api/repform/form-definition/{reportType}')")
    print("    2. this.formDefinitions[reportType] = response.data.data")
    print("    3. return response.data")
    print()
    print("问题检查:")
    print("  ✅ 完整接收API返回的数据")
    print("  ❓ 但是否被其他地方过滤？")
    
    print("\n【步骤4】前端表单组件渲染")
    print("-" * 80)
    print("文件: src/components/amlo/DynamicForm/DynamicForm.vue")
    print()
    print("代码逻辑:")
    print("  loadFormDefinition():")
    print("    1. response = await amloStore.fetchFormDefinition(reportType, language)")
    print("    2. formFields.value = response.data.fields || []")
    print("    3. formData.value = buildFormData(formFields.value, initialData)")
    print()
    print("  模板渲染:")
    print("    <FormField")
    print("      v-for='field in formFields'")
    print("      :key='field.field_id'")
    print("      :field='field'")
    print("    />")
    print()
    print("问题检查:")
    print("  ❓ response.data.fields 是什么？")
    print("  ❓ 应该是 response.data.field_groups 还是扁平化的fields？")
    print("  ⚠️ 这里可能有问题！")
    
    print("\n【步骤5】关键问题点")
    print("-" * 80)
    print("后端返回的数据结构:")
    print("  {")
    print("    'report_type': 'AMLO-1-01',")
    print("    'report_name': '现金交易报告',")
    print("    'field_groups': [                    ← 分组后的字段")
    print("      {")
    print("        'group_name': '交易者信息',")
    print("        'fields': [...]                 ← 字段在这里")
    print("      },")
    print("      {")
    print("        'group_name': '交易详情',")
    print("        'fields': [...]")
    print("      }")
    print("    ],")
    print("    'total_fields': 73                   ← 总字段数")
    print("  }")
    print()
    print("前端读取:")
    print("  formFields.value = response.data.fields || []")
    print("                                   ^^^^^^")
    print("  🔴 问题: response.data 中没有 'fields' 字段！")
    print("  🔴 只有 'field_groups' 字段！")
    print("  🔴 所以 formFields.value = [] （空数组）")
    
    print("\n【步骤6】验证问题")
    print("-" * 80)
    print("需要检查的文件:")
    print("  1. DynamicForm.vue 中如何读取字段")
    print("  2. 是否需要从field_groups中提取所有fields")
    print("  3. 还是API应该返回扁平化的fields数组")

def main():
    print("\n" + "="*80)
    print("动态表单逻辑完整性检查")
    print("="*80)
    print("检查目标: 字段管理有N个字段 → 表单有N个输入框 → PDF有N个数据\n")
    
    # 检查字段数量
    check_field_counts()
    
    # 追踪数据流
    trace_api_flow()
    
    print("\n" + "="*80)
    print("下一步行动")
    print("="*80)
    print("\n需要详细检查:")
    print("  1. DynamicForm.vue 如何读取 response.data")
    print("  2. 是读取 response.data.fields 还是 response.data.field_groups")
    print("  3. 如果读取field_groups，是否正确展平所有字段")
    print()
    print("预计问题:")
    print("  🔴 前端读取了错误的字段路径")
    print("  🔴 导致 formFields = [] 空数组")
    print("  🔴 所以表单没有渲染任何字段")
    print()

if __name__ == "__main__":
    main()

