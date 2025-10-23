<template>
  <div class="container-fluid report-list-page">
    <div class="row">
      <div class="col-12">
        <div class="d-flex justify-content-between align-items-center mb-4" style="margin-top: 20px;">
          <h2 class="page-title-bold">
            <font-awesome-icon :icon="['fas', 'list-alt']" class="me-2" />
            {{ $t('amlo.report_list.title') }}
          </h2>
          <div>
            <button
              class="btn btn-primary"
              @click="batchReportSelected"
              :disabled="selectedReports.length === 0"
            >
              <font-awesome-icon :icon="['fas', 'file-upload']" class="me-1" />
              {{ $t('amlo.report_list.batch_report') }} ({{ selectedReports.length }})
            </button>
          </div>
        </div>

        <!-- 筛选器卡片 -->
        <div class="card mb-4">
          <div class="card-header">
            <h5 class="mb-0">
              <font-awesome-icon :icon="['fas', 'filter']" class="me-2" />
              {{ $t('amlo.report_list.filters') }}
            </h5>
          </div>
          <div class="card-body">
            <div class="row g-3">
              <div class="col-md-3">
                <label class="form-label">{{ $t('amlo.report_list.report_status') }}</label>
                <select class="form-select" v-model="filters.status">
                  <option value="">{{ $t('amlo.report_list.all') }}</option>
                  <option value="pending">{{ $t('amlo.report_list.pending_report') }}</option>
                  <option value="reported">{{ $t('amlo.report_list.already_reported') }}</option>
                  <option value="overdue">{{ $t('amlo.report_list.overdue') }}</option>
                </select>
              </div>
              <div class="col-md-3">
                <label class="form-label">{{ $t('amlo.report_list.report_type') }}</label>
                <select class="form-select" v-model="filters.reportType">
                  <option value="">{{ $t('amlo.report_list.all') }}</option>
                  <option value="AMLO-1-01">{{ $t('amlo.report_list.ctr_report') }}</option>
                  <option value="AMLO-1-02">{{ $t('amlo.report_list.str_report') }}</option>
                </select>
              </div>
              <div class="col-md-3">
                <label class="form-label">{{ $t('amlo.report_list.start_date') }}</label>
                <input
                  type="date"
                  class="form-control"
                  v-model="filters.startDate"
                />
              </div>
              <div class="col-md-3">
                <label class="form-label">{{ $t('amlo.report_list.end_date') }}</label>
                <input
                  type="date"
                  class="form-control"
                  v-model="filters.endDate"
                />
              </div>
            </div>
            <div class="row mt-3">
              <div class="col-12">
                <button class="btn btn-primary me-2" @click="loadReports">
                  <font-awesome-icon :icon="['fas', 'search']" class="me-1" />
                  {{ $t('amlo.report_list.search') }}
                </button>
                <button class="btn btn-secondary" @click="resetFilters">
                  <font-awesome-icon :icon="['fas', 'redo']" class="me-1" />
                  {{ $t('amlo.report_list.reset') }}
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- 数据加载状态 -->
        <div v-if="loading" class="text-center py-5">
          <div class="spinner-border text-primary" role="status">
            <span class="visually-hidden">{{ $t('common.loading') }}</span>
          </div>
          <p class="mt-2 text-muted">{{ $t('amlo.report_list.loading') }}</p>
        </div>

        <!-- 报告列表卡片 -->
        <div v-else-if="reports.length > 0" class="card">
          <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
            <h5 class="mb-0">
              <font-awesome-icon :icon="['fas', 'table']" class="me-2" />
              {{ $t('amlo.report_list.report_list') }}
            </h5>
            <span class="badge bg-light text-primary">
              {{ $t('amlo.report_list.total_count') }}: {{ total }}
            </span>
          </div>
          <div class="card-body p-0">
            <div class="table-responsive">
              <table class="table table-hover mb-0">
                <thead class="table-light">
                  <tr>
                    <th style="width: 40px;">
                      <input
                        type="checkbox"
                        class="form-check-input"
                        :checked="isAllSelected"
                        @change="toggleSelectAll"
                      />
                    </th>
                    <th>{{ $t('amlo.report_list.reservation_no') }}</th>
                    <th>{{ $t('amlo.report_list.report_type') }}</th>
                    <th>{{ $t('amlo.report_list.customer_info') }}</th>
                    <th>{{ $t('amlo.report_list.transaction_amount') }}</th>
                    <th>{{ $t('amlo.report_list.created_at') }}</th>
                    <th>{{ $t('amlo.report_list.status') }}</th>
                    <th>{{ $t('amlo.report_list.actions') }}</th>
                  </tr>
                </thead>
                <tbody>
                  <tr
                    v-for="report in reports"
                    :key="report.id"
                    :class="{ 'table-danger': isOverdue(report) }"
                  >
                    <td>
                      <input
                        type="checkbox"
                        class="form-check-input"
                        :checked="selectedReports.includes(report.id)"
                        @change="toggleSelectReport(report.id)"
                        :disabled="report.is_reported"
                      />
                    </td>
                    <td>
                      <div class="d-flex align-items-center">
                        <strong>{{ report.reservation_no }}</strong>
                        <span
                          v-if="isOverdue(report)"
                          class="badge bg-danger ms-2"
                          :title="$t('amlo.report_list.overdue_tooltip', { days: getOverdueDays(report) })"
                        >
                          <font-awesome-icon :icon="['fas', 'exclamation-triangle']" class="me-1" />
                          {{ $t('amlo.report_list.overdue') }} ({{ getOverdueDays(report) }}{{ $t('amlo.report_list.days') }})
                        </span>
                      </div>
                    </td>
                    <td>
                      <span class="badge bg-info">{{ report.report_type }}</span>
                    </td>
                    <td>
                      <div>
                        <strong>{{ report.customer_name }}</strong>
                        <br />
                        <small class="text-muted">{{ report.customer_id }}</small>
                      </div>
                    </td>
                    <td>
                      <strong>{{ formatAmount(report.amount) }}</strong> {{ report.currency_code }}
                      <br />
                      <small class="text-muted">
                        {{ report.direction === 'buy' ? $t('exchange.buy') : $t('exchange.sell') }}
                      </small>
                    </td>
                    <td>
                      <small>{{ formatDateTime(report.created_at) }}</small>
                    </td>
                    <td>
                      <span
                        v-if="report.is_reported"
                        class="badge bg-success"
                      >
                        {{ $t('amlo.report_list.already_reported') }}
                      </span>
                      <span
                        v-else-if="isOverdue(report)"
                        class="badge bg-danger"
                      >
                        {{ $t('amlo.report_list.overdue') }}
                      </span>
                      <span
                        v-else
                        class="badge bg-warning"
                      >
                        {{ $t('amlo.report_list.pending_report') }}
                      </span>
                    </td>
                    <td>
                      <div class="btn-group" role="group">
                        <button
                          class="btn btn-sm btn-outline-primary"
                          @click="viewReport(report)"
                          :title="$t('amlo.report_list.view_details')"
                        >
                          <font-awesome-icon :icon="['fas', 'eye']" />
                        </button>
                        <button
                          class="btn btn-sm btn-outline-success"
                          @click="downloadPDF(report.id)"
                          :title="$t('amlo.report_list.download_pdf')"
                        >
                          <font-awesome-icon :icon="['fas', 'file-pdf']" />
                        </button>
                        <button
                          v-if="!report.is_reported"
                          class="btn btn-sm btn-outline-danger"
                          @click="reportSingle(report.id)"
                          :title="$t('amlo.report_list.report_now')"
                        >
                          <font-awesome-icon :icon="['fas', 'paper-plane']" />
                        </button>
                      </div>
                    </td>
                  </tr>
                </tbody>
              </table>
            </div>
          </div>

          <!-- 分页 -->
          <div class="card-footer">
            <nav aria-label="Page navigation">
              <ul class="pagination justify-content-center mb-0">
                <li class="page-item" :class="{ disabled: currentPage === 1 }">
                  <a class="page-link" href="#" @click.prevent="changePage(currentPage - 1)">
                    {{ $t('common.previous') }}
                  </a>
                </li>
                <li
                  v-for="page in totalPages"
                  :key="page"
                  class="page-item"
                  :class="{ active: page === currentPage }"
                >
                  <a class="page-link" href="#" @click.prevent="changePage(page)">{{ page }}</a>
                </li>
                <li class="page-item" :class="{ disabled: currentPage === totalPages }">
                  <a class="page-link" href="#" @click.prevent="changePage(currentPage + 1)">
                    {{ $t('common.next') }}
                  </a>
                </li>
              </ul>
            </nav>
          </div>
        </div>

        <!-- 无数据提示 -->
        <div v-else class="card">
          <div class="card-body text-center py-5">
            <font-awesome-icon :icon="['fas', 'inbox']" size="3x" class="text-muted mb-3" />
            <p class="text-muted">{{ $t('amlo.report_list.no_data') }}</p>
          </div>
        </div>
      </div>
    </div>

    <!-- 查看详情模态框 -->
    <div
      class="modal fade"
      id="reportDetailModal"
      ref="reportDetailModal"
      tabindex="-1"
    >
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ $t('amlo.report_list.report_details') }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body" v-if="selectedReport">
            <div class="row mb-3">
              <div class="col-md-6">
                <strong>{{ $t('amlo.report_list.reservation_no') }}:</strong> {{ selectedReport.reservation_no }}
              </div>
              <div class="col-md-6">
                <strong>{{ $t('amlo.report_list.report_type') }}:</strong> {{ selectedReport.report_type }}
              </div>
            </div>
            <div class="row mb-3">
              <div class="col-md-6">
                <strong>{{ $t('amlo.report_list.customer_name') }}:</strong> {{ selectedReport.customer_name }}
              </div>
              <div class="col-md-6">
                <strong>{{ $t('amlo.report_list.customer_id') }}:</strong> {{ selectedReport.customer_id }}
              </div>
            </div>
            <div class="row mb-3">
              <div class="col-md-6">
                <strong>{{ $t('amlo.report_list.transaction_amount') }}:</strong>
                {{ formatAmount(selectedReport.amount) }} {{ selectedReport.currency_code }}
              </div>
              <div class="col-md-6">
                <strong>{{ $t('amlo.report_list.direction') }}:</strong>
                {{ selectedReport.direction === 'buy' ? $t('exchange.buy') : $t('exchange.sell') }}
              </div>
            </div>
            <div class="row mb-3">
              <div class="col-12">
                <strong>{{ $t('amlo.report_list.form_data') }}:</strong>
                <pre class="bg-light p-3 mt-2">{{ formatJSON(selectedReport.form_data) }}</pre>
              </div>
            </div>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              {{ $t('common.close') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue';
import amloService from '@/services/api/amloService';
import { formatAmount, formatTransactionTime } from '@/utils/formatters';
import { Modal } from 'bootstrap';

export default {
  name: 'ReportListView',
  setup() {
    const loading = ref(false);
    const reports = ref([]);
    const total = ref(0);
    const currentPage = ref(1);
    const pageSize = ref(20);
    const selectedReports = ref([]);
    const selectedReport = ref(null);
    const reportDetailModal = ref(null);
    let modalInstance = null;

    const filters = ref({
      status: '',
      reportType: '',
      startDate: '',
      endDate: ''
    });

    // 计算总页数
    const totalPages = computed(() => {
      return Math.ceil(total.value / pageSize.value);
    });

    // 是否全选
    const isAllSelected = computed(() => {
      if (reports.value.length === 0) return false;
      const selectableReports = reports.value.filter(r => !r.is_reported);
      return selectableReports.length > 0 &&
             selectableReports.every(r => selectedReports.value.includes(r.id));
    });

    // 判断是否逾期（超过1天未上报 - 符合监管要求第64行）
    const isOverdue = (report) => {
      if (report.is_reported) return false;

      const now = new Date();
      const createdDate = new Date(report.created_at);
      const diffTime = now - createdDate;
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

      return diffDays > 1;  // 修改为1天，符合监管要求
    };

    // 获取逾期天数
    const getOverdueDays = (report) => {
      if (report.is_reported) return 0;

      const now = new Date();
      const createdDate = new Date(report.created_at);
      const diffTime = now - createdDate;
      const diffDays = Math.floor(diffTime / (1000 * 60 * 60 * 24));

      return Math.max(0, diffDays);
    };

    // 加载报告列表
    const loadReports = async () => {
      loading.value = true;
      try {
        const params = {
          page: currentPage.value,
          page_size: pageSize.value,
          ...filters.value
        };

        const response = await amloService.getReports(params);

        if (response.data.success) {
          reports.value = response.data.data.items || [];
          total.value = response.data.data.total || 0;
        } else {
          console.error('加载报告列表失败:', response.data.message);
          alert('加载报告列表失败: ' + response.data.message);
        }
      } catch (error) {
        console.error('加载报告列表出错:', error);
        alert('加载报告列表失败');
      } finally {
        loading.value = false;
      }
    };

    // 重置筛选
    const resetFilters = () => {
      filters.value = {
        status: '',
        reportType: '',
        startDate: '',
        endDate: ''
      };
      currentPage.value = 1;
      loadReports();
    };

    // 切换页码
    const changePage = (page) => {
      if (page < 1 || page > totalPages.value) return;
      currentPage.value = page;
      loadReports();
    };

    // 全选/取消全选
    const toggleSelectAll = () => {
      if (isAllSelected.value) {
        selectedReports.value = [];
      } else {
        selectedReports.value = reports.value
          .filter(r => !r.is_reported)
          .map(r => r.id);
      }
    };

    // 切换单个选择
    const toggleSelectReport = (reportId) => {
      const index = selectedReports.value.indexOf(reportId);
      if (index > -1) {
        selectedReports.value.splice(index, 1);
      } else {
        selectedReports.value.push(reportId);
      }
    };

    // 批量上报
    const batchReportSelected = async () => {
      if (selectedReports.value.length === 0) {
        alert('请至少选择一条记录');
        return;
      }

      if (!confirm(`确定要上报选中的 ${selectedReports.value.length} 条记录吗？`)) {
        return;
      }

      try {
        const response = await amloService.batchReport(selectedReports.value);

        if (response.data.success) {
          alert('批量上报成功');
          selectedReports.value = [];
          loadReports();
        } else {
          alert('批量上报失败: ' + response.data.message);
        }
      } catch (error) {
        console.error('批量上报失败:', error);
        alert('批量上报失败');
      }
    };

    // 查看报告详情
    const viewReport = (report) => {
      selectedReport.value = report;
      if (!modalInstance) {
        modalInstance = new Modal(reportDetailModal.value);
      }
      modalInstance.show();
    };

    // 下载PDF
    const downloadPDF = async (reportId) => {
      try {
        const response = await amloService.generateReportPDF(reportId);

        // 创建下载链接
        const url = window.URL.createObjectURL(new Blob([response.data]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', `AMLO_Report_${reportId}.pdf`);
        document.body.appendChild(link);
        link.click();
        link.remove();
      } catch (error) {
        console.error('下载PDF失败:', error);
        alert('下载PDF失败');
      }
    };

    // 单个上报
    const reportSingle = async (reportId) => {
      if (!confirm('确定要上报此记录吗？')) {
        return;
      }

      try {
        const response = await amloService.batchReport([reportId]);

        if (response.data.success) {
          alert('上报成功');
          loadReports();
        } else {
          alert('上报失败: ' + response.data.message);
        }
      } catch (error) {
        console.error('上报失败:', error);
        alert('上报失败');
      }
    };

    // 格式化日期时间
    const formatDateTime = (datetime) => {
      if (!datetime) return '';
      return formatTransactionTime(datetime.split('T')[0], datetime.split('T')[1]);
    };

    // 格式化JSON
    const formatJSON = (jsonData) => {
      try {
        return JSON.stringify(jsonData, null, 2);
      } catch (error) {
        return jsonData;
      }
    };

    onMounted(() => {
      loadReports();
    });

    return {
      loading,
      reports,
      total,
      currentPage,
      pageSize,
      totalPages,
      filters,
      selectedReports,
      selectedReport,
      isAllSelected,
      reportDetailModal,
      isOverdue,
      getOverdueDays,
      loadReports,
      resetFilters,
      changePage,
      toggleSelectAll,
      toggleSelectReport,
      batchReportSelected,
      viewReport,
      downloadPDF,
      reportSingle,
      formatAmount,
      formatDateTime,
      formatJSON
    };
  }
};
</script>

<style scoped>
.report-list-page {
  padding: 0 1rem;
}

.page-title-bold {
  font-weight: 700;
  color: #212529;
}

/* 逾期行红色高亮 */
.table-danger {
  background-color: #f8d7da !important;
  border-color: #f5c2c7 !important;
}

.table-danger:hover {
  background-color: #f1aeb5 !important;
}

/* 逾期徽章动画 */
.badge.bg-danger {
  animation: pulse-badge 2s infinite;
}

@keyframes pulse-badge {
  0% {
    opacity: 1;
  }
  50% {
    opacity: 0.7;
  }
  100% {
    opacity: 1;
  }
}

/* 表格样式优化 */
.table {
  font-size: 0.9rem;
}

.table th {
  background-color: #f8f9fa;
  font-weight: 600;
  border-bottom: 2px solid #dee2e6;
}

.table td {
  vertical-align: middle;
}

/* 按钮组样式 */
.btn-group {
  gap: 0.25rem;
}

/* 分页样式 */
.pagination {
  margin-top: 1rem;
}

/* JSON预览样式 */
pre {
  max-height: 300px;
  overflow-y: auto;
  border-radius: 0.375rem;
  font-size: 0.85rem;
}
</style>
