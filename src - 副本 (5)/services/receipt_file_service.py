"""
票据文件管理服务
处理票据文件的浏览、预览和打印记录功能
"""

import os
import logging
from datetime import datetime
from typing import List, Dict, Optional, Any
from pathlib import Path

from services.db_service import DatabaseService
from models.exchange_models import ExchangeTransaction, SystemLog, Operator

logger = logging.getLogger(__name__)

class ReceiptFileService:
    """票据文件管理服务类"""
    
    # 票据文件存储根目录
    RECEIPTS_ROOT = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'receipts')
    
    @staticmethod
    def get_available_years() -> List[str]:
        """获取可用的年份列表"""
        try:
            if not os.path.exists(ReceiptFileService.RECEIPTS_ROOT):
                return []
            
            years = []
            for item in os.listdir(ReceiptFileService.RECEIPTS_ROOT):
                year_path = os.path.join(ReceiptFileService.RECEIPTS_ROOT, item)
                if os.path.isdir(year_path) and item.isdigit() and len(item) == 4:
                    years.append(item)
            
            return sorted(years, reverse=True)  # 最新年份在前
        except Exception as e:
            logger.error(f"获取年份列表失败: {e}")
            return []
    
    @staticmethod
    def get_available_months(year: str) -> List[str]:
        """获取指定年份的可用月份列表"""
        try:
            year_path = os.path.join(ReceiptFileService.RECEIPTS_ROOT, year)
            if not os.path.exists(year_path):
                return []
            
            months = []
            for item in os.listdir(year_path):
                month_path = os.path.join(year_path, item)
                if os.path.isdir(month_path) and item.isdigit() and 1 <= int(item) <= 12:
                    months.append(item.zfill(2))  # 确保两位数格式
            
            return sorted(months, reverse=True)  # 最新月份在前
        except Exception as e:
            logger.error(f"获取月份列表失败: {e}")
            return []
    
    @staticmethod
    def get_receipt_files(year: str, month: str, branch_id: Optional[int] = None) -> List[Dict[str, Any]]:
        """获取指定年月的票据文件列表"""
        try:
            month_path = os.path.join(ReceiptFileService.RECEIPTS_ROOT, year, month.zfill(2))
            if not os.path.exists(month_path):
                return []
            
            files = []
            for filename in os.listdir(month_path):
                file_path = os.path.join(month_path, filename)
                if os.path.isfile(file_path) and filename.lower().endswith('.pdf'):
                    # 获取文件信息
                    stat = os.stat(file_path)
                    file_info = {
                        'filename': filename,
                        'relative_path': f'/receipts/{year}/{month.zfill(2)}/{filename}',
                        'size': stat.st_size,
                        'created_time': datetime.fromtimestamp(stat.st_ctime).isoformat(),
                        'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                        'print_count': 0  # 默认值，后续从数据库获取
                    }
                    
                    # 尝试从文件名解析交易信息
                    transaction_info = ReceiptFileService._parse_filename(filename)
                    if transaction_info:
                        file_info.update(transaction_info)
                    
                    files.append(file_info)
            
            # 按修改时间降序排列
            files.sort(key=lambda x: x['modified_time'], reverse=True)
            
            # 获取打印次数信息
            ReceiptFileService._update_print_counts(files)
            
            return files
        except Exception as e:
            logger.error(f"获取票据文件列表失败: {e}")
            return []
    
    @staticmethod
    def _parse_filename(filename: str) -> Optional[Dict[str, Any]]:
        """解析票据文件名获取交易信息"""
        try:
            # 文件名格式通常为：A005202506240041.pdf
            # A005: 网点代码，20250624: 日期，0041: 流水号
            name_without_ext = filename.replace('.pdf', '').replace('.PDF', '')
            
            if len(name_without_ext) >= 16:
                # 提取可能的交易编号
                transaction_no = name_without_ext
                
                # 尝试从数据库查找对应的交易记录
                session = DatabaseService.get_session()
                try:
                    transaction = session.query(ExchangeTransaction).filter(
                        ExchangeTransaction.receipt_filename == filename
                    ).first()
                    
                    if transaction:
                        return {
                            'transaction_no': transaction.transaction_no,
                            'customer_name': transaction.customer_name,
                            'amount': float(transaction.amount) if transaction.amount else 0,
                            'currency_id': transaction.currency_id,
                            'transaction_date': transaction.transaction_date.isoformat() if transaction.transaction_date else None,
                            'print_count': transaction.print_count or 0
                        }
                finally:
                    DatabaseService.close_session(session)
            
            return None
        except Exception as e:
            logger.error(f"解析文件名失败 {filename}: {e}")
            return None
    
    @staticmethod
    def _update_print_counts(files: List[Dict[str, Any]]) -> None:
        """更新文件的打印次数信息"""
        try:
            session = DatabaseService.get_session()
            try:
                for file_info in files:
                    if 'transaction_no' in file_info:
                        transaction = session.query(ExchangeTransaction).filter(
                            ExchangeTransaction.receipt_filename == file_info['filename']
                        ).first()
                        
                        if transaction:
                            file_info['print_count'] = transaction.print_count or 0
            finally:
                DatabaseService.close_session(session)
        except Exception as e:
            logger.error(f"更新打印次数失败: {e}")
    
    @staticmethod
    def record_print_action(filename: str, operator_id: int) -> bool:
        """记录票据打印操作"""
        try:
            session = DatabaseService.get_session()
            try:
                # 查找对应的交易记录
                transaction = session.query(ExchangeTransaction).filter(
                    ExchangeTransaction.receipt_filename == filename
                ).first()
                
                if transaction:
                    # 更新打印次数
                    if transaction.print_count is None:
                        transaction.print_count = 1
                    else:
                        transaction.print_count += 1
                    
                    DatabaseService.commit_session(session)
                
                # 记录系统日志
                log_entry = SystemLog(
                    operation='票据打印',
                    operator_id=operator_id,
                    log_type='print',
                    action=f'打印票据文件: {filename}',
                    details=f'文件路径: {filename}, 打印次数: {transaction.print_count if transaction else "未知"}'
                )
                session.add(log_entry)
                DatabaseService.commit_session(session)
                
                return True
            except Exception as e:
                DatabaseService.rollback_session(session)
                raise e
            finally:
                DatabaseService.close_session(session)
        except Exception as e:
            logger.error(f"记录打印操作失败: {e}")
            return False
    
    @staticmethod
    def get_file_url(relative_path: str) -> str:
        """获取文件的访问URL"""
        # 将相对路径转换为Web可访问的URL
        # 例如：/receipts/2025/06/A005202506240041.pdf -> /static/receipts/2025/06/A005202506240041.pdf
        if relative_path.startswith('/receipts/'):
            return f"/static{relative_path}"
        return relative_path
    
    @staticmethod
    def check_file_exists(relative_path: str) -> bool:
        """检查文件是否存在"""
        try:
            # 移除开头的斜杠和receipts前缀
            clean_path = relative_path.lstrip('/').replace('receipts/', '')
            full_path = os.path.join(ReceiptFileService.RECEIPTS_ROOT, clean_path)
            return os.path.isfile(full_path)
        except Exception as e:
            logger.error(f"检查文件存在性失败: {e}")
            return False 