#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本：为币种模板表添加自定义图标字段
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from services.db_service import get_db_url

def migrate():
    """执行数据库迁移"""
    db_url = get_db_url()
    engine = create_engine(db_url)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # 检查字段是否已存在
        result = session.execute(text("""
            SELECT COUNT(*) 
            FROM information_schema.columns 
            WHERE table_name = 'currency_templates' 
            AND column_name = 'custom_flag_filename'
        """))
        
        if result.scalar() == 0:
            # 添加自定义图标字段
            session.execute(text("""
                ALTER TABLE currency_templates 
                ADD COLUMN custom_flag_filename VARCHAR(255)
            """))
            
            session.commit()
            print("✅ 成功添加 custom_flag_filename 字段到 currency_templates 表")
        else:
            print("ℹ️  custom_flag_filename 字段已存在，跳过迁移")
            
    except Exception as e:
        session.rollback()
        print(f"❌ 迁移失败: {str(e)}")
        raise
    finally:
        session.close()

if __name__ == "__main__":
    print("开始执行数据库迁移：添加自定义图标字段...")
    migrate()
    print("迁移完成！") 