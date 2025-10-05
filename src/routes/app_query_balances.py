from flask import Blueprint, request, jsonify
from sqlalchemy import func, desc
from datetime import datetime, date
from models.exchange_models import CurrencyBalance, Currency, Branch, Operator, ExchangeTransaction
from services.db_service import DatabaseService
from services.auth_service import token_required, has_permission, check_business_lock
from sqlalchemy.orm import joinedload
import logging
import random
from utils.transaction_utils import generate_transaction_no

# 配置日志
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# 创建blueprint，但不再注册任何路由
# 保留文件是为了避免导入错误
balances_bp = Blueprint('balances', __name__, url_prefix='/api/balances')

# 所有接口已删除，文件保留以避免导入错误 