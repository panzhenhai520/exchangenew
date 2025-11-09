from decimal import Decimal
from datetime import datetime
from sqlalchemy.orm import Session
from models.exchange_models import CurrencyBalance, ExchangeTransaction, Currency, Operator, Branch
from typing import Tuple
from utils.transaction_utils import generate_unified_transaction_no
import logging

# 获取模块的日志记录器
logger = logging.getLogger(__name__)
# 设置日志级别为INFO，确保调试信息可见
logger.setLevel(logging.INFO)

class BalanceService:
    @staticmethod
    def update_currency_balance(
        session: Session,
        currency_id: int,
        branch_id: int,
        amount: Decimal,
        lock_for_update: bool = True,
        allow_negative: bool = False
    ) -> Tuple[Decimal, Decimal]:
        """
        更新货币余额，带并发控制
        :param session: 数据库会话
        :param currency_id: 货币ID
        :param branch_id: 分行ID
        :param amount: 变动金额
        :param lock_for_update: 是否使用行锁
        :param allow_negative: 是否允许余额为负数（用于冲正等特殊操作）
        :return: (调节前余额, 调节后余额)
        """
        try:
            logger.info(f"开始更新余额 - 币种ID: {currency_id}, 分行ID: {branch_id}, 变动金额: {amount}")
            
            # 查询余额记录并加行锁
            query = session.query(CurrencyBalance).filter(
                CurrencyBalance.currency_id == currency_id,
                CurrencyBalance.branch_id == branch_id
            )
            
            if lock_for_update:
                query = query.with_for_update()
                logger.info("已添加行锁")
                
            balance_record = query.first()
            logger.info(f"【调试】查询到的余额记录: ID={balance_record.id if balance_record else 'None'}, 余额={balance_record.balance if balance_record else 'None'}")
            logger.info(f"【调试】查询条件: currency_id={currency_id}, branch_id={branch_id}")
            
            # 检查所有THB余额记录
            all_thb_records = session.query(CurrencyBalance).filter(
                CurrencyBalance.currency_id == currency_id
            ).all()
            logger.info(f"【调试】所有THB余额记录数量: {len(all_thb_records)}")
            for record in all_thb_records:
                logger.info(f"【调试】THB记录: ID={record.id}, branch_id={record.branch_id}, balance={record.balance}")
            
            if not balance_record:
                logger.info(f"未找到余额记录，创建新记录 - 币种ID: {currency_id}, 分行ID: {branch_id}")
                # 自动创建余额记录，初始余额为0
                balance_record = CurrencyBalance(
                    currency_id=currency_id,
                    branch_id=branch_id,
                    balance=0,
                    updated_at=datetime.now()
                )
                session.add(balance_record)
                session.flush()  # 确保记录被保存并获得ID
                logger.info(f"已创建新余额记录 - 币种ID: {currency_id}, 分行ID: {branch_id}, 初始余额: 0")
            
            # 记录调节前余额
            balance_before = Decimal(str(balance_record.balance))
            logger.info(f"当前余额: {balance_before}")
            
            # 计算新余额
            new_balance = balance_before + amount
            logger.info(f"计算得到新余额: {new_balance}")
            
            # 检查余额是否会变成负数（如果是支出且不允许负余额）
            if not allow_negative and amount < 0 and new_balance < 0:
                logger.error(f"余额不足 - 当前余额: {balance_before}, 需要: {abs(amount)}")
                raise ValueError(f"余额不足。当前余额: {balance_before}, 需要: {abs(amount)}")
            elif amount < 0 and new_balance < 0:
                logger.warning(f"余额将为负数 - 当前余额: {balance_before}, 变动: {amount}, 结果: {new_balance}")
            
            # 更新余额 - 使用直接SQL更新，避免ORM缓存问题
            from sqlalchemy import text
            
            # 【调试】检查数据类型
            logger.info(f"【调试】SQL更新参数:")
            logger.info(f"  - new_balance: {new_balance} (类型: {type(new_balance)})")
            logger.info(f"  - currency_id: {currency_id} (类型: {type(currency_id)})")
            logger.info(f"  - branch_id: {branch_id} (类型: {type(branch_id)})")
            
            # 先查询当前余额
            select_sql = text("""
                SELECT balance FROM currency_balances 
                WHERE currency_id = :currency_id AND branch_id = :branch_id
            """)
            
            current_result = session.execute(select_sql, {
                'currency_id': currency_id,
                'branch_id': branch_id
            }).fetchone()
            
            if current_result:
                logger.info(f"【调试】SQL查询当前余额: {current_result[0]}")
            
            # 执行更新
            update_sql = text("""
                UPDATE currency_balances 
                SET balance = :new_balance, updated_at = :updated_at 
                WHERE currency_id = :currency_id AND branch_id = :branch_id
            """)
            
            result = session.execute(update_sql, {
                'new_balance': str(new_balance),  # 【修复】使用字符串格式，避免精度问题
                'updated_at': datetime.now(),
                'currency_id': currency_id,
                'branch_id': branch_id
            })
            
            # 强制刷新会话
            session.flush()
            
            logger.info(f"已更新余额记录 - 调节前: {balance_before}, 调节后: {new_balance}")
            logger.info(f"【调试】SQL更新结果: 影响行数={result.rowcount}")
            
            # 重新查询余额记录以验证更新
            updated_result = session.execute(select_sql, {
                'currency_id': currency_id,
                'branch_id': branch_id
            }).fetchone()
            
            if updated_result:
                logger.info(f"【调试】SQL查询更新后余额: {updated_result[0]}")
            else:
                logger.error(f"【调试】SQL查询更新后找不到余额记录")
            
            return balance_before, new_balance
            
        except ValueError as e:
            logger.error(f"余额更新出现ValueError: {str(e)}")
            raise ValueError(str(e))
        except Exception as e:
            logger.error(f"余额更新出现异常: {str(e)}", exc_info=True)
            raise ValueError(f"更新余额失败: {str(e)}")

    @staticmethod
    def create_exchange_transaction(
        session: Session,
        branch_id: int,
        currency_id: int,
        transaction_type: str,
        amount: Decimal,
        rate: Decimal,
        local_amount: Decimal,
        customer_name: str,
        customer_id: str,
        operator_id: int,
        balance_before: Decimal,
        balance_after: Decimal,
        purpose: str = '',
        remarks: str = ''
    ) -> ExchangeTransaction:
        """
        创建兑换交易记录
        """
        try:
            logger.info(f"开始创建交易记录 - 类型: {transaction_type}, 币种ID: {currency_id}, 金额: {amount}")
            logger.info(f"余额信息 - 调节前: {balance_before}, 调节后: {balance_after}")
            
            # 确保金额都转换为字符串格式
            str_balance_before = str(balance_before) if balance_before is not None else None
            str_balance_after = str(balance_after) if balance_after is not None else None
            
            # 使用统一的单据号生成服务
            if transaction_type in ['ADJUSTMENT', 'adjustment']:
                transaction_no = generate_unified_transaction_no(branch_id, 'ADJUSTMENT', session)
            elif transaction_type in ['INITIAL', 'initial']:
                transaction_no = generate_unified_transaction_no(branch_id, 'INITIAL', session)
            else:
                transaction_no = generate_unified_transaction_no(branch_id, 'EXCHANGE', session)
            
            logger.info(f"生成统一格式单据号: {transaction_no} (类型: {transaction_type})")
            
            transaction = ExchangeTransaction(
                branch_id=branch_id,
                currency_id=currency_id,
                type=transaction_type,
                amount=str(amount),
                rate=str(rate),
                local_amount=str(local_amount),
                customer_name=customer_name,
                customer_id=customer_id,
                operator_id=operator_id,
                transaction_date=datetime.now().date(),
                transaction_time=datetime.now().strftime('%H:%M:%S'),
                transaction_no=transaction_no,
                created_at=datetime.now(),
                balance_before=str_balance_before,
                balance_after=str_balance_after,
                # 新增字段
                purpose=purpose or '',
                remarks=remarks or '',
                receipt_filename='',  # 暂时为空，后续PDF生成时填入
                print_count=0
            )
            
            session.add(transaction)
            logger.info(f"交易记录已创建 - 交易号: {transaction.transaction_no}, 余额前: {str_balance_before}, 余额后: {str_balance_after}")
            logger.info(f"交易记录附加信息 - 用途: {purpose}, 备注: {remarks}")
            return transaction
            
        except Exception as e:
            logger.error(f"创建交易记录失败: {str(e)}", exc_info=True)
            raise ValueError(f"创建交易记录失败: {str(e)}")
    
    @staticmethod
    def generate_adjustment_receipt(transaction, session, reprint_time=None, language='zh'):
        """
        生成余额调节收据
        
        Args:
            transaction: 交易记录对象
            session: 数据库会话
            reprint_time: 重新打印时间（可选）
            language: 语言代码 ('zh', 'en', 'th')
            
        Returns:
            str: PDF文件的base64编码内容
        """
        try:
            from services.simple_pdf_service import SimplePDFService
            return SimplePDFService.generate_balance_receipt(
                transaction, session, 'adjustment', reprint_time, language
            )
                
        except Exception as e:
            logger.error(f"生成余额调节收据失败: {e}")
            raise
    
    @staticmethod
    def generate_initial_balance_receipt(transaction, session, reprint_time=None, language='zh'):
        """
        生成余额初始化收据
        
        Args:
            transaction: 交易记录对象
            session: 数据库会话
            reprint_time: 重新打印时间（可选）
            language: 语言代码 ('zh', 'en', 'th')
            
        Returns:
            str: PDF文件的base64编码内容
        """
        try:
            from services.simple_pdf_service import SimplePDFService
            return SimplePDFService.generate_balance_receipt(
                transaction, session, 'initial', reprint_time, language
            )
                
        except Exception as e:
            logger.error(f"生成余额初始化收据失败: {e}")
            raise 