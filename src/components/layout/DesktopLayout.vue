<template>
  <div class="d-flex flex-column min-vh-100">
    <nav class="navbar navbar-expand-lg navbar-dark bg-primary">
      <div class="container-fluid">
        <!-- 移除品牌标识，为右侧菜单腾出空间 -->
        
        <button class="navbar-toggler" type="button" data-bs-toggle="collapse" data-bs-target="#navbarNav" aria-controls="navbarNav" aria-expanded="false" aria-label="Toggle navigation">
          <span class="navbar-toggler-icon"></span>
        </button>
        
        <div class="collapse navbar-collapse" id="navbarNav">
          <ul class="navbar-nav me-auto" id="mainNavbar">
            <!-- 核心菜单项 - 始终显示 -->
            <li class="nav-item core-menu">
              <router-link class="nav-link" to="/dashboard">
                <font-awesome-icon :icon="['fas', 'home']" /> 
                <span class="nav-text">{{ $t('common.dashboard') }}</span>
              </router-link>
            </li>
            
            <li class="nav-item dropdown core-menu" v-if="hasPermission('transaction_execute')">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false" @click="toggleDropdown">
                <font-awesome-icon :icon="['fas', 'exchange-alt']" /> 
                <span class="nav-text">{{ $t('common.exchange') }}</span>
              </a>
              <ul class="dropdown-menu">
                <li>
                  <router-link class="dropdown-item" to="/exchange">
                    <font-awesome-icon :icon="['fas', 'calculator']" class="me-2" />
                    {{ $t('exchange.standard_exchange') }}
                  </router-link>
                </li>
                <li>
                  <router-link class="dropdown-item" to="/dual-direction-exchange">
                    <font-awesome-icon :icon="['fas', 'coins']" class="me-2" />
                    {{ $t('exchange.denomination_exchange') }}
                  </router-link>
                </li>
              </ul>
            </li>
            
            <li class="nav-item core-menu" v-if="hasPermission('rate_manage')">
              <router-link class="nav-link" to="/rates">
                <font-awesome-icon :icon="['fas', 'chart-line']" /> 
                <span class="nav-text">{{ $t('rates.today_rates') }}</span>
              </router-link>
            </li>
            
            <!-- 余额管理 -->
            <li class="nav-item dropdown secondary-menu" v-if="hasPermission('balance_manage')">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false" @click="toggleDropdown">
                <font-awesome-icon :icon="['fas', 'wallet']" /> 
                <span class="nav-text">{{ $t('common.balances') }}</span>
              </a>
              <ul class="dropdown-menu">
                <li v-if="hasPermission('balance_manage')">
                  <router-link class="dropdown-item" to="/initial-balance">
                    {{ $t('balance.initial') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('balance_manage')">
                  <router-link class="dropdown-item" to="/adjust-balance">
                    {{ $t('balance.adjust') }}
                  </router-link>
                </li>
              </ul>
            </li>
            
            <!-- 日终处理 -->
            <li class="nav-item secondary-menu" v-if="hasPermission('end_of_day')">
              <router-link class="nav-link" to="/end-of-day">
                <font-awesome-icon :icon="['fas', 'calendar-check']" /> 
                <span class="nav-text">{{ $t('common.end_of_day') }}</span>
              </router-link>
            </li>
            
            <!-- 交易冲正 -->
            <li class="nav-item secondary-menu" v-if="hasPermission('reverse_transaction')">
              <router-link class="nav-link" to="/reversal">
                <font-awesome-icon :icon="['fas', 'undo']" /> 
                <span class="nav-text">{{ $t('common.reversal') }}</span>
              </router-link>
            </li>
            
            <!-- 查询菜单 -->
            <li class="nav-item dropdown secondary-menu" v-if="hasAnyPermission(['view_transactions', 'view_balances', 'log_view', 'report_view'])">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false" @click="toggleDropdown">
                <font-awesome-icon :icon="['fas', 'search']" />
                <span class="nav-text">{{ $t('common.search') }}</span>
              </a>
              <ul class="dropdown-menu">
                <li v-if="hasPermission('log_view')">
                  <router-link class="dropdown-item" to="/log-management">
                    {{ $t('menu.system_log') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('view_transactions')">
                  <router-link class="dropdown-item" to="/transactions">
                    {{ $t('menu.transaction_query') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('view_balances')">
                  <router-link class="dropdown-item" to="/balances">
                    {{ $t('menu.balance_query') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('reverse_transaction')">
                  <router-link class="dropdown-item" to="/reversal-query">
                    {{ $t('menu.reversal_query') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('balance_manage')">
                  <router-link class="dropdown-item" to="/balance-adjust-query">
                    {{ $t('menu.balance_adjustment_query') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('view_transactions')">
                  <router-link class="dropdown-item" to="/income-query">
                    {{ $t('menu.income_query') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('view_balances')">
                  <router-link class="dropdown-item" to="/foreign-stock-query">
                    {{ $t('menu.foreign_stock_query') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('view_balances')">
                  <router-link class="dropdown-item" to="/local-stock-query">
                    {{ $t('menu.local_stock_query') }}
                  </router-link>
                </li>
              </ul>
            </li>

            <!-- AMLO审计菜单 -->
            <li class="nav-item dropdown secondary-menu" v-if="hasAnyPermission(['amlo_reservation_view', 'amlo_reservation_audit', 'amlo_report_view'])">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false" @click="toggleDropdown">
                <font-awesome-icon :icon="['fas', 'file-shield']" />
                <span class="nav-text">{{ $t('menu.amlo_audit') }}</span>
              </a>
              <ul class="dropdown-menu">
                <li v-if="hasPermission('amlo_reservation_view')">
                  <router-link class="dropdown-item" to="/amlo/reservations">
                    <font-awesome-icon :icon="['fas', 'clipboard-check']" class="me-2" />
                    {{ $t('menu.amlo_reservation_audit') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('amlo_report_view')">
                  <router-link class="dropdown-item" to="/amlo/reports">
                    <font-awesome-icon :icon="['fas', 'list-alt']" class="me-2" />
                    {{ $t('menu.amlo_report_list') }}
                  </router-link>
                </li>
              </ul>
            </li>

            <!-- BOT合规报告菜单 -->
            <li class="nav-item dropdown secondary-menu" v-if="hasAnyPermission(['bot_report_view', 'bot_report_export'])">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false" @click="toggleDropdown">
                <font-awesome-icon :icon="['fas', 'file-export']" />
                <span class="nav-text">{{ $t('menu.bot_report') }}</span>
              </a>
              <ul class="dropdown-menu">
                <li v-if="hasPermission('bot_report_view')">
                  <router-link class="dropdown-item" to="/bot/t1-submit">
                    <font-awesome-icon :icon="['fas', 'calendar-day']" class="me-2" />
                    {{ $t('menu.bot_t1_submit') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('bot_report_view')">
                  <router-link class="dropdown-item" to="/bot/reports">
                    <font-awesome-icon :icon="['fas', 'search-dollar']" class="me-2" />
                    {{ $t('menu.bot_report_query') }}
                  </router-link>
                </li>
              </ul>
            </li>

            <!-- 更多菜单 - 在中等屏幕上显示 -->
            <li class="nav-item dropdown more-menu" v-if="hasAnyMenuItems">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false" @click="toggleDropdown">
                <font-awesome-icon :icon="['fas', 'ellipsis-h']" /> 
                <span class="nav-text">{{ $t('common.more') }}</span>
              </a>
              <ul class="dropdown-menu">
                <!-- 余额管理子菜单 -->
                <li v-if="hasPermission('balance_manage')">
                  <h6 class="dropdown-header">{{ $t('common.balances') }}</h6>
                </li>
                <li v-if="hasPermission('balance_manage')">
                  <router-link class="dropdown-item" to="/initial-balance">
                    <font-awesome-icon :icon="['fas', 'wallet']" class="me-2" />
                    {{ $t('balance.initial') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('balance_manage')">
                  <router-link class="dropdown-item" to="/adjust-balance">
                    <font-awesome-icon :icon="['fas', 'wallet']" class="me-2" />
                    {{ $t('balance.adjust') }}
                  </router-link>
                </li>
                
                <!-- 其他功能 -->
                <li v-if="hasPermission('end_of_day')">
                  <hr class="dropdown-divider">
                </li>
                <li v-if="hasPermission('end_of_day')">
                  <router-link class="dropdown-item" to="/end-of-day">
                    <font-awesome-icon :icon="['fas', 'calendar-check']" class="me-2" />
                    {{ $t('common.end_of_day') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('end_of_day')">
                  <router-link class="dropdown-item" to="/eod-history">
                    <font-awesome-icon :icon="['fas', 'history']" class="me-2" />
                    {{ $t('eod.history_button') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('reverse_transaction')">
                  <router-link class="dropdown-item" to="/reversal">
                    <font-awesome-icon :icon="['fas', 'undo']" class="me-2" />
                    {{ $t('common.reversal') }}
                  </router-link>
                </li>

                <!-- AMLO审计子菜单 -->
                <li v-if="hasAnyPermission(['amlo_reservation_view', 'amlo_report_view'])">
                  <hr class="dropdown-divider">
                </li>
                <li v-if="hasAnyPermission(['amlo_reservation_view', 'amlo_report_view'])">
                  <h6 class="dropdown-header">{{ $t('menu.amlo_audit') }}</h6>
                </li>
                <li v-if="hasPermission('amlo_reservation_view')">
                  <router-link class="dropdown-item" to="/amlo/reservations">
                    <font-awesome-icon :icon="['fas', 'clipboard-check']" class="me-2" />
                    {{ $t('menu.amlo_reservation_audit') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('amlo_report_view')">
                  <router-link class="dropdown-item" to="/amlo/reports">
                    <font-awesome-icon :icon="['fas', 'list-alt']" class="me-2" />
                    {{ $t('menu.amlo_report_list') }}
                  </router-link>
                </li>

                <!-- BOT合规报告子菜单 -->
                <li v-if="hasAnyPermission(['bot_report_view', 'bot_report_export'])">
                  <hr class="dropdown-divider">
                </li>
                <li v-if="hasAnyPermission(['bot_report_view', 'bot_report_export'])">
                  <h6 class="dropdown-header">{{ $t('menu.bot_compliance') }}</h6>
                </li>
                <li v-if="hasPermission('bot_report_view')">
                  <router-link class="dropdown-item" to="/bot/reports">
                    <font-awesome-icon :icon="['fas', 'search-dollar']" class="me-2" />
                    {{ $t('menu.bot_report_query') }}
                  </router-link>
                </li>
              </ul>
            </li>
          </ul>
          
          <ul class="navbar-nav">
            <li class="nav-item dropdown" v-if="hasAnyPermission(['system_manage', 'user_manage', 'role_manage', 'branch_manage', 'currency_manage'])">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false" @click="toggleDropdown">
                <font-awesome-icon :icon="['fas', 'cogs']" /> {{ $t('common.system_maintenance') }}
              </a>
              <ul class="dropdown-menu">
                <li v-if="hasPermission('branch_manage')">
                  <router-link class="dropdown-item" to="/branch-management">
                    <font-awesome-icon :icon="['fas', 'building']" /> {{ $t('common.branch_management') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('user_manage')">
                  <router-link class="dropdown-item" to="/user-management">
                    <font-awesome-icon :icon="['fas', 'users']" /> {{ $t('common.user_management') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('role_manage')">
                  <router-link class="dropdown-item" to="/role-management">
                    <font-awesome-icon :icon="['fas', 'user-shield']" /> {{ $t('common.role_management') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('system_manage') && showadd">
                  <router-link class="dropdown-item" to="/user-activity">
                    <font-awesome-icon :icon="['fas', 'chart-line']" /> {{ $t('common.user_activity') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('currency_manage')">
                  <router-link class="dropdown-item" to="/currency-management">
                    <font-awesome-icon :icon="['fas', 'money-bill-wave']" /> {{ $t('common.currency_management') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('system_manage') && showadd">
                  <router-link class="dropdown-item" to="/system/print-settings">
                    <font-awesome-icon :icon="['fas', 'print']" /> {{ $t('common.print_settings') }}
                  </router-link>
                </li>
                <li v-if="hasPermission('branch_manage')">
                  <router-link class="dropdown-item" to="/standards-management">
                    <font-awesome-icon :icon="['fas', 'clipboard-list']" /> {{ $t('common.standards_management') }}
                  </router-link>
                </li>
                <li><hr class="dropdown-divider"></li>
                <li v-if="hasPermission('system_manage')">
                  <router-link class="dropdown-item text-danger" to="/data-clear">
                    <font-awesome-icon :icon="['fas', 'trash-alt']" /> {{ $t('data_clear.title') }}
                  </router-link>
                </li>
              </ul>
            </li>

            <!-- 语言切换器 - 确保在所有屏幕尺寸下都可访问 -->
            <li class="nav-item language-switcher-nav">
              <div class="nav-link p-0">
                <language-switcher :current-language="currentLanguage" @language-change="handleLanguageChange" />
              </div>
            </li>
            
            <!-- 用户信息下拉菜单 -->
            <li class="nav-item dropdown user-menu">
              <a class="nav-link dropdown-toggle" href="#" role="button" data-bs-toggle="dropdown" aria-expanded="false" @click="toggleDropdown">
                <span class="user-info">
                  <span class="d-none d-lg-inline">{{ branchName }} | </span>
                  <span>{{ username }}</span>
                </span>
              </a>
              <ul class="dropdown-menu dropdown-menu-end">
                <li>
                  <a class="dropdown-item disabled" href="#">
                    <small class="text-muted">{{ $t('user_menu.branch_label') }}: {{ branchName }}</small>
                  </a>
                </li>
                <li>
                  <a class="dropdown-item disabled" href="#">
                    <small class="text-muted">{{ $t('user_menu.operator_label') }}: {{ username }}</small>
                  </a>
                </li>
                <li><hr class="dropdown-divider"></li>
                <li>
                  <router-link class="dropdown-item" to="/profile">
                    <font-awesome-icon :icon="['fas', 'user-edit']" /> {{ $t('user_menu.profile') }}
                  </router-link>
                </li>
                <li>
                  <a class="dropdown-item" href="#" @click.prevent="openUserManual">
                    <font-awesome-icon :icon="['fas', 'book']" /> {{ $t('common.user_manual') }}
                  </a>
                </li>
                <li>
                  <a class="dropdown-item" href="#" @click.prevent="logout">
                    <font-awesome-icon :icon="['fas', 'sign-out-alt']" /> {{ $t('user_menu.logout') }}
                  </a>
                </li>
              </ul>
            </li>
          </ul>
        </div>
      </div>
    </nav>
    
    <div class="flex-grow-1">
      <router-view />
    </div>
    
    <footer class="bg-light py-3 mt-4">
      <div class="container">
        <div class="d-flex justify-content-between align-items-center">
          <div>
            <small class="text-muted">{{ $t('footer.copyright') }} &copy; 2025</small>
          </div>
          <div>
            <small class="text-muted">{{ $t('footer.version') }}: v2.0.0</small>
          </div>
        </div>
      </div>
    </footer>
  </div>
</template>

<script>
import LanguageSwitcher from '../LanguageSwitcher.vue';
import { computed } from 'vue';
import { useRouter } from 'vue-router';

export default {
  name: 'AppLayout',
  components: {
    LanguageSwitcher
  },
  mounted() {
    // 简单的Bootstrap下拉菜单重新初始化
    this.$nextTick(() => {
      // 确保Bootstrap的下拉菜单功能正常工作
      const dropdowns = document.querySelectorAll('[data-bs-toggle="dropdown"]');
      dropdowns.forEach(dropdown => {
        // 移除可能存在的事件监听器
        dropdown.removeAttribute('data-bs-toggle');
        // 重新添加
        dropdown.setAttribute('data-bs-toggle', 'dropdown');
      });
    });

    // 添加全局点击事件来关闭下拉菜单
    document.addEventListener('click', (event) => {
      if (!event.target.closest('.dropdown')) {
        this.closeAllDropdowns();
      }
    });

    // 监听路由变化，关闭下拉菜单
    this.$router.afterEach(() => {
      this.closeAllDropdowns();
    });
  },
  setup() {
    const router = useRouter();

    const isAdmin = computed(() => {
      try {
        const userStr = localStorage.getItem('user');
        if (!userStr) {
          console.log('【权限检查】未找到用户数据');
          return false;
        }
        
        const user = JSON.parse(userStr);
        const userRole = user.role_name || user.role || '';
        const isAdminUser = ['admin', 'administrator', 'Admin', 'Administrator', '系统管理员', 'admin_role'].includes(userRole) || 
                           this.isSystemAdminRole(userRole);
        console.log('【权限检查】用户角色 (role_name):', user.role_name);
        console.log('【权限检查】用户角色 (role):', user.role);
        console.log('【权限检查】使用的角色:', userRole);
        console.log('【权限检查】是否为管理员:', isAdminUser);
        return isAdminUser;
      } catch (e) {
        console.error('【权限检查】检查管理员权限时出错:', e);
        return false;
      }
    });

    const logout = () => {
      localStorage.clear();
      router.push('/login');
    };

    // 权限检查方法
    const hasPermission = (permission) => {
      try {
        const userStr = localStorage.getItem('user');
        if (!userStr) return false;
        
        const user = JSON.parse(userStr);
        
        // admin用户拥有所有权限
        if (user.login_code === 'admin' || user.username === 'admin') {
          return true;
        }
        
        // 检查用户权限 - 使用正确的localStorage键名
        const userPermissions = JSON.parse(localStorage.getItem('userPermissions') || '[]');
        
        // 支持多种权限格式
        return userPermissions.some(p => 
          p === permission || 
          p.name === permission || 
          p.permission_name === permission
        );
      } catch (e) {
        console.error('权限检查出错:', e);
        return false;
      }
    };

    // 检查是否拥有任意一个权限
    const hasAnyPermission = (permissions) => {
      return permissions.some(permission => hasPermission(permission));
    };

    // 检查是否有任何菜单项需要显示在"更多"菜单中
    const hasAnyMenuItems = computed(() => {
      return hasPermission('balance_manage') || 
             hasPermission('end_of_day') || 
             hasPermission('reverse_transaction');
    });

    return {
      isAdmin,
      logout,
      hasPermission,
      hasAnyPermission,
      hasAnyMenuItems,
      isSystemAdminRole: (roleName) => roleName === '系统管理员'
    };
  },
  data() {
    try {
      const userStr = localStorage.getItem('user');
      const user = userStr ? JSON.parse(userStr) : {};
      console.log('Current user data:', user);
      
      return {
        username: user.username || user.name || 'admin',
        branchName: user.branch_name || this.$t('defaults.main_branch'),
        currentLanguage: localStorage.getItem('language') || 'zh',
        showadd: false
      };
    } catch (e) {
      console.error('Error in data():', e);
      return {
        username: 'admin',
        branchName: this.$t('defaults.main_branch'),
        currentLanguage: 'zh',
        showadd: false
      };
    }
  },
  methods: {
    handleLanguageChange(lang) {
      this.currentLanguage = lang;
      localStorage.setItem('language', lang);
      this.$i18n.locale = lang;
      // 不刷新页面，只更新i18n语言设置
      // window.location.reload(); // 移除页面刷新，避免跳转
    },
    toggleDropdown(event) {
      event.preventDefault();
      const dropdownToggle = event.currentTarget;
      const dropdownMenu = dropdownToggle.nextElementSibling;
      
      // 关闭其他打开的下拉菜单
      document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
        if (menu !== dropdownMenu) {
          menu.classList.remove('show');
        }
      });
      
      // 切换当前下拉菜单
      dropdownMenu.classList.toggle('show');
    },
    closeAllDropdowns() {
      document.querySelectorAll('.dropdown-menu.show').forEach(menu => {
        menu.classList.remove('show');
      });
    },
    openUserManual() {
      // 根据当前语言选择对应的PDF文件
      const languageMap = {
        'zh-CN': 'cn_ExchangeOK_help.pdf',
        'en-US': 'en_ExchangeOK_help.pdf',
        'th-TH': 'th_ExchangeOK_help.pdf'
      };
      
      const currentLang = this.$i18n.locale || 'zh-CN';
      const fileName = languageMap[currentLang] || 'cn_ExchangeOK_help.pdf';
      const filePath = `/help/${fileName}`;
      
      // 在新窗口中打开PDF文件
      window.open(filePath, '_blank');
    }
  }
};
</script>

<style scoped>
.navbar {
  padding: 0.5rem 1rem;
}

/* 增加主菜单项之间的间距，为多语言切换预留空间 */
.navbar-nav .nav-item {
  margin-right: 1.5rem; /* 从默认间距增加到1.5rem */
}

.navbar-nav .nav-item:last-child {
  margin-right: 0; /* 最后一项不需要右边距 */
}

.nav-link {
  padding: 0.5rem 1rem;
  color: rgba(255, 255, 255, 0.9) !important;
  cursor: pointer;
  white-space: nowrap; /* 防止文字换行，为多语言文本预留空间 */
}

.nav-link:hover {
  color: #fff !important;
}

/* 品牌相关样式已移除，因为品牌标识已被移除 */

.dropdown-toggle::after {
  display: inline-block;
  margin-left: 0.255em;
  vertical-align: 0.255em;
  content: "";
  border-top: 0.3em solid;
  border-right: 0.3em solid transparent;
  border-bottom: 0;
  border-left: 0.3em solid transparent;
}

.dropdown-menu {
  margin-top: 0;
  border: 1px solid rgba(0, 0, 0, 0.15);
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.175);
}

.dropdown-item {
  padding: 0.5rem 1rem;
  cursor: pointer;
}

.dropdown-item:hover {
  background-color: #f8f9fa;
}

.navbar-dark .navbar-nav .nav-link {
  color: rgba(255, 255, 255, 0.9);
}

.navbar-dark .navbar-nav .nav-link:hover {
  color: #fff;
}

.dropdown-item.active {
  background-color: #0d6efd;
  color: white;
}

.currency-flag {
  width: 24px;
  height: 16px;
  object-fit: cover;
  border-radius: 2px;
}

/* 响应式设计优化 */
@media (max-width: 1399.98px) {
  /* 中等屏幕：压缩菜单项间距 */
  .navbar-nav .nav-item {
    margin-right: 0.25rem;
  }
  
  .nav-link {
    padding: 0.5rem 0.75rem;
    font-size: 0.9rem;
  }
  
  /* 品牌标题已移除 */
}

@media (max-width: 991.98px) {
  /* 小屏幕：启用汉堡菜单 */
  .navbar-nav .nav-item {
    margin-right: 0;
    margin-bottom: 0.25rem;
  }
  
  .nav-link {
    padding: 0.75rem 1rem;
    font-size: 1rem;
  }
  
  /* 确保语言切换器在移动端可见 */
  .navbar-nav:last-child {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 0.5rem;
    margin-top: 0.5rem;
  }
}

@media (max-width: 767.98px) {
  /* 超小屏幕：进一步优化 */
  /* 品牌相关样式已移除 */
}

/* 菜单项分级显示 */
.core-menu {
  /* 核心菜单项始终显示 */
}

@media (max-width: 1399.98px) {
  /* 在中等屏幕上隐藏次要菜单项 */
  .secondary-menu {
    display: none !important;
  }
  
  /* 显示"更多"菜单 */
  .more-menu {
    display: block !important;
  }
}

@media (min-width: 1400px) {
  /* 在大屏幕上隐藏"更多"菜单 */
  .more-menu {
    display: none !important;
  }
}

/* 防止菜单项文字过长时的处理 */
.nav-link {
  transition: all 0.3s ease;
}

@media (max-width: 1399.98px) {
  .nav-link .nav-text {
    display: none;
  }
  
  .nav-link {
    padding: 0.5rem 0.75rem;
    min-width: 40px;
    text-align: center;
  }
}

@media (min-width: 1400px) {
  .nav-link .nav-text {
    display: inline;
  }
}

/* 语言切换器优化 */
.language-switcher-nav {
  min-width: 100px; /* 增加最小宽度 */
}

.language-switcher-nav .nav-link {
  padding: 0.25rem 0.75rem; /* 增加内边距 */
}

/* 用户信息下拉菜单优化 */
.user-menu .dropdown-toggle {
  max-width: 250px; /* 增加最大宽度 */
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

/* 为右侧菜单分配更多空间 */
.navbar-nav:last-child {
  margin-left: auto; /* 确保右侧对齐 */
  flex-shrink: 0; /* 防止收缩 */
}

/* 系统维护菜单优化 */
.navbar-nav .dropdown-toggle {
  white-space: nowrap; /* 防止换行 */
}

/* 移动端优化 */
@media (max-width: 991.98px) {
  .navbar-nav:last-child {
    border-top: 1px solid rgba(255, 255, 255, 0.1);
    padding-top: 0.5rem;
    margin-top: 0.5rem;
  }
  
  .language-switcher-nav,
  .user-menu {
    width: 100%;
  }
  
  .language-switcher-nav .nav-link,
  .user-menu .dropdown-toggle {
    text-align: left;
    width: 100%;
    max-width: none;
    white-space: normal;
  }
  
  .user-menu .dropdown-toggle {
    max-width: none;
    white-space: normal;
  }
}

/* 下拉菜单头部样式 */
.dropdown-header {
  font-size: 0.875rem;
  font-weight: 600;
  color: #6c757d;
  padding: 0.5rem 1rem 0.25rem;
}

/* 查询菜单下拉菜单样式优化 */
.secondary-menu .dropdown-menu {
  min-width: 280px;
  max-width: 350px;
  padding: 0.5rem 0;
  margin-top: 0.25rem;
  border: 1px solid rgba(0, 0, 0, 0.15);
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.175);
}

.secondary-menu .dropdown-item {
  padding: 0.75rem 1.25rem;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.secondary-menu .dropdown-item:hover {
  background-color: #f8f9fa;
  color: #495057;
}

/* 系统维护下拉菜单样式优化 */
.navbar-nav .dropdown-menu {
  min-width: 200px;
  max-width: 280px;
  padding: 0.5rem 0;
  margin-top: 0.25rem;
  border: 1px solid rgba(0, 0, 0, 0.15);
  box-shadow: 0 0.5rem 1rem rgba(0, 0, 0, 0.175);
}

.navbar-nav .dropdown-item {
  padding: 0.75rem 1.25rem;
  font-size: 0.9rem;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.navbar-nav .dropdown-item:hover {
  background-color: #f8f9fa;
  color: #495057;
}
</style>
