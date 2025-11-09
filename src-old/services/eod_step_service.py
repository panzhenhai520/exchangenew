"""
日结步骤服务
"""

from services.db_service import DatabaseService
from services.log_service import LogService

class EODStepService:
    @staticmethod
    def cancel_complete_eod(eod_id, reason, operator_id):
        """完全取消日结"""
        try:
            return {'success': True, 'message': '取消成功'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
    
    @staticmethod
    def rollback_step(eod_id, step_number, operator_id):
        """回滚指定步骤"""
        try:
            return {'success': True, 'message': '回滚成功'}
        except Exception as e:
            return {'success': False, 'message': str(e)}
