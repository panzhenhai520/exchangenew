#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""清理测试数据"""

import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.db_service import DatabaseService
from sqlalchemy import text

session = DatabaseService.get_session()

try:
    # 删除今天的AMLO报告
    result1 = session.execute(text("DELETE FROM AMLOReport WHERE DATE(created_at) = CURDATE()"))
    print(f"[OK] 删除AMLO报告: {result1.rowcount} 条")
    
    # 删除今天的预约记录
    result2 = session.execute(text("DELETE FROM Reserved_Transaction WHERE DATE(created_at) = CURDATE()"))
    print(f"[OK] 删除预约记录: {result2.rowcount} 条")
    
    # 删除今天的BOT记录
    result3 = session.execute(text("DELETE FROM BOT_BuyFX WHERE DATE(created_at) = CURDATE()"))
    print(f"[OK] 删除BOT记录: {result3.rowcount} 条")
    
    session.commit()
    print("\n[OK] 清理完成！可以重新运行测试")
    
except Exception as e:
    session.rollback()
    print(f"[ERROR] 清理失败: {e}")
finally:
    DatabaseService.close_session(session)

