#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化合规表的多语言数据
"""

from services.db_service import DatabaseService
from sqlalchemy import text
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 字段分组的多语言翻译
FIELD_GROUP_TRANSLATIONS = {
    '表头信息': {
        'cn': '表头信息',
        'en': 'Header Information',
        'th': 'ข้อมูลส่วนหัว'
    },
    '报告类型': {
        'cn': '报告类型',
        'en': 'Report Type',
        'th': 'ประเภทรายงาน'
    },
    'ส่วนที่ ๑ ผู้ทำธุรกรรม': {
        'cn': '交易制作人信息',
        'en': 'Transaction Maker Information',
        'th': 'ส่วนที่ ๑ ผู้ทำธุรกรรม'
    },
    'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม': {
        'cn': '共同交易人信息',
        'en': 'Co-transactor Information',
        'th': 'ส่วนที่ ๒ ผู้ร่วมทำธุรกรรม'
    },
    'ส่วนที่ ๓ ธุรกรรม': {
        'cn': '交易信息',
        'en': 'Transaction Information',
        'th': 'ส่วนที่ ๓ ธุรกรรม'
    },
    'ส่วนที่ ๔ ผู้รายงาน': {
        'cn': '报告人信息',
        'en': 'Reporter Information',
        'th': 'ส่วนที่ ๔ ผู้รายงาน'
    },
    'ส่วนที่ ๔ เหตุสงสัย': {
        'cn': '可疑原因',
        'en': 'Suspicious Reasons',
        'th': 'ส่วนที่ ๔ เหตุสงสัย'
    },
    'ส่วนที่ ๕ ผู้รายงาน': {
        'cn': '报告人信息(第五部分)',
        'en': 'Reporter Information (Part 5)',
        'th': 'ส่วนที่ ๕ ผู้รายงาน'
    },
    'BOT报告': {
        'cn': 'BOT报告',
        'en': 'BOT Report',
        'th': 'รายงาน BOT'
    },
    'BOT交易': {
        'cn': 'BOT交易',
        'en': 'BOT Transaction',
        'th': 'ธุรกรรม BOT'
    },
    'BOT客户': {
        'cn': 'BOT客户',
        'en': 'BOT Customer',
        'th': 'ลูกค้า BOT'
    },
    'BOT货币': {
        'cn': 'BOT货币',
        'en': 'BOT Currency',
        'th': 'สกุลเงิน BOT'
    }
}

# 触发规则名称的多语言翻译
TRIGGER_RULE_TRANSLATIONS = {
    'AMLO-1-01-500万THB': {
        'cn': 'AMLO-1-01-500万THB',
        'en': 'AMLO-1-01-5M THB',
        'th': 'AMLO-1-01-5 ล้านบาท'
    },
    'AMLO-1-02-800万THB': {
        'cn': 'AMLO-1-02-800万THB',
        'en': 'AMLO-1-02-8M THB',
        'th': 'AMLO-1-02-8 ล้านบาท'
    },
    'AMLO-1-03-累计200万+频率': {
        'cn': 'AMLO-1-03-累计200万+频率',
        'en': 'AMLO-1-03-Cumulative 2M + Frequency',
        'th': 'AMLO-1-03-สะสม 2 ล้าน + ความถี่'
    },
    'AMLO-1-03-资金来源': {
        'cn': 'AMLO-1-03-资金来源',
        'en': 'AMLO-1-03-Funding Source',
        'th': 'AMLO-1-03-แหล่งเงินทุน'
    },
    'BOT-BuyFX-2万USD等值': {
        'cn': 'BOT-BuyFX-2万USD等值',
        'en': 'BOT-BuyFX-20K USD Equivalent',
        'th': 'BOT-BuyFX-20K เทียบเท่า USD'
    },
    'BOT-SellFX-2万USD等值': {
        'cn': 'BOT-SellFX-2万USD等值',
        'en': 'BOT-SellFX-20K USD Equivalent',
        'th': 'BOT-SellFX-20K เทียบเท่า USD'
    },
    'BOT-FCD-5万USD': {
        'cn': 'BOT-FCD-5万USD',
        'en': 'BOT-FCD-50K USD',
        'th': 'BOT-FCD-50K USD'
    }
}

def init_field_group_translations():
    """初始化字段分组的多语言翻译"""
    session = DatabaseService.get_session()
    
    try:
        logger.info("Step 1: Initializing field_group translations...")
        
        # 获取所有不同的字段分组
        result = session.execute(text("""
            SELECT DISTINCT field_group_cn
            FROM report_fields
            WHERE field_group_cn IS NOT NULL AND field_group_cn != ''
        """))
        
        existing_groups = [row[0] for row in result]
        logger.info(f"Found {len(existing_groups)} field groups to translate")
        
        update_count = 0
        for group_cn in existing_groups:
            # 查找匹配的翻译
            translation = None
            for key, trans in FIELD_GROUP_TRANSLATIONS.items():
                if trans['cn'] == group_cn or key == group_cn:
                    translation = trans
                    break
            
            if translation:
                # 更新翻译
                update_sql = text("""
                    UPDATE report_fields
                    SET field_group_cn = :cn,
                        field_group_en = :en,
                        field_group_th = :th
                    WHERE field_group_cn = :original
                """)
                
                session.execute(update_sql, {
                    'cn': translation['cn'],
                    'en': translation['en'],
                    'th': translation['th'],
                    'original': group_cn
                })
                
                update_count += 1
                logger.info(f"✅ Updated: {group_cn} -> EN: {translation['en']}, TH: {translation['th']}")
            else:
                logger.warning(f"⚠️ No translation found for: {group_cn}")
        
        session.commit()
        logger.info(f"✅ Updated {update_count} field group translations")
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Failed to initialize field_group translations: {e}")
        raise
    finally:
        session.close()

def init_rule_name_translations():
    """初始化触发规则名称的多语言翻译"""
    session = DatabaseService.get_session()
    
    try:
        logger.info("Step 2: Initializing rule_name translations...")
        
        # 获取所有规则
        result = session.execute(text("""
            SELECT id, rule_name
            FROM trigger_rules
            WHERE rule_name IS NOT NULL AND rule_name != ''
        """))
        
        rules = [(row[0], row[1]) for row in result]
        logger.info(f"Found {len(rules)} trigger rules to translate")
        
        update_count = 0
        for rule_id, rule_name in rules:
            # 查找匹配的翻译
            translation = None
            for key, trans in TRIGGER_RULE_TRANSLATIONS.items():
                if trans['cn'] == rule_name or key == rule_name:
                    translation = trans
                    break
            
            if translation:
                # 更新翻译
                update_sql = text("""
                    UPDATE trigger_rules
                    SET rule_name = :cn,
                        rule_name_en = :en,
                        rule_name_th = :th
                    WHERE id = :id
                """)
                
                session.execute(update_sql, {
                    'cn': translation['cn'],
                    'en': translation['en'],
                    'th': translation['th'],
                    'id': rule_id
                })
                
                update_count += 1
                logger.info(f"✅ Updated: {rule_name} -> EN: {translation['en']}, TH: {translation['th']}")
            else:
                logger.warning(f"⚠️ No translation found for: {rule_name}")
        
        session.commit()
        logger.info(f"✅ Updated {update_count} rule name translations")
        
    except Exception as e:
        session.rollback()
        logger.error(f"❌ Failed to initialize rule_name translations: {e}")
        raise
    finally:
        session.close()

def main():
    """主函数"""
    logger.info("=" * 60)
    logger.info("Starting multilingual data initialization")
    logger.info("=" * 60)
    
    try:
        init_field_group_translations()
        init_rule_name_translations()
        
        logger.info("=" * 60)
        logger.info("✅ All translations initialized successfully!")
        logger.info("=" * 60)
    except Exception as e:
        logger.error(f"❌ Initialization failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

if __name__ == '__main__':
    main()

