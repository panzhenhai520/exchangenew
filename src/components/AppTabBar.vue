<template>
  <div class="app-tab-bar">
    <div class="tab-bar-container">
      <div 
        v-for="tab in tabs" 
        :key="tab.key"
        class="tab-item"
        :class="{ active: activeTab === tab.key }"
        @click="switchTab(tab.key)"
      >
        <div class="tab-icon">
          <i :class="tab.icon"></i>
        </div>
        <div class="tab-label">{{ tab.label }}</div>
      </div>
    </div>
  </div>
</template>

<script>
import { computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'

export default {
  name: 'AppTabBar',
  setup() {
    const router = useRouter()
    const route = useRoute()
    
    // 定义Tab配置
    const tabs = [
      {
        key: 'home',
        label: '首页',
        icon: 'fas fa-home',
        route: '/app/dashboard'
      },
      {
        key: 'rates',
        label: '汇率',
        icon: 'fas fa-chart-line',
        route: '/app/rates'
      },
      {
        key: 'queries',
        label: '查询',
        icon: 'fas fa-search',
        route: '/app/queries'
      },
      {
        key: 'eod',
        label: '日结',
        icon: 'fas fa-calendar-check',
        route: '/app/eod'
      },
      {
        key: 'system',
        label: '系统',
        icon: 'fas fa-cog',
        route: '/app/system'
      }
    ]
    
    // 根据当前路由确定活跃Tab
    const activeTab = computed(() => {
      const path = route.path
      if (path.includes('/app/dashboard')) return 'home'
      if (path.includes('/app/rates')) return 'rates'
      if (path.includes('/app/queries')) return 'queries'
      if (path.includes('/app/eod')) return 'eod'
      if (path.includes('/app/system')) return 'system'
      return 'home'
    })
    
    // 切换Tab
    const switchTab = (tabKey) => {
      const tab = tabs.find(t => t.key === tabKey)
      if (tab && tab.route !== route.path) {
        router.push(tab.route)
      }
    }
    
    return {
      tabs,
      activeTab,
      switchTab
    }
  }
}
</script>

<style scoped>
.app-tab-bar {
  position: fixed;
  bottom: 0;
  left: 0;
  right: 0;
  background: #ffffff;
  border-top: 1px solid #e0e0e0;
  box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.1);
  z-index: 1000;
}

.tab-bar-container {
  display: flex;
  justify-content: space-around;
  align-items: center;
  padding: 8px 0;
  max-width: 100%;
}

.tab-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  flex: 1;
  padding: 8px 4px;
  cursor: pointer;
  transition: all 0.3s ease;
  border-radius: 8px;
  margin: 0 2px;
}

.tab-item:hover {
  background-color: #f8f9fa;
}

.tab-item.active {
  background-color: #e3f2fd;
  color: #1976d2;
}

.tab-icon {
  font-size: 20px;
  margin-bottom: 4px;
  transition: all 0.3s ease;
}

.tab-item.active .tab-icon {
  transform: scale(1.1);
}

.tab-label {
  font-size: 12px;
  font-weight: 500;
  text-align: center;
  line-height: 1.2;
}

/* 响应式调整 */
@media (max-width: 480px) {
  .tab-icon {
    font-size: 18px;
  }
  
  .tab-label {
    font-size: 11px;
  }
  
  .tab-item {
    padding: 6px 2px;
  }
}

/* 为App角色页面添加底部间距 */
.app-dashboard-mobile {
  padding-bottom: 80px;
}
</style> 