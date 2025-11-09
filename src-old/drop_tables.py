#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
sys.path.append('.')

from services.db_service import DatabaseService
from sqlalchemy import text

def drop_tables():
    session = DatabaseService.get_session()
    
    try:
        session.execute(text('DROP TABLE IF EXISTS amlo_report_sequences'))
        session.execute(text('DROP TABLE IF EXISTS bot_report_sequences'))
        session.execute(text('DROP TABLE IF EXISTS report_number_logs'))
        session.commit()
        print('Old tables dropped successfully')
        
    except Exception as e:
        session.rollback()
        print(f'Error: {e}')
        raise e
    finally:
        session.close()

if __name__ == '__main__':
    drop_tables()





