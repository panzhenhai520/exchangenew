import { createRouter, createWebHistory } from 'vue-router'
import { hasPermission } from '@/utils/permissions'
import Layout from '../components/Layout.vue'
import LoginView from '../views/LoginView.vue'
import DashboardView from '../views/DashboardView.vue'
import ExchangeView from '../views/ExchangeView.vue'
import RateManagementView from '../views/RateManagementView.vue'
import SystemMaintenanceView from '../views/SystemMaintenanceView.vue'
import UserManagementView from '../views/UserManagementView.vue'
import RoleManagementView from '../views/RoleManagementView.vue'
import UserActivityView from '../views/UserActivityView.vue'
import CurrencyManagementView from '../views/CurrencyManagementView.vue'
import ProfileView from '../views/ProfileView.vue'
import PrintLayoutEditorView from '@/views/PrintLayoutEditorView.vue'
import ExchangePurposeLimitsView from '@/views/ExchangePurposeLimitsView.vue'
import DenominationManagementView from '@/views/DenominationManagementView.vue'
import ExchangeViewWithDenominations from '@/views/ExchangeViewWithDenominations.vue'
import DualDirectionExchangeView from '@/views/DualDirectionExchangeView.vue'
import TestDenominationView from '@/views/TestDenominationView.vue'
import DenominationPublishView from '@/views/DenominationPublishView.vue'
import DenominationPreviewView from '@/views/DenominationPreviewView.vue'

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { requiresAuth: false }
  },
  {
    path: '/print-layout-editor',
    name: 'PrintLayoutEditor',
    component: PrintLayoutEditorView,
    meta: {
      requiresAuth: false,  // 独立窗口，不需要认证检查
      title: '打印布局编辑器'
    }
  },
  {
    path: '/amlo/pdf-viewer',
    name: 'AMLOPDFViewer',
    component: () => import('../views/amlo/PDFViewerWindow.vue'),
    meta: {
      requiresAuth: false,  // 独立窗口，将通过token参数验证
      title: 'AMLO PDF查看器'
    }
  },
  // App角色专用路由
  {
    path: '/app',
    component: () => import('../components/AppMobileLayout.vue'),
    meta: { requiresAuth: true, appRole: true },
    children: [
      {
        path: '',
        name: 'app-home',
        component: () => import('../views/AppHomeView.vue'),
        meta: {
          requiresAuth: true,
          appRole: true,
          title: 'App首页'
        }
      },
      {
        path: 'rates',
        name: 'app-rates',
        component: RateManagementView,
        meta: { 
          requiresAuth: true,
          appRole: true,
          permission: 'rates_manage',
          title: '汇率发布'
        }
      },
      {
        path: 'queries',
        name: 'app-queries',
        component: () => import('../views/AppQueriesView.vue'),
        meta: { 
          requiresAuth: true,
          appRole: true,
          title: '查询功能'
        }
      },
      {
        path: 'eod',
        name: 'app-eod',
        component: () => import('../views/EODHistoryView.vue'),
        meta: { 
          requiresAuth: true,
          appRole: true,
          title: '日结历史'
        }
      },
      {
        path: 'system',
        name: 'app-system',
        component: () => import('../views/AppSystemView.vue'),
        meta: { 
          requiresAuth: true,
          appRole: true,
          title: '系统管理'
        }
      },
      // 桌面版页面的手机版布局路由
      {
        path: 'desktop-balances',
        name: 'app-desktop-balances',
        component: () => import('../views/BalancesView.vue'),
        meta: { 
          requiresAuth: true,
          appRole: true,
          title: '余额查询',
          hideDesktopNav: true
        }
      },
      // 移动端PDF查看器
      {
        path: 'eod-report/:eodId',
        name: 'mobile-eod-report-viewer',
        component: () => import('../views/MobileEODReportViewer.vue'),
        meta: { 
          requiresAuth: true,
          appRole: true,
          title: '日结报表查看器'
        }
      },
      {
        path: 'desktop-balance-adjust-query',
        name: 'app-desktop-balance-adjust-query',
        component: () => import('../views/BalanceAdjustQueryView.vue'),
        meta: { 
          requiresAuth: true,
          appRole: true,
          title: '余额调节查询',
          hideDesktopNav: true
        }
      },
      {
        path: 'desktop-transactions',
        name: 'app-desktop-transactions',
        component: () => import('../views/TransactionsView.vue'),
        meta: { 
          requiresAuth: true,
          appRole: true,
          title: '交易查询',
          hideDesktopNav: true
        }
      },
      {
        path: 'desktop-reversal-query',
        name: 'app-desktop-reversal-query',
        component: () => import('../views/ReversalQueryView.vue'),
        meta: { 
          requiresAuth: true,
          appRole: true,
          title: '冲正查询',
          hideDesktopNav: true
        }
      },
      {
        path: 'desktop-foreign-stock-query',
        name: 'app-desktop-foreign-stock-query',
        component: () => import('../views/ForeignStockQueryView.vue'),
        meta: { 
          requiresAuth: true,
          appRole: true,
          title: '外币库存查询',
          hideDesktopNav: true
        }
      },
      {
        path: 'desktop-local-stock-query',
        name: 'app-desktop-local-stock-query',
        component: () => import('../views/LocalStockQueryView.vue'),
        meta: { 
          requiresAuth: true,
          appRole: true,
          title: '本币库存查询',
          hideDesktopNav: true
        }
      },
      {
        path: 'desktop-reports',
        name: 'app-desktop-reports',
        component: () => import('../views/IncomeQueryView.vue'),
        meta: { 
          requiresAuth: true,
          appRole: true,
          title: '收入查询',
          hideDesktopNav: true
        }
      },
      {
        path: 'desktop-end-of-day',
        name: 'app-desktop-end-of-day',
        component: () => import('../views/EODHistoryView.vue'),
        meta: { 
          requiresAuth: true,
          appRole: true,
          title: '日结历史',
          hideDesktopNav: true
        }
      },
      {
        path: 'desktop-log-management',
        name: 'app-desktop-log-management',
        component: () => import('../views/LogManagementView.vue'),
        meta: { 
          requiresAuth: true,
          appRole: true,
          title: '系统日志查询',
          hideDesktopNav: true
        }
      },
      {
        path: 'desktop-system-maintenance',
        name: 'app-desktop-system-maintenance',
        component: () => import('../views/SystemMaintenanceView.vue'),
        meta: { 
          requiresAuth: true,
          appRole: true,
          title: '系统管理',
          hideDesktopNav: true
        }
      }
    ]
  },
  {
    path: '/',
    component: Layout,
    children: [
      {
        path: 'dashboard',
        name: 'dashboard',
        component: DashboardView,
        meta: { requiresAuth: true }
      },
      {
        path: 'exchange',
        name: 'exchange',
        component: ExchangeView,
        meta: { 
          requiresAuth: true,
          permission: 'transaction_execute',
          title: '外币兑换'
        }
      },
      {
        path: 'exchange-with-denominations',
        name: 'exchange-with-denominations',
        component: ExchangeViewWithDenominations,
        meta: {
          requiresAuth: true,
          permission: 'transaction_execute',
          title: '面值兑换'
        }
      },
      {
        path: 'dual-direction-exchange',
        name: 'dual-direction-exchange',
        component: DualDirectionExchangeView,
        meta: {
          requiresAuth: true,
          permission: 'transaction_execute',
          title: '双向交易'
        }
      },
      {
        path: 'rates',
        name: 'rates',
        component: RateManagementView,
        meta: { 
          requiresAuth: true,
          permission: 'rate_manage',
          title: '汇率管理'
        }
      },
      {
        path: 'system-maintenance',
        name: 'system-maintenance',
        component: SystemMaintenanceView,
        meta: { requiresAuth: true, requiresAdmin: true }
      },
      {
        path: 'branch-management',
        name: 'branch-management',
        component: SystemMaintenanceView,
        meta: { 
          requiresAuth: true,
          permission: 'branch_manage',
          title: '网点管理'
        }
      },
      {
        path: 'user-management',
        name: 'user-management',
        component: UserManagementView,
        meta: { 
          requiresAuth: true,
          permission: 'user_manage',
          title: '用户管理'
        }
      },
      {
        path: 'role-management',
        name: 'role-management',
        component: RoleManagementView,
        meta: { 
          requiresAuth: true,
          permission: 'role_manage',
          title: '角色管理'
        }
      },
      {
        path: 'user-activity',
        name: 'user-activity',
        component: UserActivityView,
        meta: {
          requiresAuth: true,
          showadd: false  // 控制菜单显示
        },
        title: '用户活动监控'
      },
      {
        path: 'currency-management',
        name: 'currency-management',
        component: CurrencyManagementView,
        meta: { 
          requiresAuth: true,
          permission: 'currency_manage',
          title: '币种管理'
        }
      },
      {
        path: 'initial-balance',
        name: 'initialBalance',
        component: () => import('../views/InitialBalanceView.vue'),
        meta: { 
          requiresAuth: true,
          permission: 'balance_manage',
          title: '期初余额设置'
        }
      },
      {
        path: 'adjust-balance',
        name: 'adjustBalance',
        component: () => import('../views/AdjustBalanceView.vue'),
        meta: { 
          requiresAuth: true,
          permission: 'balance_manage',
          title: '余额调节'
        }
      },
      {
        path: 'end-of-day',
        name: 'end-of-day',
        component: () => import('../views/EndOfDayView.vue'),
        meta: { 
          requiresAuth: true,
          permission: 'end_of_day',
          title: '日终处理'
        }
      },
      {
        path: 'eod-history',
        name: 'eod-history',
        component: () => import('../views/EODHistoryView.vue'),
        meta: { 
          requiresAuth: true,
          permission: 'end_of_day',
          title: '日结历史'
        }
      },
      {
        path: 'eod-history-detail/:id',
        name: 'EODHistoryDetail',
        component: () => import('../views/EODHistoryDetailView.vue'),
        meta: { 
          requiresAuth: true,
          permission: 'end_of_day',
          title: '日结历史详情'
        }
      },
      {
        path: 'eod-report-viewer/:eodId',
        name: 'EODReportViewer',
        component: () => import('../views/EODReportViewer.vue'),
        meta: { 
          requiresAuth: true,
          permission: 'end_of_day',
          title: '日结报表查看'
        }
      },
      {
        path: 'cash-handover',
        name: 'cash-handover',
        component: () => import('../views/CashHandoverView.vue')
      },
      {
        path: 'reversal',
        name: 'reversal',
        component: () => import('../views/ReversalView.vue'),
        meta: { 
          requiresAuth: true,
          permission: 'reverse_transaction',
          title: '交易冲正'
        }
      },

      {
        path: 'log-management',
        name: 'log-management',
        component: () => import('../views/LogManagementView.vue'),
        meta: { 
          requiresAuth: true,
          permission: 'log_view',
          title: '系统日志'
        }
      },
      {
        path: 'transactions',
        name: 'transactions',
        component: () => import('../views/TransactionsView.vue'),
        meta: { 
          requiresAuth: true,
          permission: 'view_transactions',
          title: '交易查询'
        }
      },
      {
        path: 'balances',
        name: 'balances',
        component: () => import('../views/BalancesView.vue'),
        meta: { 
          requiresAuth: true,
          permission: 'view_balances',
          title: '余额查询'
        }
      },
      {
        path: 'reversal-query',
        name: 'reversal-query',
        component: () => import('../views/ReversalQueryView.vue'),
        meta: { 
          requiresAuth: true,
          permission: 'reverse_transaction',
          title: '冲正查询'
        }
      },
      {
        path: 'balance-adjust-query',
        name: 'balance-adjust-query',
        component: () => import('../views/BalanceAdjustQueryView.vue'),
        meta: { 
          requiresAuth: true,
          permission: 'balance_manage',
          title: '余额调节查询'
        }
      },
      {
        path: 'profile',
        name: 'profile',
        component: ProfileView,
        meta: { requiresAuth: true }
      },
      {
        path: 'system/exchange-purpose-limits',
        name: 'ExchangePurposeLimits',
        component: ExchangePurposeLimitsView,
        meta: { 
          requiresAuth: true, 
          permission: 'system_manage',
          title: '兑换提示信息维护' 
        }
      },
      {
        path: 'system/print-settings',
        name: 'print-settings',
        component: () => import('../views/PrintSettingsViewModular.vue'),
        meta: {
          requiresAuth: true,
          showadd: false  // 控制菜单显示
        },
        title: '打印单据设置'
      },
      {
        path: 'system/denomination-management',
        name: 'denomination-management',
        component: DenominationManagementView,
        meta: { 
          requiresAuth: true, 
          permission: 'system_manage',
          title: '面值管理' 
        }
      },
      {
        path: 'system/denomination-publish',
        name: 'denomination-publish',
        component: DenominationPublishView,
        meta: { 
          requiresAuth: true, 
          permission: 'rate_manage',
          title: '面值汇率发布' 
        }
      },
      {
        path: 'system/denomination-preview',
        name: 'denomination-preview',
        component: DenominationPreviewView,
        meta: { 
          requiresAuth: true, 
          permission: 'rate_manage',
          title: '面值汇率预览' 
        }
      },
      {
        path: 'standards-management',
        name: 'standards-management',
        component: () => import('../views/StandardsManagementView.vue'),
        meta: {
          requiresAuth: true,
          permission: 'branch_manage',
          title: '规范管理'
        }
      },
      {
        path: 'test-denomination',
        name: 'test-denomination',
        component: TestDenominationView,
        meta: { 
          requiresAuth: true,
          title: '面值功能测试'
        }
      },
      {
        path: 'income-query',
        name: 'income-query',
        component: () => import('../views/IncomeQueryView.vue'),
        meta: {
          requiresAuth: true,
          permission: 'view_transactions',
          title: '动态收入查询'
        }
      },
      // AMLO/BOT合规报告模块
      {
        path: 'amlo/reservations',
        name: 'AMLOReservations',
        component: () => import('../views/amlo/ReservationListSimple.vue'),  // 使用Bootstrap简化版
        meta: {
          requiresAuth: true,
          permission: 'amlo_reservation_view',
          title: 'AMLO预约查询'
        }
      },
      {
        path: 'amlo/reports',
        name: 'AMLOReports',
        component: () => import('../views/amlo/ReportListSimple.vue'),  // 使用Bootstrap简化版
        meta: {
          requiresAuth: true,
          permission: 'amlo_report_view',
          title: 'AMLO报告管理'
        }
      },
      {
        path: 'amlo/signature-test',
        name: 'SignaturePadTest',
        component: () => import('../views/amlo/SignaturePadTest.vue'),
        meta: {
          requiresAuth: true,
          title: '签字板测试'
        }
      },
      {
        path: 'bot/reports',
        name: 'BOTReports',
        component: () => import('../views/bot/BOTReportSimple.vue'),  // 使用Bootstrap简化版
        meta: {
          requiresAuth: true,
          permission: 'bot_report_view',
          title: 'BOT报表查询'
        }
      },
      {
        path: 'bot/t1-submit',
        name: 'BOTT1Submit',
        component: () => import('../views/bot/T1SubmitView.vue'),
        meta: {
          requiresAuth: true,
          permission: 'bot_report_export',
          title: 'BOT T+1上报'
        }
      },
      {
        path: 'foreign-stock-query',
        name: 'foreign-stock-query',
        component: () => import('../views/ForeignStockQueryView.vue'),
        meta: { 
          requiresAuth: true,
          permission: 'view_balances',
          title: '外币库存查询'
        }
      },
      {
        path: 'local-stock-query',
        name: 'local-stock-query',
        component: () => import('../views/LocalStockQueryView.vue'),
        meta: { 
          requiresAuth: true,
          permission: 'view_balances',
          title: '本币库存查询'
        }
      },
      {
        path: 'data-clear',
        name: 'data-clear',
        component: () => import('../views/DataClearView.vue'),
        meta: { 
          requiresAuth: true,
          permission: 'system_manage',
          title: '清空营业数据'
        }
      }
    ]
  }
]

const router = createRouter({
  history: createWebHistory(),
  routes
})

// 路由守卫
router.beforeEach((to, from, next) => {
  console.log(`🚀 路由导航: ${from.path} -> ${to.path}`)
  console.log(`📋 路由元信息:`, to.meta)
  
  // 检查token是否有效
  const token = localStorage.getItem('token')
  let isAuthenticated = false
  
  if (token) {
    try {
      // 简单的token格式检查（JWT格式）
      const parts = token.split('.')
      if (parts.length === 3) {
        // 检查token是否过期
        const payload = JSON.parse(atob(parts[1]))
        const currentTime = Math.floor(Date.now() / 1000)
        if (payload.exp && payload.exp > currentTime) {
          isAuthenticated = true
        } else {
          console.warn('⚠️ Token已过期，清除认证信息')
          localStorage.clear()
          sessionStorage.clear()
        }
      } else {
        console.warn('⚠️ Token格式无效，清除认证信息')
        localStorage.clear()
        sessionStorage.clear()
      }
    } catch (error) {
      console.warn('⚠️ Token解析失败，清除认证信息:', error)
      localStorage.clear()
      sessionStorage.clear()
    }
  }
  
  console.log(`🔐 认证状态: ${isAuthenticated}`)
  
  // 检查是否需要登录
  if (to.meta.requiresAuth && !isAuthenticated) {
    console.warn('❌ 需要登录，重定向到登录页')
    next('/login')
    return
  }
  
  // 如果已登录但访问登录页，根据用户角色重定向
  if (to.path === '/login' && isAuthenticated) {
    console.warn('❌ 已登录用户访问登录页，重定向到仪表盘')
    // 检查用户角色
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    if (user.role_name === 'App' || user.role_name === 'APP') {
      next('/app')
    } else {
      next('/dashboard')
    }
    return
  }
  
  // 检查App角色路由权限
  if (to.meta.appRole && isAuthenticated) {
    const user = JSON.parse(localStorage.getItem('user') || '{}')
    if (user.role_name !== 'App' && user.role_name !== 'APP') {
      console.warn('❌ 非App角色访问App专用路由，重定向到仪表盘')
      next('/dashboard')
      return
    }
  }
  
  // 检查页面权限
  if (to.meta.permission && isAuthenticated) {
    console.log(`🔍 检查权限: ${to.meta.permission}`)
    const hasPerm = hasPermission(to.meta.permission)
    console.log(`📊 权限检查结果: ${hasPerm}`)

    if (!hasPerm) {
      console.warn(`❌ 权限不足: 缺少 ${to.meta.permission} 权限`)

      // 避免重定向循环：如果目标就是dashboard，则不再重定向
      if (to.path === '/dashboard') {
        console.log('✅ 目标是dashboard，允许访问')
        next()
        return
      }

      // 权限不足，根据用户角色重定向
      const user = JSON.parse(localStorage.getItem('user') || '{}')
      console.warn(`⚠️ 权限不足，重定向用户 (角色: ${user.role_name})`)

      if (user.role_name === 'App' || user.role_name === 'APP') {
        next('/app')
      } else {
        next('/dashboard')
      }
      return
    }
  }
  
  console.log('✅ 路由检查通过，允许导航')
  next()
})

// 路由后置守卫 - 完全禁用，避免任何问题
router.afterEach(() => {
  // 日志功能已禁用，确保路由正常工作
})

export default router
