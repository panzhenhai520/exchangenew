import os
import logging
from flask import g, current_app
from sqlalchemy import create_engine, event, inspect
from sqlalchemy.orm import sessionmaker, scoped_session, Session
from sqlalchemy.exc import SQLAlchemyError
try:
    from src.models.exchange_models import Base
except ImportError:
    # 当从src目录内运行时的相对导入
    from models.exchange_models import Base
from functools import wraps
from dotenv import load_dotenv, dotenv_values

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# 设置SQLAlchemy相关日志级别以减少输出
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.pool').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.dialects').setLevel(logging.WARNING)
logging.getLogger('sqlalchemy.orm').setLevel(logging.WARNING)

def load_env_config():
    """加载.env文件配置"""
    # 获取项目根目录路径
    current_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(current_dir)  # src的上级目录
    
    # 确保项目根目录是正确的
    if not os.path.exists(os.path.join(project_root, '.env')):
        # 如果当前目录是src/services，那么项目根目录应该是src的上级目录
        if 'src' in current_dir:
            project_root = os.path.dirname(os.path.dirname(current_dir))
    
    # 尝试加载.env文件（项目根目录）
    env_path = os.path.join(project_root, '.env')
    if os.path.exists(env_path):
        try:
            load_dotenv(env_path, override=True)  # 强制覆盖环境变量
        except UnicodeDecodeError as e:
            logger.error(f".env文件编码错误: {e}")
            logger.error("请确保.env文件是UTF-8编码格式")
        except Exception as e:
            logger.error(f"加载.env文件失败: {e}")
    else:
        logger.warning(f".env文件不存在: {env_path}")
    
    # 尝试加载.env.local文件
    env_local_path = os.path.join(project_root, '.env.local')
    if os.path.exists(env_local_path):
        try:
            load_dotenv(env_local_path, override=True)
        except UnicodeDecodeError as e:
            logger.warning(f".env.local文件编码错误，跳过加载: {e}")
        except Exception as e:
            logger.warning(f"加载.env.local文件失败，跳过: {e}")
    
    # 如果项目根目录的.env文件不存在，尝试从当前目录加载
    current_env_path = os.path.join(current_dir, '.env')
    if not os.path.exists(env_path) and os.path.exists(current_env_path):
        load_dotenv(current_env_path, override=True)

# 加载环境配置
load_env_config()

# 数据库配置 - 从.env文件读取
import os
current_working_dir = os.getcwd()
possible_paths = [
    os.path.join(current_working_dir, '.env'),
    os.path.join(os.path.dirname(current_working_dir), '.env'),
    os.path.join(os.path.dirname(os.path.dirname(current_working_dir)), '.env'),
]

env_path = None
for path in possible_paths:
    if os.path.exists(path):
        env_path = path
        break

if env_path:
    config = dotenv_values(env_path)
    DB_TYPE = config.get('DB_TYPE', 'mysql').lower()
else:
    DB_TYPE = 'sqlite'  # 默认值

def get_db_url():
    """获取数据库URL"""
    if DB_TYPE == 'mysql':
        # 只从.env文件读取配置

        # 使用与DB_TYPE相同的路径计算方法
        current_working_dir = os.getcwd()
        possible_paths = [
            os.path.join(current_working_dir, '.env'),
            os.path.join(os.path.dirname(current_working_dir), '.env'),
            os.path.join(os.path.dirname(os.path.dirname(current_working_dir)), '.env'),
        ]
        
        env_path = None
        for path in possible_paths:
            if os.path.exists(path):
                env_path = path
                break
        
        if not env_path:
            logger.error(f"未找到.env文件，尝试的路径: {possible_paths}")
            raise FileNotFoundError(f"未找到.env文件")
        
        config = dotenv_values(env_path)
        mysql_host = config.get('MYSQL_HOST', 'localhost')
        mysql_port = config.get('MYSQL_PORT', '3306')
        mysql_user = config.get('MYSQL_USER', 'root')
        mysql_password = config.get('MYSQL_PASSWORD', 'your_password')
        mysql_database = config.get('MYSQL_DATABASE', 'Exchange')
        mysql_charset = config.get('MYSQL_CHARSET', 'utf8mb4')
        
        return (
            f'mysql+pymysql://{mysql_user}:{mysql_password}'
            f'@{mysql_host}:{mysql_port}/{mysql_database}'
            f'?charset={mysql_charset}'
        )
    else:
        # SQLite配置
        BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        DATA_DIR = os.path.join(BASE_DIR, 'data')
        DATABASE_PATH = os.path.join(DATA_DIR, 'exchange_system.db')
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
            logger.info(f"Created data directory at {DATA_DIR}")
        return f'sqlite:///{DATABASE_PATH}'

# Create global engine instance
def create_db_engine():
    """创建数据库引擎"""
    db_url = get_db_url()
    
    if DB_TYPE == 'mysql':
        # MySQL引擎配置
        engine = create_engine(
            db_url,
            echo=os.getenv('EXCHANGEOK_DB_ECHO', 'false').lower() == 'true',
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20,
            # 设置事务隔离级别为READ_COMMITTED，确保事务提交后立即可见
            isolation_level='READ_COMMITTED'
        )
        return engine
    else:
        # SQLite引擎配置
        return create_engine(
            db_url,
            echo=os.getenv('EXCHANGEOK_DB_ECHO', 'false').lower() == 'true',
            pool_pre_ping=True,
            pool_recycle=3600,
            connect_args={"check_same_thread": False}
        )

engine = create_db_engine()

# Create session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 测试数据库连接
def test_database_connection():
    """测试数据库连接"""
    try:
        if DB_TYPE == 'mysql':
            logger.info("🔍 测试MySQL数据库连接...")
            
            # 创建测试会话
            test_session = SessionLocal()
            try:
                # 执行简单查询测试连接
                result = test_session.execute("SELECT 1")
                result.fetchone()
                logger.info("✅ MySQL数据库连接测试成功")
            except Exception as e:
                logger.error(f"❌ MySQL数据库连接测试失败: {e}")
                raise
            finally:
                test_session.close()
        else:
            logger.info("🔍 测试SQLite数据库连接...")
            # SQLite连接测试逻辑可以在这里添加
    except Exception as e:
        logger.error(f"❌ 数据库连接测试失败: {e}")
        raise

# 在模块加载时测试连接
# try:
#     test_database_connection()
# except Exception as e:
#     logger.error(f"数据库连接初始化失败: {e}")

class DatabaseService:
    """统一的数据库服务类"""
    
    @staticmethod
    def get_session():
        """获取新的数据库会话"""
        try:
            session = SessionLocal()
            return session
        except Exception as e:
            logger.error(f"Error creating database session: {str(e)}")
            raise

    @staticmethod
    def close_session(session):
        """关闭数据库会话"""
        try:
            if session:
                # Ensure any pending transactions are handled
                if session.in_transaction():
                    session.rollback()
                session.close()
        except Exception as e:
            logger.error(f"Error closing database session: {str(e)}")
            # Don't raise here to avoid masking original errors

    @staticmethod
    def commit_session(session):
        """提交数据库会话"""
        try:
            if session:
                session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"Error committing database session: {str(e)}")
            raise

    @staticmethod
    def rollback_session(session):
        """回滚数据库会话"""
        try:
            if session:
                session.rollback()
        except Exception as e:
            logger.error(f"Error rolling back database session: {str(e)}")
            raise

    @staticmethod
    def init_db():
        """初始化数据库"""
        try:
            if DB_TYPE == 'mysql':
                # MySQL数据库初始化 - 只需要创建表结构
                Base.metadata.create_all(bind=engine)
                logger.info("MySQL database initialized successfully")
            else:
                # SQLite数据库初始化
                BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
                DATA_DIR = os.path.join(BASE_DIR, 'data')
                DATABASE_PATH = os.path.join(DATA_DIR, 'exchange_system.db')
                
                # 确保data目录存在
                if not os.path.exists(DATA_DIR):
                    os.makedirs(DATA_DIR)
                    logger.info(f"Created data directory at {DATA_DIR}")
                
                # 初始化数据库表
                Base.metadata.create_all(bind=engine)
                logger.info(f"SQLite database initialized successfully at {DATABASE_PATH}")
            
            # 注册branch_id过滤中间件
            if not event.contains(Session, 'do_orm_execute', DatabaseService.branch_filter_middleware):
                event.listen(Session, 'do_orm_execute', DatabaseService.branch_filter_middleware)
                logger.info("Branch filter middleware registered successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")
            raise

    @staticmethod
    def init_permissions(session):
        """Initialize default permissions"""
        try:
            from src.models.exchange_models import Permission
        except ImportError:
            from models.exchange_models import Permission
        
        permissions = [
            Permission(permission_name='balance_manage', description='管理币种余额'),
            Permission(permission_name='view_balances', description='查看币种余额'),
            Permission(permission_name='manage_operators', description='管理操作员'),
            Permission(permission_name='manage_roles', description='管理角色和权限'),
            Permission(permission_name='view_transactions', description='查看交易记录'),
            Permission(permission_name='manage_rates', description='管理汇率'),
            Permission(permission_name='manage_all_branches', description='管理所有网点')
        ]
        
        for permission in permissions:
            existing = session.query(Permission).filter_by(permission_name=permission.permission_name).first()
            if not existing:
                session.add(permission)
        
        session.commit()

    @staticmethod
    def branch_filter_middleware(orm_execute_state):
        """Middleware to automatically add branch_id filter to queries"""
        
        # Skip if not in request context or if explicitly disabled
        if not hasattr(g, 'current_user') or getattr(g, 'skip_branch_filter', False):
            return
            
        # Skip for system tables or tables without branch_id
        if not orm_execute_state.is_select:
            return
            
        # Get the primary entity being queried
        entities = orm_execute_state.statement.column_descriptions
        if not entities:
            return
            
        primary_entity = entities[0].get('entity')
        if not primary_entity:
            return
            
        # Check if the entity has branch_id column
        mapper = inspect(primary_entity)
        if not hasattr(mapper.class_, 'branch_id'):
            return
            
        # Skip for Currency table - currencies should be global
        if mapper.class_.__name__ == 'Currency':
            return
            
        # Skip if user has all-branch permission and skip_branch_filter is True
        current_user = getattr(g, 'current_user', None)
        if (current_user and 
            isinstance(current_user, dict) and 
            'manage_all_branches' in current_user.get('permissions', []) and 
            getattr(g, 'skip_branch_filter', False)):
            return
            
        # Add branch_id condition
        if current_user and isinstance(current_user, dict):
            orm_execute_state.statement = orm_execute_state.statement.where(
                primary_entity.branch_id == current_user.get('branch_id')
            )

    @staticmethod
    def skip_branch_filter(func):
        """Decorator to skip branch filter for specific queries"""
        @wraps(func)
        def wrapper(*args, **kwargs):
            g.skip_branch_filter = True
            try:
                return func(*args, **kwargs)
            finally:
                g.skip_branch_filter = False
        return wrapper

# 创建全局数据库实例
db = SessionLocal()

def shutdown_session(exception=None):
    """在应用关闭时清理数据库会话"""
    db.close()

def get_branch_list():
    """Get list of all branches"""
    session = DatabaseService.get_session()
    try:
        try:
            from src.models.exchange_models import Branch
        except ImportError:
            from models.exchange_models import Branch
        branches = session.query(Branch).all()
        result = []
        for branch in branches:
            result.append({
                'id': branch.id,
                'branch_name': branch.branch_name,
                'branch_code': branch.branch_code,
                'address': branch.address,
                'is_active': branch.is_active
            })
        logger.info(f"Successfully retrieved {len(result)} branches")
        return result
    except SQLAlchemyError as e:
        logger.error(f"Database error while fetching branches: {str(e)}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while fetching branches: {str(e)}")
        raise
    finally:
        DatabaseService.close_session(session)


