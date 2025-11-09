#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
检查完整链条：字段管理 → 表单生成 → PDF生成
找出问题所在
"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')

from services.db_service import DatabaseService
from sqlalchemy import text
import json

def check_report_fields():
    """检查字段管理中定义的字段"""
    session = DatabaseService.get_session()
    
    try:
        print("="*80)
        print("步骤1: 检查字段管理 - AMLO-1-01应该有多少字段？")
        print("="*80)
        
        # 查询AMLO-1-01的所有字段
        sql = text("""
            SELECT 
                id,
                field_name,
                field_cn_name,
                field_en_name,
                field_th_name,
                field_type,
                fill_order,
                is_required,
                field_group
            FROM report_fields
            WHERE report_type = 'AMLO-1-01'
            ORDER BY fill_order
        """)
        
        results = session.execute(sql).fetchall()
        
        print(f"\n[结果] 字段管理中定义了 {len(results)} 个字段")
        print("-"*80)
        
        if len(results) == 0:
            print("[ERROR] 字段管理中没有定义AMLO-1-01的字段！")
            print("[问题] 这就是为什么表单和PDF字段很少的原因")
            return []
        
        print(f"\n字段列表 (按填写顺序):")
        print(f"{'序号':<5} {'字段名':<30} {'中文名':<20} {'泰文名':<30} {'必填'}")
        print("-"*120)
        
        for idx, row in enumerate(results, 1):
            field_name = row[1]
            cn_name = row[2]
            th_name = row[4]
            is_required = '是' if row[7] else '否'
            print(f"{idx:<5} {field_name:<30} {cn_name:<20} {th_name:<30} {is_required}")
        
        print(f"\n[结论] 如果字段管理中有{len(results)}个字段，那么：")
        print(f"  - 预约表单应该显示{len(results)}个输入框")
        print(f"  - 生成的PDF应该有{len(results)}个数据字段（红色）")
        
        return results
        
    finally:
        DatabaseService.close_session(session)

def check_form_generation():
    """检查表单生成逻辑"""
    
    print("\n" + "="*80)
    print("步骤2: 检查表单生成 - 动态表单是否使用了所有字段？")
    print("="*80)
    
    print("\n[检查] 表单生成逻辑位置:")
    print("  - 前端组件: src/components/amlo/DynamicForm/DynamicForm.vue")
    print("  - API接口: /api/repform/form-definition?report_type=AMLO-1-01")
    
    print("\n[检查] 表单生成流程:")
    print("  1. 前端请求表单定义")
    print("  2. 后端从report_fields表查询AMLO-1-01的所有字段")
    print("  3. 按fill_order排序返回字段列表")
    print("  4. 前端根据字段列表动态生成输入框")
    print("  5. 用户填写表单")
    print("  6. 提交时将数据保存到Reserved_Transaction.form_data (JSON)")

def check_pdf_generation(field_count):
    """检查PDF生成逻辑"""
    
    print("\n" + "="*80)
    print("步骤3: 检查PDF生成 - PDF是否使用了表单的所有数据？")
    print("="*80)
    
    print("\n[检查] PDF生成器位置:")
    print("  - src/services/pdf/amlo_pdf_generator.py")
    print("  - src/services/pdf/amlo_101_final.py")
    
    print("\n[问题检查] PDF生成器可能的问题:")
    print(f"\n问题1: PDF生成器是否只硬编码了部分字段？")
    print(f"  - 字段管理定义: {field_count} 个字段")
    print(f"  - PDF生成器使用: ??? 个字段")
    print(f"  - [需要检查] PDF生成器代码中有多少个data.get('xxx')调用")
    
    print(f"\n问题2: PDF生成器是否使用form_data？")
    print(f"  - Reserved_Transaction.form_data 包含所有表单输入")
    print(f"  - PDF生成时是否读取了完整的form_data？")
    print(f"  - 还是只使用了部分固定字段？")
    
    print(f"\n问题3: PDF布局是否硬编码？")
    print(f"  - 样本PDF有固定的表格布局")
    print(f"  - 当前生成器是否按样本布局绘制？")
    print(f"  - 还是用简单的列表形式？")

def check_data_flow():
    """检查数据流转"""
    session = DatabaseService.get_session()
    
    try:
        print("\n" + "="*80)
        print("步骤4: 检查数据流转 - 实际数据是否完整？")
        print("="*80)
        
        # 查询一条实际的预约记录
        sql = text("""
            SELECT 
                id,
                customer_name,
                report_type,
                form_data,
                created_at
            FROM Reserved_Transaction
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        result = session.execute(sql).fetchone()
        
        if result:
            print(f"\n[检查] 最近的预约记录:")
            print(f"  ID: {result[0]}")
            print(f"  客户: {result[1]}")
            print(f"  报告类型: {result[2]}")
            print(f"  创建时间: {result[4]}")
            
            # 解析form_data
            if result[3]:
                form_data = json.loads(result[3])
                print(f"\n  form_data 中的字段数量: {len(form_data)}")
                print(f"\n  form_data 包含的字段:")
                for key, value in form_data.items():
                    print(f"    - {key}: {value[:50] if isinstance(value, str) and len(value) > 50 else value}")
                
                print(f"\n[问题] form_data只有{len(form_data)}个字段")
                print(f"  这说明预约表单在提交时就只收集了这些字段")
                print(f"  而不是字段管理中定义的所有字段")
            else:
                print(f"\n  [WARN] form_data 为空")
        else:
            print(f"\n[INFO] 没有找到预约记录")
        
        # 查询对应的AMLO报告
        sql = text("""
            SELECT 
                id,
                report_no,
                pdf_filename
            FROM AMLOReport
            ORDER BY created_at DESC
            LIMIT 1
        """)
        
        result = session.execute(sql).fetchone()
        
        if result:
            print(f"\n[检查] 最近的AMLO报告:")
            print(f"  ID: {result[0]}")
            print(f"  报告号: {result[1]}")
            print(f"  PDF文件: {result[2]}")
            
            print(f"\n[问题] PDF生成时使用的数据来源:")
            print(f"  1. 从Reserved_Transaction读取form_data？")
            print(f"  2. 从其他表读取固定字段？")
            print(f"  3. 只使用了部分字段？")
        
    finally:
        DatabaseService.close_session(session)

def main():
    print("\n" + "="*80)
    print("AMLO字段链条完整性检查")
    print("="*80)
    print("目标: 找出为什么表单和PDF字段这么少\n")
    
    # 步骤1: 检查字段定义
    fields = check_report_fields()
    
    # 步骤2: 检查表单生成
    check_form_generation()
    
    # 步骤3: 检查PDF生成
    check_pdf_generation(len(fields))
    
    # 步骤4: 检查数据流转
    check_data_flow()
    
    # 总结
    print("\n" + "="*80)
    print("问题分析总结")
    print("="*80)
    
    print(f"\n可能的问题点:")
    print(f"\n1. 字段管理中字段定义不完整")
    print(f"   - 应该有70-80个字段")
    print(f"   - 实际定义了{len(fields)}个字段")
    print(f"   - [需要] 补充完整的字段定义")
    
    print(f"\n2. 表单生成只使用了部分字段")
    print(f"   - API返回了所有字段，但前端只显示了部分")
    print(f"   - 或者表单硬编码了固定字段")
    print(f"   - [需要] 检查DynamicForm组件")
    
    print(f"\n3. PDF生成器硬编码了字段")
    print(f"   - PDF生成器没有读取form_data的所有字段")
    print(f"   - 只使用了10-15个固定字段")
    print(f"   - [需要] PDF生成器应该遍历form_data的所有字段")
    
    print(f"\n4. PDF布局不匹配样本")
    print(f"   - 样本PDF有固定的表格结构")
    print(f"   - 当前生成器使用简单列表布局")
    print(f"   - [需要] 使用样本PDF作为背景模板")
    
    print(f"\n" + "="*80)
    print("建议的修复方案")
    print("="*80)
    
    if len(fields) < 50:
        print(f"\n[优先] 首先补充字段定义到70-80个")
        print(f"  当前只有{len(fields)}个，远少于样本PDF的要求")
    
    print(f"\n[然后] 实现方案B（PDF背景叠加）")
    print(f"  使用样本PDF作为模板，精确填充数据")

if __name__ == "__main__":
    main()

