from models.exchange_models import OperatorActivityLog, Operator
from services.db_service import DatabaseService
from datetime import datetime, timedelta
from sqlalchemy.orm import joinedload
from sqlalchemy import func, desc

class ActivityService:
    @staticmethod
    def log_activity(operator_id, activity_type, description=None, ip_address=None, user_agent=None, session_id=None, branch_id=None):
        """记录操作员活跃状态"""
        session = DatabaseService.get_session()
        try:
            activity_log = OperatorActivityLog(
                operator_id=operator_id,
                activity_type=activity_type,
                activity_description=description,
                ip_address=ip_address,
                user_agent=user_agent,
                session_id=session_id,
                branch_id=branch_id,
                created_at=datetime.utcnow()
            )
            session.add(activity_log)
            DatabaseService.commit_session(session)
            return True
        except Exception as e:
            DatabaseService.rollback_session(session)
            print(f"Error logging activity: {str(e)}")
            return False
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def get_operator_activities(operator_id, limit=50, activity_type=None, start_date=None, end_date=None):
        """获取操作员活跃记录"""
        session = DatabaseService.get_session()
        try:
            query = session.query(OperatorActivityLog).options(
                joinedload(OperatorActivityLog.operator),
                joinedload(OperatorActivityLog.branch)
            ).filter_by(operator_id=operator_id)
            
            if activity_type:
                query = query.filter(OperatorActivityLog.activity_type == activity_type)
            
            if start_date:
                query = query.filter(OperatorActivityLog.created_at >= start_date)
            
            if end_date:
                query = query.filter(OperatorActivityLog.created_at <= end_date)
            
            activities = query.order_by(desc(OperatorActivityLog.created_at)).limit(limit).all()
            
            result = []
            for activity in activities:
                result.append({
                    'id': activity.id,
                    'activity_type': activity.activity_type,
                    'activity_description': activity.activity_description,
                    'ip_address': activity.ip_address,
                    'user_agent': activity.user_agent,
                    'session_id': activity.session_id,
                    'created_at': activity.created_at.isoformat() if activity.created_at else None,
                    'operator_name': activity.operator.name if activity.operator else None,
                    'branch_name': activity.branch.branch_name if activity.branch else None
                })
            
            return result
        except Exception as e:
            print(f"Error getting operator activities: {str(e)}")
            return []
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def get_activities_summary(branch_id=None, days=7):
        """获取活跃状态统计摘要"""
        session = DatabaseService.get_session()
        try:
            start_date = datetime.utcnow() - timedelta(days=days)
            
            query = session.query(
                OperatorActivityLog.operator_id,
                Operator.name,
                Operator.login_code,
                func.count(OperatorActivityLog.id).label('activity_count'),
                func.max(OperatorActivityLog.created_at).label('last_activity')
            ).join(Operator).filter(
                OperatorActivityLog.created_at >= start_date
            )
            
            if branch_id:
                query = query.filter(OperatorActivityLog.branch_id == branch_id)
            
            results = query.group_by(
                OperatorActivityLog.operator_id,
                Operator.name,
                Operator.login_code
            ).all()
            
            summary = []
            for result in results:
                summary.append({
                    'operator_id': result.operator_id,
                    'operator_name': result.name,
                    'login_code': result.login_code,
                    'activity_count': result.activity_count,
                    'last_activity': result.last_activity.isoformat() if result.last_activity else None
                })
            
            return summary
        except Exception as e:
            print(f"Error getting activities summary: {str(e)}")
            return []
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def get_online_operators(branch_id=None, minutes=30):
        """获取在线操作员列表（基于最近活动时间）"""
        session = DatabaseService.get_session()
        try:
            cutoff_time = datetime.utcnow() - timedelta(minutes=minutes)
            
            query = session.query(
                OperatorActivityLog.operator_id,
                Operator.name,
                Operator.login_code,
                func.max(OperatorActivityLog.created_at).label('last_activity')
            ).join(Operator).filter(
                OperatorActivityLog.created_at >= cutoff_time,
                OperatorActivityLog.activity_type.in_(['login', 'action', 'page_view'])
            )
            
            if branch_id:
                query = query.filter(OperatorActivityLog.branch_id == branch_id)
            
            results = query.group_by(
                OperatorActivityLog.operator_id,
                Operator.name,
                Operator.login_code
            ).all()
            
            online_operators = []
            for result in results:
                online_operators.append({
                    'operator_id': result.operator_id,
                    'operator_name': result.name,
                    'login_code': result.login_code,
                    'last_activity': result.last_activity.isoformat() if result.last_activity else None
                })
            
            return online_operators
        except Exception as e:
            print(f"Error getting online operators: {str(e)}")
            return []
        finally:
            DatabaseService.close_session(session)
    
    @staticmethod
    def cleanup_old_activities(days=90):
        """清理旧的活动记录"""
        session = DatabaseService.get_session()
        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days)
            deleted_count = session.query(OperatorActivityLog).filter(
                OperatorActivityLog.created_at < cutoff_date
            ).delete()
            DatabaseService.commit_session(session)
            return deleted_count
        except Exception as e:
            DatabaseService.rollback_session(session)
            print(f"Error cleaning up old activities: {str(e)}")
            return 0
        finally:
            DatabaseService.close_session(session) 