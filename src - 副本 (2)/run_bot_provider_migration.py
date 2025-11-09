#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
添加BOT_Provider合规配置
包括：触发规则和字段定义
"""

from services.db_service import DatabaseService
from datetime import datetime
import json

def main():
    print("=" * 80)
    print("BOT_Provider Compliance Configuration")
    print("=" * 80)
    
    db = DatabaseService()
    session = db.get_session()
    
    try:
        # 1. 添加BOT_Provider触发规则
        print("\n[1] Adding BOT_Provider trigger rule...")
        
        rule_expression = {
            "logic": "AND",
            "conditions": [
                {
                    "field": "adjustment_type",
                    "operator": "=",
                    "value": "increase"
                },
                {
                    "field": "usd_equivalent",
                    "operator": ">",
                    "value": 20000
                }
            ]
        }
        
        # 检查规则是否已存在
        result = session.execute("""
            SELECT id FROM trigger_rules WHERE report_type = 'BOT_Provider'
        """)
        existing_rule = result.fetchone()
        
        if not existing_rule:
            insert_rule_sql = """
                INSERT INTO trigger_rules (
                    rule_name, rule_name_en, rule_name_th,
                    report_type, rule_expression,
                    description_cn, description_en, description_th,
                    priority, allow_continue,
                    warning_message_cn, warning_message_en, warning_message_th,
                    is_active, created_at, updated_at
                ) VALUES (
                    :rule_name, :rule_name_en, :rule_name_th,
                    :report_type, :rule_expression,
                    :description_cn, :description_en, :description_th,
                    :priority, :allow_continue,
                    :warning_message_cn, :warning_message_en, :warning_message_th,
                    :is_active, :created_at, :updated_at
                )
            """
            
            session.execute(insert_rule_sql, {
                'rule_name': 'BOT-Provider-余额调节>2万USD',
                'rule_name_en': 'BOT-Provider-Balance Adjustment >20K USD',
                'rule_name_th': 'BOT-Provider-การปรับยอด >20K USD',
                'report_type': 'BOT_Provider',
                'rule_expression': json.dumps(rule_expression),
                'description_cn': '网点增加外币余额 > 2万美元等值时触发',
                'description_en': 'Triggered when branch increases foreign currency balance > 20K USD equivalent',
                'description_th': 'เมื่อสาขาเพิ่มยอดเงินตราต่างประเทศ > 20K USD',
                'priority': 100,
                'allow_continue': True,
                'warning_message_cn': '此次余额调节需要生成BOT Provider报告',
                'warning_message_en': 'This balance adjustment requires BOT Provider report',
                'warning_message_th': 'การปรับยอดนี้ต้องทำรายงาน BOT Provider',
                'is_active': True,
                'created_at': datetime.now(),
                'updated_at': datetime.now()
            })
            session.commit()
            print("   [OK] Trigger rule added successfully")
        else:
            print("   [SKIP] Trigger rule already exists")
        
        # 2. 添加BOT_Provider字段定义
        print("\n[2] Adding BOT_Provider field definitions...")
        
        # 参考 Re/BOT( Save Excel, PDF, Bot).xlsx - Provider Info工作表
        fields = [
            {
                'field_name': 'institution_code',
                'field_cn_name': '机构代码',
                'field_en_name': 'Institution Code',
                'field_th_name': 'รหัสสถาบัน',
                'field_type': 'VARCHAR',
                'field_length': 50,
                'is_required': True,
                'field_group': 'Provider Information',
                'field_group_cn': '提供方信息',
                'field_group_en': 'Provider Information',
                'field_group_th': 'ข้อมูลผู้ให้บริการ',
                'fill_order': 1,
                'placeholder_cn': '请输入机构代码',
                'placeholder_en': 'Enter institution code',
                'placeholder_th': 'กรอกรหัสสถาบัน'
            },
            {
                'field_name': 'licensee_name',
                'field_cn_name': '授权机构名称',
                'field_en_name': 'Licensee Name',
                'field_th_name': 'ชื่อบุคคลรับอนุญาต',
                'field_type': 'VARCHAR',
                'field_length': 200,
                'is_required': True,
                'field_group': 'Provider Information',
                'field_group_cn': '提供方信息',
                'field_group_en': 'Provider Information',
                'field_group_th': 'ข้อมูลผู้ให้บริการ',
                'fill_order': 2,
                'placeholder_cn': '请输入授权机构名称',
                'placeholder_en': 'Enter licensee name',
                'placeholder_th': 'กรอกชื่อบุคคลรับอนุญาต'
            },
            {
                'field_name': 'license_no',
                'field_cn_name': '许可证号',
                'field_en_name': 'License Number',
                'field_th_name': 'License No',
                'field_type': 'VARCHAR',
                'field_length': 50,
                'is_required': True,
                'field_group': 'Provider Information',
                'field_group_cn': '提供方信息',
                'field_group_en': 'Provider Information',
                'field_group_th': 'ข้อมูลผู้ให้บริการ',
                'fill_order': 3,
                'placeholder_cn': '请输入许可证号',
                'placeholder_en': 'Enter license number',
                'placeholder_th': 'กรอก License No'
            },
            {
                'field_name': 'business_name',
                'field_cn_name': '营业场所名称',
                'field_en_name': 'Business Name',
                'field_th_name': 'ชื่อสถานประกอบการ',
                'field_type': 'VARCHAR',
                'field_length': 200,
                'is_required': True,
                'field_group': 'Provider Information',
                'field_group_cn': '提供方信息',
                'field_group_en': 'Provider Information',
                'field_group_th': 'ข้อมูลผู้ให้บริการ',
                'fill_order': 4,
                'placeholder_cn': '请输入营业场所名称',
                'placeholder_en': 'Enter business name',
                'placeholder_th': 'กรอกชื่อสถานประกอบการ'
            },
            {
                'field_name': 'business_code',
                'field_cn_name': '营业场所代码',
                'field_en_name': 'Business Code',
                'field_th_name': 'รหัสพื้นที่ของสถานประกอบการ',
                'field_type': 'VARCHAR',
                'field_length': 50,
                'is_required': True,
                'field_group': 'Provider Information',
                'field_group_cn': '提供方信息',
                'field_group_en': 'Provider Information',
                'field_group_th': 'ข้อมูลผู้ให้บริการ',
                'fill_order': 5,
                'placeholder_cn': '请输入营业场所代码',
                'placeholder_en': 'Enter business code',
                'placeholder_th': 'กรอกรหัสพื้นที่ของสถานประกอบการ'
            },
            {
                'field_name': 'report_month',
                'field_cn_name': '报告月份',
                'field_en_name': 'Report Month',
                'field_th_name': 'ประจำงวด (เดือน)',
                'field_type': 'ENUM',
                'field_length': 20,
                'is_required': True,
                'field_group': 'Report Period',
                'field_group_cn': '报告期间',
                'field_group_en': 'Report Period',
                'field_group_th': 'งวดรายงาน',
                'fill_order': 6,
                'placeholder_cn': '选择报告月份',
                'placeholder_en': 'Select report month',
                'placeholder_th': 'เลือกประจำงวด (เดือน)'
            },
            {
                'field_name': 'report_year',
                'field_cn_name': '报告年份',
                'field_en_name': 'Report Year',
                'field_th_name': 'ประจำงวด (ปี)',
                'field_type': 'INT',
                'field_length': 4,
                'is_required': True,
                'field_group': 'Report Period',
                'field_group_cn': '报告期间',
                'field_group_en': 'Report Period',
                'field_group_th': 'งวดรายงาน',
                'fill_order': 7,
                'placeholder_cn': '输入报告年份',
                'placeholder_en': 'Enter report year',
                'placeholder_th': 'กรอกประจำงวด (ปี)'
            },
            {
                'field_name': 'data_date',
                'field_cn_name': '数据日期',
                'field_en_name': 'Data Date',
                'field_th_name': 'วันที่ชุดข้อมูล',
                'field_type': 'DATE',
                'field_length': 10,
                'is_required': True,
                'field_group': 'Report Period',
                'field_group_cn': '报告期间',
                'field_group_en': 'Report Period',
                'field_group_th': 'งวดรายงาน',
                'fill_order': 8,
                'placeholder_cn': '选择数据日期',
                'placeholder_en': 'Select data date',
                'placeholder_th': 'เลือกวันที่ชุดข้อมูล'
            },
            {
                'field_name': 'adjustment_currency',
                'field_cn_name': '调节币种',
                'field_en_name': 'Adjustment Currency',
                'field_th_name': 'สกุลเงินที่ปรับ',
                'field_type': 'VARCHAR',
                'field_length': 10,
                'is_required': True,
                'field_group': 'Adjustment Details',
                'field_group_cn': '调节详情',
                'field_group_en': 'Adjustment Details',
                'field_group_th': 'รายละเอียดการปรับยอด',
                'fill_order': 9,
                'placeholder_cn': '币种代码',
                'placeholder_en': 'Currency code',
                'placeholder_th': 'รหัสสกุลเงิน'
            },
            {
                'field_name': 'adjustment_amount',
                'field_cn_name': '调节金额',
                'field_en_name': 'Adjustment Amount',
                'field_th_name': 'จำนวนเงินที่ปรับ',
                'field_type': 'INT',
                'field_length': 15,
                'is_required': True,
                'field_group': 'Adjustment Details',
                'field_group_cn': '调节详情',
                'field_group_en': 'Adjustment Details',
                'field_group_th': 'รายละเอียดการปรับยอด',
                'fill_order': 10,
                'placeholder_cn': '调节金额',
                'placeholder_en': 'Adjustment amount',
                'placeholder_th': 'จำนวนเงินที่ปรับ'
            },
            {
                'field_name': 'adjustment_reason',
                'field_cn_name': '调节原因',
                'field_en_name': 'Adjustment Reason',
                'field_th_name': 'เหตุผลการปรับยอด',
                'field_type': 'TEXT',
                'field_length': 500,
                'is_required': True,
                'field_group': 'Adjustment Details',
                'field_group_cn': '调节详情',
                'field_group_en': 'Adjustment Details',
                'field_group_th': 'รายละเอียดการปรับยอด',
                'fill_order': 11,
                'placeholder_cn': '请说明调节原因',
                'placeholder_en': 'Enter adjustment reason',
                'placeholder_th': 'กรอกเหตุผลการปรับยอด'
            }
        ]
        
        # 检查并插入字段
        added_count = 0
        for field in fields:
            result = session.execute("""
                SELECT id FROM report_fields 
                WHERE report_type = 'BOT_Provider' AND field_name = :field_name
            """, {'field_name': field['field_name']})
            
            existing_field = result.fetchone()
            
            if not existing_field:
                insert_field_sql = """
                    INSERT INTO report_fields (
                        report_type, field_name,
                        field_cn_name, field_en_name, field_th_name,
                        field_type, field_length,
                        is_required, is_active,
                        field_group, field_group_cn, field_group_en, field_group_th,
                        fill_order,
                        placeholder_cn, placeholder_en, placeholder_th,
                        created_at, updated_at
                    ) VALUES (
                        'BOT_Provider', :field_name,
                        :field_cn_name, :field_en_name, :field_th_name,
                        :field_type, :field_length,
                        :is_required, 1,
                        :field_group, :field_group_cn, :field_group_en, :field_group_th,
                        :fill_order,
                        :placeholder_cn, :placeholder_en, :placeholder_th,
                        :created_at, :updated_at
                    )
                """
                
                session.execute(insert_field_sql, {
                    **field,
                    'created_at': datetime.now(),
                    'updated_at': datetime.now()
                })
                added_count += 1
                print(f"   [OK] Field added: {field['field_name']}")
        
        if added_count > 0:
            session.commit()
            print(f"\n   [OK] {added_count} fields added successfully")
        else:
            print("   [SKIP] All fields already exist")
        
        print("\n" + "=" * 80)
        print("Migration completed successfully!")
        print("=" * 80)
        
    except Exception as e:
        session.rollback()
        print(f"\n[ERROR] Migration failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        session.close()
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())

