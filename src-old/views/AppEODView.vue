<template>
  <div class="app-eod-view">
    <div class="container-fluid py-3">
      <!-- 页面头部 -->
      <div class="row mb-3">
        <div class="col-12">
          <div class="d-flex justify-content-between align-items-center">
            <h4 class="mb-0 text-primary">
              <i class="fas fa-calendar-check me-2"></i>
              日结功能
            </h4>
          </div>
        </div>
      </div>

      <!-- 日结功能说明 -->
      <div class="row mb-3">
        <div class="col-12">
          <div class="card border-0 shadow-sm">
            <div class="card-body p-3">
              <div class="text-center">
                <div class="eod-icon bg-primary mb-3">
                  <i class="fas fa-calendar-check text-white"></i>
                </div>
                <h5 class="card-title">日结历史查询</h5>
                <p class="card-text text-muted">
                  查看网点日结历史记录，包括日结状态、完成时间、操作人员等信息
                </p>
                <button 
                  class="btn btn-primary btn-lg"
                  @click="goToEODHistory"
                >
                  <i class="fas fa-history me-2"></i>
                  查看日结历史
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- 功能说明 -->
      <div class="row">
        <div class="col-12">
          <div class="card border-0 shadow-sm">
            <div class="card-header bg-light py-2">
              <h6 class="mb-0">
                <i class="fas fa-info-circle text-info me-2"></i>
                功能说明
              </h6>
            </div>
            <div class="card-body p-3">
              <div class="row">
                <div class="col-6">
                  <div class="feature-item">
                    <i class="fas fa-list text-primary me-2"></i>
                    <span>历史记录</span>
                  </div>
                </div>
                <div class="col-6">
                  <div class="feature-item">
                    <i class="fas fa-search text-success me-2"></i>
                    <span>详细查询</span>
                  </div>
                </div>
                <div class="col-6">
                  <div class="feature-item">
                    <i class="fas fa-file-alt text-warning me-2"></i>
                    <span>报表查看</span>
                  </div>
                </div>
                <div class="col-6">
                  <div class="feature-item">
                    <i class="fas fa-download text-info me-2"></i>
                    <span>数据导出</span>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- App角色底部Tab导航 -->

  </div>
</template>

<script>
import { useRouter } from 'vue-router'


export default {
  name: 'AppEODView',
  components: {
  },
  setup() {
    const router = useRouter()

    const goToEODHistory = () => {
      // 跳转到日结历史页面
      router.push('/eod-history')
    }

    return {
      goToEODHistory
    }
  }
}
</script>

<style scoped>
.app-eod-view {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  min-height: 100vh;
  padding-bottom: 80px;
}

.app-eod-view .card {
  border-radius: 15px;
  border: none;
  box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
  transition: all 0.3s ease;
}

.app-eod-view .card:hover {
  transform: translateY(-2px);
  box-shadow: 0 6px 20px rgba(0, 0, 0, 0.15);
}

.eod-icon {
  width: 80px;
  height: 80px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 32px;
  margin: 0 auto;
}

.card-title {
  font-size: 1.2rem;
  font-weight: 600;
  margin-bottom: 1rem;
}

.card-text {
  font-size: 0.9rem;
  line-height: 1.5;
  margin-bottom: 1.5rem;
}

.feature-item {
  display: flex;
  align-items: center;
  padding: 0.5rem 0;
  font-size: 0.9rem;
  color: #495057;
}

/* 手机端响应式调整 */
@media (max-width: 768px) {
  .app-eod-view .container-fluid {
    padding-left: 10px;
    padding-right: 10px;
  }
  
  .app-eod-view .card-body {
    padding: 1rem;
  }
  
  .eod-icon {
    width: 60px;
    height: 60px;
    font-size: 24px;
  }
  
  .card-title {
    font-size: 1.1rem;
  }
  
  .card-text {
    font-size: 0.85rem;
  }
  
  .feature-item {
    font-size: 0.8rem;
  }
}
</style> 