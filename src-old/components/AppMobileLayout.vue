<template>
  <div class="app-mobile-layout">

    <!-- 主内容区域 -->
    <div class="mobile-content">
      <!-- 顶部导航栏 -->
      <div class="mobile-header">
        <div class="header-left">
          <button class="menu-toggle" @click="toggleMenu">
            <span class="hamburger-icon">☰</span>
          </button>
          <h4 class="page-title">ExchangeOK</h4>
        </div>
        <div class="header-right">
          <div class="language-selector">
            <button class="lang-btn" @click="toggleLanguage">
              <i class="fas fa-globe"></i>
              <span>{{ currentLanguage }}</span>
              <i class="fas fa-chevron-down"></i>
            </button>
          </div>
          <div class="user-info">
            <span class="user-name">{{ userInfo.name }}</span>
            <i class="fas fa-chevron-down"></i>
          </div>
        </div>
      </div>

      <!-- 左侧菜单 -->
      <div class="mobile-sidebar" :class="{ 'open': isMenuOpen }">
        <div class="sidebar-header">
          <div class="user-profile">
            <div class="avatar">
              <i class="fas fa-bars"></i>
            </div>
            <div class="user-details">
              <div class="user-name">{{ userInfo.name }}</div>
              <div class="user-role">{{ userInfo.role }}</div>
            </div>
          </div>
        </div>
        
        <div class="sidebar-menu">
          <!-- 所有菜单项平铺显示，不分层次 -->
          <router-link 
            v-for="item in allMenuItems" 
            :key="item.path"
            :to="item.path"
            class="menu-item"
            :class="{ 'active': $route.path === item.path }"
            @click="closeMenu"
          >
            <i :class="item.icon"></i>
            <span>{{ item.title }}</span>
          </router-link>
        </div>
        
        <div class="sidebar-footer">
          <button class="logout-btn" @click="handleLogout">
            <i class="fas fa-sign-out-alt"></i>
            <span>{{ $t('common.logout') }}</span>
          </button>
        </div>
      </div>

      <!-- 内容区域 -->
      <div class="content-area">
        <router-view />
      </div>


    </div>

    <!-- 菜单遮罩 -->
    <div 
      v-if="isMenuOpen" 
      class="menu-overlay" 
      @click="closeMenu"
    ></div>
  </div>
</template>

<script>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { useUserStore } from '../stores/user'
import { useI18n } from 'vue-i18n'

export default {
  name: 'AppMobileLayout',
  setup() {
    const router = useRouter()
    const route = useRoute()
    const userStore = useUserStore()
    const { locale, t } = useI18n()
    
    const isMenuOpen = ref(false)
    const currentTime = ref('')

    // 用户信息
    const userInfo = computed(() => ({
      name: userStore.user?.name || t('common.app_user'),
      role: t('common.app_role')
    }))

    // 页面标题
    const pageTitle = computed(() => {
      const routeMap = {
        '/app': t('common.app_home'),
        '/app/rates': t('common.rate_publish'),
        '/app/queries': t('common.query_functions'),
        '/app/eod': t('common.eod_history'),
        '/app/system': t('common.system_management')
      }
      return routeMap[route.path] || 'ExchangeOK'
    })

    // 主菜单项
    const mainMenuItems = [
      { path: '/app', title: t('common.app_home'), icon: 'fas fa-home' }
    ]

    // 查询菜单项 - 使用手机版布局的桌面版页面路由
    const queryMenuItems = [
      { path: '/app/desktop-balances', title: t('common.balance_query'), icon: 'fas fa-search' },
      { path: '/app/desktop-balance-adjust-query', title: t('common.balance_adjust_query'), icon: 'fas fa-balance-scale' },
      { path: '/app/desktop-transactions', title: t('common.transaction_query'), icon: 'fas fa-exchange-alt' },
      { path: '/app/desktop-reversal-query', title: t('common.reversal_query'), icon: 'fas fa-undo' },
      { path: '/app/desktop-foreign-stock-query', title: t('common.foreign_stock_query'), icon: 'fas fa-coins' },
      { path: '/app/desktop-local-stock-query', title: t('common.local_stock_query'), icon: 'fas fa-wallet' },
      { path: '/app/desktop-reports', title: t('common.income_query'), icon: 'fas fa-chart-bar' },
      { path: '/app/desktop-end-of-day', title: t('common.eod_history'), icon: 'fas fa-history' },
      { path: '/app/desktop-log-management', title: t('common.system_log_query'), icon: 'fas fa-file-alt' }
    ]

    // 系统菜单项 - 使用手机版布局的桌面版页面路由
    const systemMenuItems = [
      { path: '/app/desktop-system-maintenance', title: t('common.system_management'), icon: 'fas fa-cog' }
    ]

    // 所有菜单项
    const allMenuItems = [
      ...mainMenuItems,
      ...queryMenuItems,
      ...systemMenuItems
    ]

    // 当前语言
    const currentLanguage = computed(() => {
      const langMap = {
        'zh-CN': '中文',
        'en-US': 'English',
        'th-TH': 'ไทย'
      }
      return langMap[locale.value] || '中文'
    })

    // 切换语言
    const toggleLanguage = () => {
      const languages = ['zh-CN', 'en-US', 'th-TH']
      const currentIndex = languages.indexOf(locale.value)
      const nextIndex = (currentIndex + 1) % languages.length
      locale.value = languages[nextIndex]
    }


    // 更新时间
    const updateTime = () => {
      const now = new Date()
      currentTime.value = now.toLocaleTimeString('zh-CN', { 
        hour: '2-digit', 
        minute: '2-digit' 
      })
    }

    // 切换菜单
    const toggleMenu = () => {
      isMenuOpen.value = !isMenuOpen.value
    }

    // 关闭菜单
    const closeMenu = () => {
      isMenuOpen.value = false
    }

    // 退出登录
    const handleLogout = () => {
      userStore.logout()
      router.push('/login')
    }

    // 生命周期
    onMounted(() => {
      updateTime()
      const timer = setInterval(updateTime, 1000)
      onUnmounted(() => clearInterval(timer))
    })

    return {
      isMenuOpen,
      currentTime,
      userInfo,
      pageTitle,
      mainMenuItems,
      queryMenuItems,
      systemMenuItems,
      allMenuItems,
      toggleMenu,
      closeMenu,
      handleLogout,
      currentLanguage,
      toggleLanguage
    }
  }
}
</script>

<style scoped>
.app-mobile-layout {
  height: 100vh;
  display: flex;
  flex-direction: column;
  background: #f8f9fa;
}



/* 主内容区域 */
.mobile-content {
  flex: 1;
  display: flex;
  flex-direction: column;
  position: relative;
  overflow: hidden;
}

/* 顶部导航栏 */
.mobile-header {
  height: 56px;
  background: #007bff;
  color: white;
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 0 16px;
  box-shadow: none;
  z-index: 100;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 12px;
}

.menu-toggle {
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  font-size: 18px;
  padding: 8px 12px;
  cursor: pointer;
  border-radius: 6px;
  transition: all 0.3s ease;
  display: flex;
  align-items: center;
  justify-content: center;
  min-width: 40px;
  height: 40px;
}

.menu-toggle:hover {
  background: rgba(255, 255, 255, 0.2);
  transform: scale(1.05);
}

.hamburger-icon {
  font-size: 20px;
  color: white;
  font-weight: bold;
  line-height: 1;
}

.page-title {
  margin: 0;
  font-size: 18px;
  font-weight: 600;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 12px;
}

.language-selector {
  display: flex;
  align-items: center;
}

.lang-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  background: rgba(255, 255, 255, 0.1);
  border: 1px solid rgba(255, 255, 255, 0.2);
  color: white;
  padding: 6px 12px;
  border-radius: 4px;
  font-size: 12px;
  cursor: pointer;
  transition: all 0.3s ease;
}

.lang-btn:hover {
  background: rgba(255, 255, 255, 0.2);
}

.lang-btn i {
  font-size: 12px;
}

.user-info {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 8px;
}

.user-info:hover {
  background: rgba(255,255,255,0.1);
}

.user-name {
  font-size: 14px;
  font-weight: 500;
}

/* 左侧菜单 */
.mobile-sidebar {
  position: fixed;
  top: 0;
  left: -280px;
  width: 280px;
  height: 100vh;
  background: white;
  box-shadow: 2px 0 8px rgba(0,0,0,0.15);
  z-index: 1000;
  transition: left 0.3s ease;
  display: flex;
  flex-direction: column;
}

.mobile-sidebar.open {
  left: 0;
}

.sidebar-header {
  padding: 20px 16px;
  background: #007bff;
  color: white;
}

.user-profile {
  display: flex;
  align-items: center;
  gap: 12px;
}

.avatar {
  width: 50px;
  height: 50px;
  background: #007bff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  margin-right: 12px;
  border: 2px solid rgba(255, 255, 255, 0.2);
}

.avatar i {
  font-size: 20px;
  color: white;
}

.user-details .user-name {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 4px;
}

.user-details .user-role {
  font-size: 12px;
  opacity: 0.8;
}

/* 菜单内容 */
.sidebar-menu {
  flex: 1;
  padding: 16px 0;
  overflow-y: auto;
}

.menu-item {
  display: flex;
  align-items: center;
  padding: 12px 24px;
  color: #333;
  text-decoration: none;
  transition: all 0.3s ease;
  border-bottom: 1px solid #f0f0f0;
}

.menu-item:hover {
  background: #f8f9fa;
  color: #007bff;
}

.menu-item.active {
  background: #e3f2fd;
  color: #007bff;
  border-left: 4px solid #007bff;
}

.menu-item i {
  width: 20px;
  margin-right: 12px;
  font-size: 16px;
}

.menu-item span {
  font-size: 14px;
  font-weight: 500;
}

/* 菜单底部 */
.sidebar-footer {
  padding: 16px;
  border-top: 1px solid #eee;
}

.logout-btn {
  width: 100%;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 12px;
  background: #f44336;
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 500;
  cursor: pointer;
  transition: background-color 0.2s;
}

.logout-btn:hover {
  background: #d32f2f;
}

/* 内容区域 */
.content-area {
  flex: 1;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  position: relative;
  background: white;
  min-height: 100vh;
  padding-top: 20px;
}

/* 隐藏桌面版导航菜单 */
.content-area :deep(.navbar) {
  display: none !important;
}

.content-area :deep(.container-fluid) {
  padding: 0 !important;
  background: white;
}

.content-area :deep(.row) {
  margin: 0 !important;
}

.content-area :deep(.col) {
  padding: 0 !important;
}

/* 确保所有页面都使用白色背景 */
.content-area :deep(.balance-query-view),
.content-area :deep(.transaction-query-view),
.content-area :deep(.rate-management-view) {
  background: white;
  min-height: 100vh;
  padding: 0;
}

/* App首页特殊处理，允许蓝色区域 */
.content-area :deep(.app-home-view) {
  min-height: 100vh;
  padding: 0;
}

/* 白色卡片区域 */
.content-area :deep(.chart-section),
.content-area :deep(.rates-section),
.content-area :deep(.query-section),
.content-area :deep(.table-section) {
  background: white;
  border-radius: 15px;
  margin-bottom: 20px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}

/* 调整页面内容样式 */
.content-area :deep(.card) {
  border-radius: 8px;
  box-shadow: none;
  margin-bottom: 16px;
}

.content-area :deep(.card-header) {
  background: #fff;
  border-bottom: 1px solid #e9ecef;
  padding: 12px 16px;
}

.content-area :deep(.card-body) {
  padding: 16px;
}

/* 调整表格样式 */
.content-area :deep(.table) {
  font-size: 14px;
}

.content-area :deep(.table th),
.content-area :deep(.table td) {
  padding: 8px;
  vertical-align: middle;
}

/* 调整按钮样式 */
.content-area :deep(.btn) {
  font-size: 14px;
  padding: 8px 16px;
}

/* 调整表单样式 */
.content-area :deep(.form-control) {
  font-size: 14px;
  padding: 8px 12px;
}

.content-area :deep(.form-label) {
  font-size: 14px;
  font-weight: 500;
  margin-bottom: 6px;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .content-area {
    padding: 0;
  }
  
  .content-area :deep(.card-body) {
    padding: 12px;
  }
  
  .content-area :deep(.table) {
    font-size: 12px;
  }
  
  .content-area :deep(.table th),
  .content-area :deep(.table td) {
    padding: 6px;
  }
}

/* 菜单遮罩 */
.menu-overlay {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  background: rgba(0,0,0,0.5);
  z-index: 999;
}

/* 响应式调整 */
@media (max-width: 480px) {
  .mobile-sidebar {
    width: 260px;
    left: -260px;
  }
  
  .page-title {
    font-size: 16px;
  }
  
  .user-name {
    font-size: 12px;
  }
  
  .nav-item span {
    font-size: 9px;
  }
}
</style> 