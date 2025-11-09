<template>
  <div class="container-fluid py-4">
    <div class="card">
      <div class="card-header bg-success text-white d-flex justify-content-between align-items-center">
        <h5 class="mb-0">
          <i class="fas fa-file-alt me-2"></i>
          AMLO报告管理
        </h5>
        <button class="btn btn-warning btn-sm" @click="markReported" 
                :disabled="!hasSelected"
                v-if="reports.some(r => !r.is_reported)">
          <i class="fas fa-check me-1"></i>
          标记已上报
        </button>
      </div>
      <div class="card-body">
        <!-- 筛选器 -->
        <div class="row mb-3">
          <div class="col-md-3">
            <select class="form-select" v-model="filter.report_type">
              <option value="">全部类型</option>
              <option value="AMLO-1-01">AMLO-1-01</option>
              <option value="AMLO-1-02">AMLO-1-02</option>
              <option value="AMLO-1-03">AMLO-1-03</option>
            </select>
          </div>
          <div class="col-md-3">
            <input 
              type="text" 
              class="form-control" 
              v-model="filter.customer_id"
              placeholder="客户证件号"
            />
          </div>
          <div class="col-md-2">
            <button class="btn btn-primary w-100" @click="loadReports">
              <i class="fas fa-search me-1"></i>查询
            </button>
          </div>
        </div>

        <!-- 报告列表 -->
        <div class="table-responsive">
          <table class="table table-hover">
            <thead class="table-light">
              <tr>
                <th>报告ID</th>
                <th>类型</th>
                <th>客户</th>
                <th>交易金额</th>
                <th>状态</th>
                <th>生成时间</th>
                <th>操作</th>
              </tr>
            </thead>
            <tbody>
              <tr v-if="loading">
                <td colspan="7" class="text-center py-5">
                  <div class="spinner-border text-primary" role="status">
                    <span class="visually-hidden">加载中...</span>
                  </div>
                </td>
              </tr>
              <tr v-else-if="reports.length === 0">
                <td colspan="7" class="text-center text-muted py-5">
                  暂无报告记录
                </td>
              </tr>
              <tr v-else v-for="report in reports" :key="report.id"
                  :class="getReportRowClass(report)">
                <td>
                  <input type="checkbox" v-model="report.selected" class="form-check-input me-2" v-if="!report.is_reported" />
                  {{ report.report_id || report.id }}
                </td>
                <td>
                  <span class="badge" :class="report.is_reported ? 'bg-success' : 'bg-primary'">
                    {{ report.report_type }}
                  </span>
                </td>
                <td>{{ report.customer_name }}</td>
                <td class="text-end">{{ formatAmount(report.transaction_amount) }} THB</td>
                <td>
                  <span 
                    class="badge"
                    :class="{
                      'bg-warning': !report.is_reported,
                      'bg-success': report.is_reported
                    }"
                  >
                    {{ report.is_reported ? '已上报' : '待上报' }}
                  </span>
                </td>
                <td>{{ formatDateTime(report.created_at) }}</td>
                <td>
                  <button 
                    class="btn btn-sm btn-outline-primary" 
                    @click="downloadPDF(report)"
                  >
                    <i class="fas fa-download me-1"></i>下载PDF
                  </button>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import api from '@/services/api'

export default {
  name: 'ReportListSimple',
  setup() {
    const loading = ref(false)
    const reports = ref([])
    const pagination = ref({
      total: 0,
      page: 1,
      page_size: 20,
      total_pages: 1
    })
    const hasSelected = computed(() => reports.value.some(r => r.selected))
    const filter = ref({
      report_type: '',
      customer_id: ''
    })

    const loadReports = async () => {
      loading.value = true
      try {
        const params = { ...filter.value }
        const response = await api.get('/amlo/reports', { params })
        
        if (response.data?.success) {
          const payload = response.data.data
          const items = Array.isArray(payload) ? payload : payload?.items || []
          
          reports.value = items.map(item => ({
            ...item,
            selected: false
          }))

          if (payload && !Array.isArray(payload)) {
            const total = payload.total ?? items.length
            const pageSize = payload.page_size ?? (items.length || 20)
            const totalPages = payload.total_pages ?? Math.max(1, Math.ceil(total / (pageSize || 1)))

            pagination.value = {
              total,
              page: payload.page ?? 1,
              page_size: pageSize,
              total_pages: totalPages
            }
          } else {
            pagination.value = {
              total: items.length,
              page: 1,
              page_size: items.length || 20,
              total_pages: 1
            }
          }
        } else {
          reports.value = []
        }
      } catch (error) {
        console.error('加载报告列表失败:', error)
        reports.value = []
      } finally {
        loading.value = false
      }
    }

    const downloadPDF = async (report) => {
      try {
        // 构造PDF文件路径
        const reportId = report.report_id || report.id
        const reportType = report.report_type
        const filename = `${reportType}_${reportId}.pdf`
        
        // 简化：直接打开文件
        alert(`PDF文件路径: src/manager_files/<日期>/${filename}\n\n请在文件资源管理器中查找`)
        
        // TODO: 实现实际的PDF下载逻辑
        console.log('下载PDF:', filename)
      } catch (error) {
        console.error('下载PDF失败:', error)
        alert('下载失败')
      }
    }

    const formatAmount = (amount) => {
      if (!amount) return '0.00'
      return parseFloat(amount).toLocaleString('en-US', {
        minimumFractionDigits: 2,
        maximumFractionDigits: 2
      })
    }

    const formatDateTime = (dt) => {
      if (!dt) return '-'
      return new Date(dt).toLocaleString('zh-CN')
    }

    // 获取报告行的CSS类（颜色标记）
    const getReportRowClass = (report) => {
      if (report.is_reported) {
        return '';  // 已上报：正常显示
      }
      
      // 计算天数差
      const reportDate = new Date(report.transaction_date || report.created_at);
      const today = new Date();
      const daysDiff = Math.floor((today - reportDate) / (1000 * 60 * 60 * 24));
      
      if (daysDiff > 1) {
        return 'table-danger';  // 超期未报：红色
      }
      return 'table-info';  // 未上报：蓝色
    };
    
    // 标记为已上报
    const markReported = async () => {
      const selectedIds = reports.value
        .filter(r => r.selected)
        .map(r => r.id);
      
      if (selectedIds.length === 0) {
        alert('请先选择要标记的报告');
        return;
      }
      
      if (!confirm(`确定要标记 ${selectedIds.length} 条报告为已上报吗？`)) {
        return;
      }
      
      try {
        const response = await api.post('/amlo/reports/mark-reported', {
          ids: selectedIds
        });
        
        if (response.data.success) {
          alert(`成功标记${response.data.updated_count}条报告为已上报`);
          loadReports();  // 重新加载数据
        }
      } catch (error) {
        console.error('标记失败:', error);
        alert('标记失败: ' + (error.response?.data?.message || error.message));
      }
    };

    onMounted(() => {
      loadReports()
    })

    return {
      loading,
      reports,
      pagination,
      hasSelected,
      filter,
      currentReservation: ref(null),
      detailModalRef: ref(null),
      loadReports,
      downloadPDF,
      getReportRowClass,
      markReported,
      formatAmount,
      formatDateTime
    }
  }
}
</script>

