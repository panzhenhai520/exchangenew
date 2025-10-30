# 交易拆分服务 - 支持双向交易自动拆分逻辑
from datetime import datetime
from decimal import Decimal
from typing import List, Dict, Any, Optional
import uuid
import json
from services.db_service import DatabaseService
from services.receipt_service import ReceiptService
from models.exchange_models import ExchangeTransaction, CurrencyBalance, Currency
from sqlalchemy import text
import logging
from utils.backend_i18n import t

logger = logging.getLogger(__name__)

class TransactionSplitService:
    """交易拆分服务，用于将复杂的双向交易拆分为符合原始数据结构的多条记录"""

    @staticmethod
    def generate_business_group_id() -> str:
        """生成业务组ID"""
        return f"BG{datetime.now().strftime('%Y%m%d%H%M%S')}{str(uuid.uuid4())[:8].upper()}"

    @staticmethod
    def analyze_denomination_combinations(denomination_data: Dict[str, Any], base_currency_id: int, exchange_mode: str = None) -> List[Dict[str, Any]]:
        """
        分析面值组合数据，按币种+方向分组

        Args:
            denomination_data: 面值组合数据
            base_currency_id: 本币ID
            exchange_mode: 交易方向模式 ('buy_foreign' 或 'sell_foreign')

        Returns:
            List of transaction groups
        """
        logger.info(f"[TransactionSplitService] analyze_denomination_combinations 收到数据:")
        logger.info(f"[TransactionSplitService] denomination_data type: {type(denomination_data)}")
        logger.info(f"[TransactionSplitService] denomination_data content: {denomination_data}")
        logger.info(f"[TransactionSplitService] exchange_mode: {exchange_mode}")

        if not denomination_data or not denomination_data.get('combinations'):
            logger.warning(f"[TransactionSplitService] denomination_data 为空或没有 combinations 字段")
            return []

        # 🔧 修复：根据exchange_mode转换为direction
        # 前端使用客户视角：
        #   exchange_mode='buy_foreign' = 客户买入外币 → direction='sell' (网点卖出外币)
        #   exchange_mode='sell_foreign' = 客户卖出外币 → direction='buy' (网点买入外币)
        if exchange_mode:
            if exchange_mode == 'buy_foreign':
                global_direction = 'sell'  # 客户买入外币 = 网点卖出外币
            elif exchange_mode == 'sell_foreign':
                global_direction = 'buy'  # 客户卖出外币 = 网点买入外币
            else:
                global_direction = 'sell'  # 默认值
        else:
            global_direction = 'sell'  # 兼容旧代码的默认值

        logger.info(f"[TransactionSplitService] 转换后的direction: {global_direction}")

        # 按币种+方向分组
        groups = {}

        for item in denomination_data['combinations']:
            currency_id = item.get('currency_id', denomination_data.get('currency_id'))

            # 🔧 修复：优先使用全局方向（从exchange_mode转换而来），忽略item自带的direction
            # 因为item的direction可能是客户视角，而global_direction是正确的网点视角
            direction = global_direction or item.get('direction', 'sell')

            # 创建分组键
            group_key = f"{currency_id}_{direction}"

            if group_key not in groups:
                groups[group_key] = {
                    'currency_id': currency_id,
                    'direction': direction,
                    'items': [],
                    'total_amount': Decimal('0'),
                    'base_currency_id': base_currency_id
                }

            groups[group_key]['items'].append(item)
            groups[group_key]['total_amount'] += Decimal(str(item.get('subtotal', 0)))

        logger.info(f"[TransactionSplitService] 分组结果: {len(groups)} 个分组")
        for key, group in groups.items():
            logger.info(f"[TransactionSplitService] 分组 {key}: 币种ID={group['currency_id']}, 方向={group['direction']}, 总金额={group['total_amount']}")

        return list(groups.values())

    @staticmethod
    def calculate_weighted_average_rate(items: List[Dict[str, Any]], direction: str) -> Decimal:
        """
        计算加权平均汇率

        Args:
            items: 面值项目列表
            direction: 交易方向 ('buy' 或 'sell')

        Returns:
            加权平均汇率
        """
        logger.info(f"[calculate_weighted_average_rate] 开始计算汇率，方向: {direction}")
        logger.info(f"[calculate_weighted_average_rate] 输入项目: {items}")

        total_weight = Decimal('0')
        weighted_rate_sum = Decimal('0')

        for i, item in enumerate(items):
            weight = Decimal(str(item.get('subtotal', 0)))
            logger.info(f"[calculate_weighted_average_rate] 项目{i+1}: 权重={weight}")

            if weight > 0:
                # 先尝试直接获取rate字段
                rate = item.get('rate', 0)
                if rate and rate > 0:
                    rate = Decimal(str(rate))
                    logger.info(f"[calculate_weighted_average_rate] 项目{i+1}: 使用直接汇率={rate}")
                else:
                    # 根据方向选择对应汇率
                    if direction == 'sell':  # 网点买入外币，使用买入汇率
                        rate = Decimal(str(item.get('buy_rate', 0)))
                        logger.info(f"[calculate_weighted_average_rate] 项目{i+1}: 使用买入汇率={rate}")
                    else:  # 网点卖出外币，使用卖出汇率
                        rate = Decimal(str(item.get('sell_rate', 0)))
                        logger.info(f"[calculate_weighted_average_rate] 项目{i+1}: 使用卖出汇率={rate}")

                if rate > 0:
                    total_weight += weight
                    weighted_rate_sum += rate * weight
                    logger.info(f"[calculate_weighted_average_rate] 项目{i+1}: 有效汇率，累计权重={total_weight}, 累计加权汇率={weighted_rate_sum}")
                else:
                    logger.warning(f"[calculate_weighted_average_rate] 项目{i+1}: 汇率为0或无效")

        final_rate = weighted_rate_sum / total_weight if total_weight > 0 else Decimal('0')
        logger.info(f"[calculate_weighted_average_rate] 最终加权平均汇率: {final_rate}")
        return final_rate

    @staticmethod
    def create_transaction_records(
        business_group_id: str,
        transaction_groups: List[Dict[str, Any]],
        branch_id: int,
        operator_id: int,
        customer_info: Dict[str, Any],
        purpose_id: Optional[str] = None,
        session = None
    ) -> List[Dict[str, Any]]:
        """
        创建交易记录数据

        Args:
            business_group_id: 业务组ID
            transaction_groups: 交易分组列表
            branch_id: 网点ID
            operator_id: 操作员ID
            customer_info: 客户信息
            purpose_id: 交易用途ID
            session: 数据库会话（用于生成流水号）

        Returns:
            交易记录数据列表
        """
        transaction_records = []
        current_datetime = datetime.now()
        current_date = current_datetime.date()
        current_time = current_datetime.strftime('%H:%M:%S')
        created_at = current_datetime  # created_at 使用 datetime 对象

        for sequence, group in enumerate(transaction_groups, 1):
            # 计算加权平均汇率
            avg_rate = TransactionSplitService.calculate_weighted_average_rate(
                group['items'], group['direction']
            )

            # 生成交易号 - 使用统一的ReceiptService
            transaction_no = TransactionSplitService.generate_transaction_no(branch_id, sequence, session)

            # 确定交易类型和金额符号（站在网点角度）
            logger.info(f"[create_transaction_records] 分组{sequence}: 方向={group['direction']}, 总金额={group['total_amount']}, 平均汇率={avg_rate}")

            if group['direction'] == 'buy':
                # 前端选择"买入" = 网点买入外币：外币库存增加（正数），支出本币（负数）
                transaction_type = 'buy'
                foreign_amount = group['total_amount']   # 正数：网点外币库存增加
                local_amount = -(group['total_amount'] * avg_rate)  # 负数：网点支出本币
            else:
                # 前端选择"卖出" = 网点卖出外币：外币库存减少（负数），收到本币（正数）
                transaction_type = 'sell'
                foreign_amount = -group['total_amount']  # 负数：网点外币库存减少
                local_amount = group['total_amount'] * avg_rate  # 正数：网点收到本币

            logger.info(f"[create_transaction_records] 分组{sequence}: type={transaction_type}, foreign_amount={foreign_amount}, local_amount={local_amount}, rate={avg_rate}")

            transaction_record = {
                'transaction_no': transaction_no,
                'branch_id': branch_id,
                'currency_id': group['currency_id'],
                'type': transaction_type,
                'amount': float(foreign_amount),
                'rate': float(avg_rate),
                'local_amount': float(local_amount),
                'customer_name': customer_info.get('name', ''),
                'customer_id': customer_info.get('id_number', ''),
                'customer_country_code': customer_info.get('country_code', ''),
                'customer_address': customer_info.get('address', ''),
                'operator_id': operator_id,
                'transaction_date': current_date,
                'transaction_time': current_time,
                'created_at': created_at,  # 添加创建时间字段
                'business_group_id': business_group_id,
                'group_sequence': sequence,
                'transaction_direction': group['direction'],
                'purpose': purpose_id,
                'remarks': customer_info.get('remarks', ''),
                'payment_method': customer_info.get('payment_method', 'cash'),
                'payment_method_note': customer_info.get('payment_method_note', ''),
                'status': 'completed'
            }

            transaction_records.append(transaction_record)

        return transaction_records

    @staticmethod
    def generate_transaction_no(branch_id: int, sequence: int, session=None) -> str:
        """
        生成交易号 - 使用统一的ReceiptService
        注意：sequence参数保留但不使用，因为ReceiptService有自己的序列管理
        """
        return ReceiptService.generate_receipt_number(branch_id, session)

    @staticmethod
    def execute_split_transaction(
        denomination_data: Dict[str, Any],
        branch_id: int,
        base_currency_id: int,
        operator_id: int,
        customer_info: Dict[str, Any],
        purpose_id: Optional[str] = None,
        exchange_mode: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        执行拆分交易

        Args:
            denomination_data: 面值组合数据
            branch_id: 网点ID
            base_currency_id: 本币ID
            operator_id: 操作员ID
            customer_info: 客户信息
            purpose_id: 交易用途ID
            exchange_mode: 交易方向模式 ('buy_foreign' 或 'sell_foreign')

        Returns:
            执行结果
        """
        session = DatabaseService.get_session()
        try:
            # 1. 分析面值组合，按币种+方向分组
            transaction_groups = TransactionSplitService.analyze_denomination_combinations(
                denomination_data, base_currency_id, exchange_mode
            )

            if not transaction_groups:
                return {
                    'success': False,
                    'message': '没有有效的交易组合',
                    'data': None
                }

            # 2. 生成业务组ID
            business_group_id = TransactionSplitService.generate_business_group_id()

            # 3. 创建交易记录数据
            logger.info(f"[TransactionSplitService] 准备创建交易记录，分组数: {len(transaction_groups)}")
            for i, group in enumerate(transaction_groups):
                logger.info(f"[TransactionSplitService] 分组 {i+1}: 币种ID={group['currency_id']}, 方向={group['direction']}, 总金额={group['total_amount']}")

            transaction_records = TransactionSplitService.create_transaction_records(
                business_group_id, transaction_groups, branch_id, operator_id, customer_info, purpose_id, session
            )

            logger.info(f"[TransactionSplitService] 创建了 {len(transaction_records)} 条交易记录")
            for i, record in enumerate(transaction_records):
                logger.info(f"[TransactionSplitService] 交易记录 {i+1}: 币种ID={record['currency_id']}, 方向={record['transaction_direction']}, 外币金额={record['amount']}, 本币金额={record['local_amount']}")

            # 4. 验证余额充足性（仅记录警告，不阻止交易）
            validation_result = TransactionSplitService.validate_balance_sufficiency(
                session, transaction_records, branch_id, base_currency_id, 'zh-CN'  # Default to Chinese for internal validation
            )

            # 记录验证结果，但不阻止交易（允许预约）
            if not validation_result['success']:
                logger.warning(f"[TransactionSplitService] 余额验证失败，但允许继续执行（用于预约）: {validation_result['message']}")
                # 不返回错误，继续执行交易

            # 5. 执行交易记录插入和余额更新
            created_transactions = []

            for record_data in transaction_records:
                # 创建交易记录
                transaction = ExchangeTransaction(**record_data)
                session.add(transaction)
                session.flush()  # 获取ID

                # 更新外币余额
                foreign_balance_result = TransactionSplitService.update_currency_balance(
                    session, record_data, transaction.id
                )

                if not foreign_balance_result['success']:
                    session.rollback()
                    return {
                        'success': False,
                        'message': f'更新外币余额失败: {foreign_balance_result["message"]}',
                        'data': None
                    }

                # 更新本币余额
                local_amount = Decimal(str(record_data['local_amount']))
                if local_amount != 0:  # 如果有本币变动
                    base_currency_record = {
                        'currency_id': base_currency_id,
                        'branch_id': record_data['branch_id'],
                        'amount': float(local_amount)  # 本币变动金额（已带正负号）
                    }

                    base_balance_result = TransactionSplitService.update_currency_balance(
                        session, base_currency_record, transaction.id
                    )

                    if not base_balance_result['success']:
                        session.rollback()
                        return {
                            'success': False,
                            'message': f'更新本币余额失败: {base_balance_result["message"]}',
                            'data': None
                        }

                # 更新交易记录的余额信息（外币余额）
                transaction.balance_before = foreign_balance_result['balance_before']
                transaction.balance_after = foreign_balance_result['balance_after']

                created_transactions.append({
                    'id': transaction.id,
                    'transaction_no': transaction.transaction_no,
                    'currency_id': transaction.currency_id,
                    'direction': transaction.transaction_direction,
                    'amount': transaction.amount,
                    'local_amount': transaction.local_amount,
                    'rate': transaction.rate
                })

            session.commit()

            logger.info(f"双向交易执行成功，业务组ID: {business_group_id}，创建了 {len(created_transactions)} 条交易记录")

            # 🔧 6. 检查AMLO触发条件（对每个交易记录）
            compliance_results = {
                'amlo_triggered': False,
                'amlo_records': []
            }

            try:
                from services.rule_engine import RuleEngine
                from services.repform.report_data_service import ReportDataService

                for tx_info in created_transactions:
                    # 重新查询交易对象和货币对象
                    transaction_obj = session.query(ExchangeTransaction).filter_by(id=tx_info['id']).first()
                    currency_obj = session.query(Currency).filter_by(id=tx_info['currency_id']).first()

                    if transaction_obj and currency_obj:
                        # 准备交易数据用于规则匹配
                        transaction_data = {
                            'total_amount': abs(float(transaction_obj.local_amount)),
                            'amount': abs(float(transaction_obj.amount)),
                            'currency_code': currency_obj.currency_code,
                            'transaction_type': transaction_obj.type,
                            'direction': getattr(transaction_obj, 'transaction_direction', transaction_obj.type),
                            'payment_method': getattr(transaction_obj, 'payment_method', 'cash'),
                            'customer_country_code': getattr(transaction_obj, 'customer_country_code', 'TH'),
                            'transaction_date': transaction_obj.transaction_date,
                            'customer_id': transaction_obj.customer_id or '',
                            'customer_name': transaction_obj.customer_name or ''
                        }

                        logger.info(f"[AMLO检查] 交易 {tx_info['transaction_no']}: 本币金额={transaction_data['total_amount']} THB, 外币金额={transaction_data['amount']} {transaction_data['currency_code']}, 方向={transaction_data['direction']}")

                        # 检查各个AMLO报告类型的触发条件
                        report_types = ['AMLO-1-01', 'AMLO-1-02', 'AMLO-1-03']
                        triggered_reports = []

                        for report_type in report_types:
                            trigger_result = RuleEngine.check_triggers(
                                db_session=session,
                                report_type=report_type,
                                data=transaction_data,
                                branch_id=branch_id
                            )

                            logger.info(f"[AMLO检查] {report_type} 检查结果: triggered={trigger_result.get('triggered')}, rule={trigger_result.get('highest_priority_rule', {}).get('rule_name', 'N/A')}")

                            if trigger_result.get('triggered'):
                                triggered_reports.append(report_type)
                                logger.info(f"✓ 交易 {tx_info['transaction_no']} 触发 {report_type}")

                        # 为每个触发的报告类型创建预约记录
                        for report_type in triggered_reports:
                            # 映射报告类型到触发类型
                            trigger_type_map = {
                                'AMLO-1-01': 'CTR',
                                'AMLO-1-02': 'ATR',
                                'AMLO-1-03': 'STR'
                            }
                            trigger_type = trigger_type_map.get(report_type, 'CTR')

                            # 准备预约数据
                            reservation_data = {
                                'customer_id': transaction_obj.customer_id or '',
                                'customer_name': transaction_obj.customer_name or '',
                                'customer_country_code': getattr(transaction_obj, 'customer_country_code', 'TH'),
                                'currency_id': currency_obj.id,
                                'currency_code': currency_obj.currency_code,
                                'direction': getattr(transaction_obj, 'transaction_direction', 'sell'),
                                'amount': abs(float(transaction_obj.amount)),
                                'local_amount': abs(float(transaction_obj.local_amount)),
                                'rate': float(transaction_obj.rate),
                                'trigger_type': trigger_type,
                                'report_type': report_type,
                                'form_data': json.dumps({}),  # 空表单数据，等待填写
                                'branch_id': branch_id,
                                'operator_id': operator_id,
                                'transaction_id': transaction_obj.id
                            }

                            # 创建预约记录
                            reservation_id = ReportDataService.save_reservation(session, reservation_data)
                            compliance_results['amlo_triggered'] = True
                            compliance_results['amlo_records'].append({
                                'transaction_id': tx_info['id'],
                                'transaction_no': tx_info['transaction_no'],
                                'report_type': report_type,
                                'reservation_id': reservation_id
                            })
                            logger.info(f"为交易 {tx_info['transaction_no']} 创建了 {report_type} 预约记录 (ID: {reservation_id})")

                session.commit()  # 提交AMLO预约记录

            except Exception as amlo_error:
                logger.error(f"AMLO触发检查失败: {str(amlo_error)}")
                import traceback
                traceback.print_exc()
                # 不中断主流程，AMLO检查失败不影响交易

            return {
                'success': True,
                'message': '交易执行成功',
                'data': {
                    'business_group_id': business_group_id,
                    'transaction_count': len(created_transactions),
                    'transactions': created_transactions,
                    'compliance': compliance_results  # 返回合规检查结果
                }
            }

        except Exception as e:
            session.rollback()
            logger.error(f"执行拆分交易失败: {str(e)}")
            return {
                'success': False,
                'message': f'交易执行失败: {str(e)}',
                'data': None
            }
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def validate_balance_sufficiency(
        session, transaction_records: List[Dict[str, Any]], branch_id: int, base_currency_id: int, language: str = 'zh-CN'
    ) -> Dict[str, Any]:
        """验证余额充足性"""
        try:
            logger.info(f"[TransactionSplitService] validate_balance_sufficiency 开始验证余额，记录数: {len(transaction_records)}")

            for record in transaction_records:
                currency_id = record['currency_id']
                amount_change = Decimal(str(record['amount']))
                local_amount_change = Decimal(str(record['local_amount']))
                direction = record.get('transaction_direction', 'unknown')

                logger.info(f"[TransactionSplitService] 验证余额 - 币种ID: {currency_id}, 方向: {direction}, 外币变动: {amount_change}, 本币变动: {local_amount_change}")

                # 检查外币余额
                if amount_change < 0:  # 减少外币库存
                    logger.info(f"[TransactionSplitService] 需要减少外币库存，检查余额充足性...")
                    balance = session.query(CurrencyBalance).filter_by(
                        branch_id=branch_id,
                        currency_id=currency_id
                    ).with_for_update().first()

                    logger.info(f"[TransactionSplitService] 当前外币余额记录: {balance}")
                    if balance:
                        logger.info(f"[TransactionSplitService] 当前余额: {balance.balance}, 需要减少: {abs(amount_change)}")

                    if not balance or balance.balance < abs(amount_change):
                        # 获取货币信息用于国际化错误消息
                        currency = session.query(Currency).filter_by(id=currency_id).first()
                        currency_name = currency.currency_name if currency else t('system.unknown_currency', language)
                        currency_code = currency.currency_code if currency else 'UNKNOWN'

                        error_msg = t('balance.foreign_stock_insufficient', language,
                                    currency_name=currency_name,
                                    required_amount=abs(amount_change),
                                    currency_code=currency_code,
                                    current_stock=balance.balance if balance else 0,
                                    missing_amount=abs(amount_change) - (balance.balance if balance else 0))
                        logger.error(f"[TransactionSplitService] {error_msg}")
                        return {
                            'success': False,
                            'message': error_msg
                        }
                else:
                    logger.info(f"[TransactionSplitService] 增加外币库存，无需检查余额 (amount_change: {amount_change})")

                # 检查本币余额（如果有本币相关的余额记录）
                if local_amount_change < 0:  # 减少本币库存
                    logger.info(f"[TransactionSplitService] 需要减少本币库存，检查余额充足性...")
                    base_balance = session.query(CurrencyBalance).filter_by(
                        branch_id=branch_id,
                        currency_id=base_currency_id
                    ).with_for_update().first()
                    
                    logger.info(f"[TransactionSplitService] 当前本币余额记录: {base_balance}")
                    if base_balance:
                        logger.info(f"[TransactionSplitService] 当前本币余额: {base_balance.balance}, 需要减少: {abs(local_amount_change)}")
                    
                    if not base_balance or base_balance.balance < abs(local_amount_change):
                        # 获取本币信息用于国际化错误消息
                        base_currency = session.query(Currency).filter_by(id=base_currency_id).first()
                        currency_name = base_currency.currency_name if base_currency else t('system.base_currency', language)
                        currency_code = base_currency.currency_code if base_currency else 'BASE'
                        
                        error_msg = t('balance.base_stock_insufficient', language,
                                    currency_name=currency_name,
                                    required_amount=abs(local_amount_change),
                                    currency_code=currency_code,
                                    current_stock=base_balance.balance if base_balance else 0,
                                    missing_amount=abs(local_amount_change) - (base_balance.balance if base_balance else 0))
                        logger.error(f"[TransactionSplitService] {error_msg}")
                        return {
                            'success': False,
                            'message': error_msg
                        }
                else:
                    logger.info(f"[TransactionSplitService] 增加本币库存，无需检查余额 (local_amount_change: {local_amount_change})")

            return {'success': True, 'message': t('validation.validation_passed', language)}

        except Exception as e:
            return {'success': False, 'message': t('balance.balance_check_error', language, error=str(e))}

    @staticmethod
    def update_currency_balance(
        session, record_data: Dict[str, Any], transaction_id: int
    ) -> Dict[str, Any]:
        """更新币种余额"""
        try:
            currency_id = record_data['currency_id']
            branch_id = record_data['branch_id']
            amount_change = Decimal(str(record_data['amount']))

            # 获取或创建余额记录（使用行锁）
            balance = session.query(CurrencyBalance).filter_by(
                branch_id=branch_id,
                currency_id=currency_id
            ).with_for_update().first()

            if not balance:
                # 创建新的余额记录
                balance = CurrencyBalance(
                    branch_id=branch_id,
                    currency_id=currency_id,
                    balance=Decimal('0'),
                    updated_at=datetime.utcnow()
                )
                session.add(balance)
                session.flush()

            balance_before = balance.balance
            balance_after = balance_before + amount_change

            # 更新余额
            balance.balance = balance_after
            balance.updated_at = datetime.utcnow()

            return {
                'success': True,
                'balance_before': float(balance_before),
                'balance_after': float(balance_after)
            }

        except Exception as e:
            return {
                'success': False,
                'message': f'更新余额失败: {str(e)}'
            }

    @staticmethod
    def get_business_group_transactions(business_group_id: str) -> List[Dict[str, Any]]:
        """获取业务组的所有交易记录"""
        session = DatabaseService.get_session()
        try:
            transactions = session.query(ExchangeTransaction).filter_by(
                business_group_id=business_group_id
            ).order_by(ExchangeTransaction.group_sequence).all()

            result = []
            for transaction in transactions:
                result.append({
                    'id': transaction.id,
                    'transaction_no': transaction.transaction_no,
                    'currency_id': transaction.currency_id,
                    'direction': transaction.transaction_direction,
                    'amount': float(transaction.amount),
                    'local_amount': float(transaction.local_amount),
                    'rate': float(transaction.rate),
                    'group_sequence': transaction.group_sequence,
                    'status': transaction.status
                })

            return result

        except Exception as e:
            logger.error(f"获取业务组交易记录失败: {str(e)}")
            return []
        finally:
            DatabaseService.close_session(session)

    @staticmethod
    def reverse_business_group(
        business_group_id: str, operator_id: int, reason: str = ''
    ) -> Dict[str, Any]:
        """反结算整个业务组"""
        session = DatabaseService.get_session()
        try:
            # 获取原始交易记录
            original_transactions = session.query(ExchangeTransaction).filter_by(
                business_group_id=business_group_id,
                status='completed'
            ).order_by(ExchangeTransaction.group_sequence).all()

            if not original_transactions:
                return {
                    'success': False,
                    'message': '没有找到可反结算的交易记录'
                }

            # 生成新的业务组ID用于反结算记录
            reversal_group_id = f"REV_{business_group_id}"

            reversed_transactions = []

            for transaction in original_transactions:
                # 创建反向交易记录
                current_datetime = datetime.now()
                reversal_record = ExchangeTransaction(
                    transaction_no=TransactionSplitService.generate_transaction_no(
                        transaction.branch_id, transaction.group_sequence, session
                    ),
                    branch_id=transaction.branch_id,
                    currency_id=transaction.currency_id,
                    type=f"reversal_{transaction.type}",
                    amount=-transaction.amount,  # 反向金额
                    rate=transaction.rate,
                    local_amount=-transaction.local_amount,  # 反向本币金额
                    customer_name=transaction.customer_name,
                    customer_id=transaction.customer_id,
                    customer_country_code=transaction.customer_country_code,
                    customer_address=transaction.customer_address,
                    operator_id=operator_id,
                    transaction_date=current_datetime.date(),
                    transaction_time=current_datetime.strftime('%H:%M:%S'),
                    created_at=current_datetime,  # 添加创建时间
                    business_group_id=reversal_group_id,
                    group_sequence=transaction.group_sequence,
                    transaction_direction=transaction.transaction_direction,
                    purpose=transaction.purpose,
                    remarks=f"反结算: {reason}" if reason else "反结算",
                    payment_method=transaction.payment_method,
                    payment_method_note=transaction.payment_method_note,
                    original_transaction_no=transaction.transaction_no,
                    status='completed'
                )

                session.add(reversal_record)
                session.flush()

                # 更新余额
                balance_result = TransactionSplitService.update_currency_balance(
                    session, {
                        'currency_id': reversal_record.currency_id,
                        'branch_id': reversal_record.branch_id,
                        'amount': reversal_record.amount
                    }, reversal_record.id
                )

                if not balance_result['success']:
                    session.rollback()
                    return {
                        'success': False,
                        'message': f'反结算余额更新失败: {balance_result["message"]}'
                    }

                reversal_record.balance_before = balance_result['balance_before']
                reversal_record.balance_after = balance_result['balance_after']

                # 标记原交易为已反结算
                transaction.status = 'reversed'

                reversed_transactions.append(reversal_record.id)

            session.commit()

            logger.info(f"业务组反结算成功，原业务组ID: {business_group_id}，反结算业务组ID: {reversal_group_id}")

            return {
                'success': True,
                'message': '业务组反结算成功',
                'data': {
                    'original_group_id': business_group_id,
                    'reversal_group_id': reversal_group_id,
                    'reversed_transaction_count': len(reversed_transactions),
                    'reversed_transaction_ids': reversed_transactions
                }
            }

        except Exception as e:
            session.rollback()
            logger.error(f"业务组反结算失败: {str(e)}")
            return {
                'success': False,
                'message': f'反结算失败: {str(e)}'
            }
        finally:
            DatabaseService.close_session(session)