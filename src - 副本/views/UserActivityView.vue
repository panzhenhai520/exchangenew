<template>
  <div class="container-fluid py-4">
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="page-title-bold">
        <font-awesome-icon :icon="['fas', 'user-check']" class="me-2" />
        {{ $t('logs.user_activity_monitor') }}
      </h2>
    </div>

    <!-- 功能开发提示 -->
    <div class="alert alert-info mb-4">
      <div class="d-flex align-items-center">
        <font-awesome-icon :icon="['fas', 'info-circle']" class="me-3 fa-2x" />
        <div>
          <h5 class="mb-1">用户活动监控功能</h5>
          <p class="mb-0">
            此功能正在开发中。当前系统已记录用户登录/登出信息，但详细的活动监控功能需要进一步完善。
            <br>
            <strong>已实现：</strong> 用户登录/登出记录（可在系统日志中查看）
            <br>
            <strong>开发中：</strong> 页面访问记录、操作行为监控、实时在线状态
          </p>
        </div>
      </div>
    </div>

    <!-- 快速链接 -->
    <div class="row">
      <div class="col-md-6">
        <div class="card">
          <div class="card-body text-center">
            <font-awesome-icon :icon="['fas', 'file-alt']" class="fa-3x text-primary mb-3" />
            <h5>查看系统日志</h5>
            <p class="text-muted">查看用户登录/登出和其他系统操作记录</p>
            <router-link to="/log-management" class="btn btn-primary">
              <font-awesome-icon :icon="['fas', 'external-link-alt']" class="me-1" />
              前往系统日志
            </router-link>
          </div>
        </div>
      </div>
      
      <div class="col-md-6">
        <div class="card">
          <div class="card-body text-center">
            <font-awesome-icon :icon="['fas', 'users-cog']" class="fa-3x text-success mb-3" />
            <h5>用户管理</h5>
            <p class="text-muted">管理系统用户账户和权限</p>
            <router-link to="/user-management" class="btn btn-success">
              <font-awesome-icon :icon="['fas', 'external-link-alt']" class="me-1" />
              前往用户管理
            </router-link>
          </div>
        </div>
      </div>
    </div>

    <!-- 开发计划 -->
    <div class="card mt-4">
      <div class="card-header">
        <h5 class="mb-0">
          <font-awesome-icon :icon="['fas', 'road']" class="me-2" />
          功能开发计划
        </h5>
      </div>
      <div class="card-body">
        <div class="row">
          <div class="col-md-4">
            <div class="feature-item">
              <div class="feature-status completed">
                <font-awesome-icon :icon="['fas', 'check-circle']" class="me-2" />
                已完成
              </div>
              <h6>基础日志记录</h6>
              <ul class="small text-muted">
                <li>用户登录/登出记录</li>
                <li>系统操作日志</li>
                <li>交易记录日志</li>
              </ul>
            </div>
          </div>
          
          <div class="col-md-4">
            <div class="feature-item">
              <div class="feature-status in-progress">
                <font-awesome-icon :icon="['fas', 'clock']" class="me-2" />
                开发中
              </div>
              <h6>活动监控</h6>
              <ul class="small text-muted">
                <li>实时在线状态监控</li>
                <li>页面访问统计</li>
                <li>操作行为分析</li>
              </ul>
            </div>
          </div>
          
          <div class="col-md-4">
            <div class="feature-item">
              <div class="feature-status planned">
                <font-awesome-icon :icon="['fas', 'calendar-alt']" class="me-2" />
                计划中
              </div>
              <h6>高级分析</h6>
              <ul class="small text-muted">
                <li>用户行为画像</li>
                <li>异常访问检测</li>
                <li>性能监控报表</li>
              </ul>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
export default {
  name: 'UserActivityView'
}
</script>

<style scoped>
.feature-item {
  margin-bottom: 2rem;
}

.feature-status {
  font-weight: bold;
  margin-bottom: 0.5rem;
}

.feature-status.completed {
  color: #28a745;
}

.feature-status.in-progress {
  color: #ffc107;
}

.feature-status.planned {
  color: #6c757d;
}

.card {
  border: none;
  border-radius: 10px;
  box-shadow: 0 2px 4px rgba(0,0,0,0.1);
}

.card:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 8px rgba(0,0,0,0.15);
  transition: all 0.3s ease;
}

.alert-info {
  border: none;
  background: linear-gradient(135deg, #e3f2fd 0%, #bbdefb 100%);
  border-left: 4px solid #2196f3;
}
</style> 