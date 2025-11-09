<template>
  <div class="app-system-view">
    <div class="container-fluid py-3">
      <!-- 页面头部 -->
      <div class="row mb-3">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center">
            <h4 class="mb-0 text-primary">
              <i class="fas fa-cog me-2"></i>
              系统管理
            </h4>
            <div class="text-muted small">
              {{ formatDate(new Date()) }}
            </div>
          </div>
        </div>
      </div>

      <!-- 系统功能卡片 -->
      <div class="row">
        <div class="col-12 col-md-6 col-lg-4 mb-3">
          <div class="system-card" @click="navigateToSystem('users')">
            <div class="card-icon bg-primary">
              <i class="fas fa-users text-white"></i>
            </div>
            <div class="card-content">
              <h6 class="card-title">用户管理</h6>
              <p class="card-subtitle">管理系统用户</p>
            </div>
            <div class="card-arrow">
              <i class="fas fa-chevron-right"></i>
            </div>
          </div>
        </div>

        <div class="col-12 col-md-6 col-lg-4 mb-3">
          <div class="system-card" @click="navigateToSystem('roles')">
            <div class="card-icon bg-warning">
              <i class="fas fa-user-tag text-white"></i>
            </div>
            <div class="card-content">
              <h6 class="card-title">角色管理</h6>
              <p class="card-subtitle">管理系统角色</p>
            </div>
            <div class="card-arrow">
              <i class="fas fa-chevron-right"></i>
            </div>
          </div>
        </div>

        <div class="col-12 col-md-6 col-lg-4 mb-3">
          <div class="system-card" @click="navigateToSystem('profile')">
            <div class="card-icon bg-success">
              <i class="fas fa-user-circle text-white"></i>
            </div>
            <div class="card-content">
              <h6 class="card-title">个人信息</h6>
              <p class="card-subtitle">查看和编辑个人信息</p>
            </div>
            <div class="card-arrow">
              <i class="fas fa-chevron-right"></i>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'AppSystemView',
  methods: {
    formatDate(date) {
      return date.toLocaleDateString('zh-CN', {
        year: 'numeric',
        month: '2-digit',
        day: '2-digit'
      })
    },
    
    navigateToSystem(type) {
      // 根据系统功能类型跳转到对应的页面
      const routeMap = {
        'users': '/system/users',
        'roles': '/system/roles',
        'profile': '/profile'
      }
      
      const route = routeMap[type]
      if (route) {
        this.$router.push(route)
      }
    }
  }
}
</script>

<style scoped>
.app-system-view {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding-bottom: 80px;
  overflow-x: hidden;
}

.app-system-view .container-fluid {
  max-width: 100%;
  padding-left: 10px;
  padding-right: 10px;
}

.app-system-view .row {
  margin-left: -5px;
  margin-right: -5px;
}

.app-system-view .col-12,
.app-system-view .col-md-6,
.app-system-view .col-lg-4 {
  padding-left: 5px;
  padding-right: 5px;
}

/* 系统卡片样式 */
.system-card {
  background: white;
  border-radius: 15px;
  padding: 20px;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
  cursor: pointer;
  display: flex;
  align-items: center;
  gap: 15px;
  height: 100px;
}

.system-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.card-icon {
  width: 50px;
  height: 50px;
  border-radius: 12px;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 20px;
  flex-shrink: 0;
}

.card-content {
  flex: 1;
}

.card-title {
  font-size: 16px;
  font-weight: 600;
  color: #333;
  margin: 0 0 5px 0;
}

.card-subtitle {
  font-size: 12px;
  color: #666;
  margin: 0;
}

.card-arrow {
  color: #ccc;
  font-size: 14px;
  transition: color 0.3s ease;
}

.system-card:hover .card-arrow {
  color: #007bff;
}

/* 响应式调整 */
@media (max-width: 768px) {
  .system-card {
    padding: 15px;
    height: 80px;
  }
  
  .card-icon {
    width: 40px;
    height: 40px;
    font-size: 16px;
  }
  
  .card-title {
    font-size: 14px;
  }
  
  .card-subtitle {
    font-size: 11px;
  }
}
</style> 