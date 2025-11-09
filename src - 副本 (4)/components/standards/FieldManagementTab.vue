<template>
  <div class="field-management-tab">
    <!-- 工具栏 -->
    <div class="toolbar mb-3">
      <div class="d-flex justify-content-between align-items-center">
        <div class="d-flex gap-2">
          <!-- 报告类型筛选 -->
          <select
            v-model="filters.reportType"
            class="form-select form-select-sm"
            style="width: 200px"
            @change="loadFields"
          >
            <option value="">{{ $t('compliance.allReportTypes') }}</option>
            <optgroup :label="$t('compliance.amloReports')">
              <option value="AMLO-1-01">AMLO-1-01 (CTR)</option>
              <option value="AMLO-1-02">AMLO-1-02 (ATR)</option>
              <option value="AMLO-1-03">AMLO-1-03 (STR)</option>
            </optgroup>
            <optgroup :label="$t('compliance.botReports')">
              <option value="BOT_BuyFX">BOT Buy FX</option>
              <option value="BOT_SellFX">BOT Sell FX</option>
              <option value="BOT_FCD">BOT FCD</option>
              <option value="BOT_Provider">BOT Provider</option>
            </optgroup>
          </select>

          <!-- 状态筛选 -->
          <select
            v-model="filters.isActive"
            class="form-select form-select-sm"
            style="width: 150px"
            @change="loadFields"
          >
            <option :value="undefined">{{ $t('compliance.allStatus') }}</option>
            <option :value="true">{{ $t('common.active') }}</option>
            <option :value="false">{{ $t('common.inactive') }}</option>
          </select>

          <button class="btn btn-sm btn-outline-primary" @click="loadFields">
            <font-awesome-icon :icon="['fas', 'sync']" />
            {{ $t('common.refresh') }}
          </button>
        </div>

        <button class="btn btn-sm btn-primary" @click="showCreateModal">
          <font-awesome-icon :icon="['fas', 'plus']" class="me-1" />
          {{ $t('compliance.createField') }}
        </button>
      </div>
    </div>

    <!-- 字段列表表格 -->
    <div class="table-responsive">
      <table class="table table-sm table-hover">
        <thead class="table-light">
          <tr>
            <th width="50">#</th>
            <th width="150">{{ $t('compliance.fieldName') }}</th>
            <th width="150">{{ $t('compliance.fieldLabel') }}</th>
            <th width="100">{{ $t('compliance.fieldType') }}</th>
            <th width="120">{{ $t('compliance.reportType') }}</th>
            <th width="120">{{ $t('compliance.fieldGroup') }}</th>
            <th width="80" class="text-center">{{ $t('compliance.fillOrder') }}</th>
            <th width="140">{{ $t('compliance.fillPos') }}</th>
            <th width="80" class="text-center">{{ $t('compliance.isRequired') }}</th>
            <th width="80" class="text-center">{{ $t('compliance.status') }}</th>
            <th width="150" class="text-center">{{ $t('common.action') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="11" class="text-center py-4">
              <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">{{ $t('common.loading') }}</span>
              </div>
            </td>
          </tr>
          <tr v-else-if="fields.length === 0">
            <td colspan="11" class="text-center py-4 text-muted">
              {{ $t('compliance.noFieldsFound') }}
            </td>
          </tr>
          <tr v-else v-for="(field, index) in paginatedFields" :key="field.id">
            <td>{{ (currentPage - 1) * pageSize + index + 1 }}</td>
            <td><code>{{ field.field_name }}</code></td>
            <td>{{ getFieldLabel(field) }}</td>
            <td><span class="badge" :class="getFieldTypeBadgeClass(field.field_type)">{{ field.field_type }}</span></td>
            <td><span class="badge bg-info">{{ field.report_type }}</span></td>
            <td>{{ getFieldGroup(field) }}</td>
            <td class="text-center">
              <input
                type="number"
                v-model.number="field.fill_order"
                class="form-control form-control-sm"
                style="width: 60px"
                @change="handleOrderChange(field)"
                min="1"
                max="999"
              />
            </td>
            <td>
              <code v-if="field.fillpos">{{ field.fillpos }}</code>
              <span v-else class="text-muted">-</span>
            </td>
            <td class="text-center">
              <span class="badge" :class="field.is_required ? 'bg-danger' : 'bg-secondary'">
                {{ field.is_required ? $t('common.required') : $t('common.optional') }}
              </span>
            </td>
            <td class="text-center">
              <span class="badge" :class="field.is_active ? 'bg-success' : 'bg-secondary'">
                {{ field.is_active ? $t('common.active') : $t('common.inactive') }}
              </span>
            </td>
            <td class="text-center">
              <button class="btn btn-sm btn-outline-primary me-1" @click="showEditModal(field)" :title="$t('common.edit')">
                <font-awesome-icon :icon="['fas', 'edit']" />
              </button>
              <button
                class="btn btn-sm"
                :class="field.is_active ? 'btn-outline-warning' : 'btn-outline-success'"
                @click="toggleFieldStatus(field)"
                :title="field.is_active ? $t('common.disable') : $t('common.enable')"
              >
                <font-awesome-icon :icon="['fas', field.is_active ? 'ban' : 'check']" />
              </button>
            </td>
          </tr>
        </tbody>
      </table>
    </div>

    <!-- 分页 -->
    <nav v-if="totalPages > 1" aria-label="Page navigation">
      <ul class="pagination pagination-sm justify-content-center">
        <li class="page-item" :class="{ disabled: currentPage === 1 }">
          <a class="page-link" href="#" @click.prevent="currentPage = Math.max(1, currentPage - 1)">
            {{ $t('common.previous_page') }}
          </a>
        </li>
        <li
          v-for="page in totalPages"
          :key="page"
          class="page-item"
          :class="{ active: currentPage === page }"
        >
          <a class="page-link" href="#" @click.prevent="currentPage = page">{{ page }}</a>
        </li>
        <li class="page-item" :class="{ disabled: currentPage === totalPages }">
          <a class="page-link" href="#" @click.prevent="currentPage = Math.min(totalPages, currentPage + 1)">
            {{ $t('common.next_page') }}
          </a>
        </li>
      </ul>
    </nav>

    <!-- 创建/编辑字段模态框 -->
    <div class="modal fade" id="fieldModal" tabindex="-1" ref="fieldModalRef">
      <div class="modal-dialog modal-lg modal-dialog-scrollable">
        <div class="modal-content" style="max-height: 90vh;">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ isEditMode ? $t('compliance.editField') : $t('compliance.createField') }}
            </h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <ul class="nav nav-tabs mb-3">
              <li class="nav-item">
                <button
                  class="nav-link"
                  :class="{ active: modalTab === 'basic' }"
                  @click="modalTab = 'basic'"
                  type="button"
                >
                  {{ $t('compliance.basicInfo') }}
                </button>
              </li>
              <li class="nav-item">
                <button
                  class="nav-link"
                  :class="{ active: modalTab === 'labels' }"
                  @click="modalTab = 'labels'"
                  type="button"
                >
                  {{ $t('compliance.multilingualLabels') }}
                </button>
              </li>
              <li class="nav-item">
                <button
                  class="nav-link"
                  :class="{ active: modalTab === 'validation' }"
                  @click="modalTab = 'validation'"
                  type="button"
                >
                  {{ $t('compliance.validationRules') }}
                </button>
              </li>
            </ul>

            <form>
              <!-- 基本信息Tab -->
              <div v-show="modalTab === 'basic'">
                <div class="mb-3">
                  <label class="form-label">{{ $t('compliance.fieldName') }} <span class="text-danger">*</span></label>
                  <input
                    type="text"
                    class="form-control"
                    v-model="formData.field_name"
                    :placeholder="$t('compliance.fieldNamePlaceholder')"
                    :disabled="isEditMode"
                  />
                  <small class="text-muted">{{ $t('compliance.fieldNameHelp') }}</small>
                </div>

                <div class="mb-3">
                  <label class="form-label">{{ $t('compliance.fieldType') }} <span class="text-danger">*</span></label>
                  <select class="form-select" v-model="formData.field_type">
                    <option value="VARCHAR">VARCHAR - 短文本</option>
                    <option value="TEXT">TEXT - 长文本</option>
                    <option value="INT">INT - 整数</option>
                    <option value="DECIMAL">DECIMAL - 小数</option>
                    <option value="DATE">DATE - 日期</option>
                    <option value="DATETIME">DATETIME - 日期时间</option>
                    <option value="BOOLEAN">BOOLEAN - 布尔值</option>
                    <option value="ENUM">ENUM - 枚举选择</option>
                  </select>
                </div>

                <div class="mb-3">
                  <label class="form-label">{{ $t('compliance.reportType') }} <span class="text-danger">*</span></label>
                  <select class="form-select" v-model="formData.report_type">
                    <optgroup :label="$t('compliance.amloReports')">
                      <option value="AMLO-1-01">AMLO-1-01 (CTR)</option>
                      <option value="AMLO-1-02">AMLO-1-02 (ATR)</option>
                      <option value="AMLO-1-03">AMLO-1-03 (STR)</option>
                    </optgroup>
                    <optgroup :label="$t('compliance.botReports')">
                      <option value="BOT_BuyFX">BOT Buy FX</option>
                      <option value="BOT_SellFX">BOT Sell FX</option>
                      <option value="BOT_FCD">BOT FCD</option>
                      <option value="BOT_Provider">BOT Provider</option>
                    </optgroup>
                  </select>
                </div>

                <div class="row">
                  <div class="col-md-6 mb-3">
                    <label class="form-label">{{ $t('compliance.fieldGroup') }}</label>
                    <input type="text" class="form-control" v-model="formData.field_group_cn" placeholder="中文分组名" />
                  </div>
                  <div class="col-md-6 mb-3">
                    <label class="form-label">{{ $t('compliance.fillOrder') }} <span class="text-danger">*</span></label>
                    <input type="number" class="form-control" v-model.number="formData.fill_order" min="1" max="999" />
                  </div>
                </div>

                <div class="mb-3">
                  <label class="form-label">{{ $t('compliance.fillPos') }}</label>
                  <input
                    type="text"
                    class="form-control"
                    v-model="formData.fillpos"
                    :placeholder="$t('compliance.fillPosPlaceholder')"
                  />
                  <small class="text-muted">{{ $t('compliance.fillPosHelp') }}</small>
                </div>

                <div class="mb-3">
                  <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="isRequired" v-model="formData.is_required" />
                    <label class="form-check-label" for="isRequired">{{ $t('compliance.isRequired') }}</label>
                  </div>
                </div>

                <div class="mb-3">
                  <div class="form-check form-switch">
                    <input class="form-check-input" type="checkbox" id="isActive" v-model="formData.is_active" />
                    <label class="form-check-label" for="isActive">{{ $t('compliance.status') }}</label>
                  </div>
                </div>
              </div>

              <!-- 多语言标签Tab -->
              <div v-show="modalTab === 'labels'">
                <div class="mb-3">
                  <label class="form-label">{{ $t('compliance.labelChinese') }} <span class="text-danger">*</span></label>
                  <input type="text" class="form-control" v-model="formData.field_cn_name" placeholder="中文字段名" />
                </div>

                <div class="mb-3">
                  <label class="form-label">{{ $t('compliance.labelEnglish') }}</label>
                  <input type="text" class="form-control" v-model="formData.field_en_name" placeholder="English Field Name" />
                </div>

                <div class="mb-3">
                  <label class="form-label">{{ $t('compliance.labelThai') }}</label>
                  <input type="text" class="form-control" v-model="formData.field_th_name" placeholder="ชื่อฟิลด์ภาษาไทย" />
                </div>

                <hr />

                <h6>{{ $t('compliance.fieldGroupLabels') }}</h6>
                <div class="mb-3">
                  <label class="form-label">{{ $t('compliance.groupChinese') }}</label>
                  <input type="text" class="form-control" v-model="formData.field_group_cn" placeholder="中文分组" />
                </div>

                <div class="mb-3">
                  <label class="form-label">{{ $t('compliance.groupEnglish') }}</label>
                  <input type="text" class="form-control" v-model="formData.field_group_en" placeholder="English Group" />
                </div>

                <div class="mb-3">
                  <label class="form-label">{{ $t('compliance.groupThai') }}</label>
                  <input type="text" class="form-control" v-model="formData.field_group_th" placeholder="กลุ่มภาษาไทย" />
                </div>

                <hr />

                <h6>{{ $t('compliance.placeholders') }}</h6>
                <small class="text-muted d-block mb-2">{{ $t('compliance.placeholderHelp') }}</small>
                
                <div class="row">
                  <div class="col-md-4 mb-2">
                    <label class="form-label small">中文</label>
                    <input type="text" class="form-control form-control-sm" v-model="formData.placeholder_cn" placeholder="请输入..." />
                  </div>
                  <div class="col-md-4 mb-2">
                    <label class="form-label small">English</label>
                    <input type="text" class="form-control form-control-sm" v-model="formData.placeholder_en" placeholder="Please enter..." />
                  </div>
                  <div class="col-md-4 mb-2">
                    <label class="form-label small">ไทย</label>
                    <input type="text" class="form-control form-control-sm" v-model="formData.placeholder_th" placeholder="กรุณากรอก..." />
                  </div>
                </div>
              </div>

              <!-- 验证规则Tab -->
              <div v-show="modalTab === 'validation'">
                <div class="alert alert-info">
                  <small>{{ $t('compliance.validationRulesHelp') }}</small>
                </div>

                <div v-if="formData.field_type === 'VARCHAR' || formData.field_type === 'TEXT'">
                  <div class="mb-3">
                    <label class="form-label">{{ $t('compliance.minLength') }}</label>
                    <input type="number" class="form-control" v-model.number="validationRules.min_length" min="0" />
                  </div>

                  <div class="mb-3">
                    <label class="form-label">{{ $t('compliance.maxLength') }}</label>
                    <input type="number" class="form-control" v-model.number="validationRules.max_length" min="0" />
                  </div>

                  <div class="mb-3">
                    <label class="form-label">{{ $t('compliance.pattern') }}</label>
                    <input type="text" class="form-control" v-model="validationRules.pattern" placeholder="^[A-Za-z0-9]+$" />
                    <small class="text-muted">{{ $t('compliance.patternHelp') }}</small>
                  </div>
                </div>

                <div v-if="formData.field_type === 'INT' || formData.field_type === 'DECIMAL'">
                  <div class="mb-3">
                    <label class="form-label">{{ $t('compliance.minValue') }}</label>
                    <input type="number" class="form-control" v-model.number="validationRules.min" />
                  </div>

                  <div class="mb-3">
                    <label class="form-label">{{ $t('compliance.maxValue') }}</label>
                    <input type="number" class="form-control" v-model.number="validationRules.max" />
                  </div>
                </div>

                <div v-if="formData.field_type === 'ENUM'">
                  <label class="form-label">{{ $t('compliance.enumOptions') }}</label>
                  <div v-for="(option, index) in enumOptions" :key="index" class="input-group mb-2">
                    <input
                      type="text"
                      class="form-control"
                      v-model="enumOptions[index]"
                      :placeholder="`${$t('compliance.option')} ${index + 1}`"
                    />
                    <button class="btn btn-outline-danger" type="button" @click="removeEnumOption(index)">
                      <font-awesome-icon :icon="['fas', 'trash']" />
                    </button>
                  </div>
                  <button class="btn btn-sm btn-outline-primary" @click="addEnumOption">
                    <font-awesome-icon :icon="['fas', 'plus']" class="me-1" />
                    {{ $t('compliance.addOption') }}
                  </button>
                </div>

                <hr />

                <h6>{{ $t('compliance.jsonPreview') }}</h6>
                <pre class="bg-light p-2 rounded"><code>{{ JSON.stringify(buildValidationRule(), null, 2) }}</code></pre>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeModal">{{ $t('common.cancel') }}</button>
            <button type="button" class="btn btn-primary" @click="handleSubmit">
              {{ $t('common.save') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import i18n from '@/i18n'
import complianceService from '@/services/api/complianceService'
import { Modal } from 'bootstrap'

export default {
  name: 'FieldManagementTab',
  setup() {
    const { t } = useI18n()

    const loading = ref(false)
    const fields = ref([])
    const isEditMode = ref(false)
    const currentRecord = ref(null)
    const modalTab = ref('basic')
    const fieldModalRef = ref(null)
    let modalInstance = null

    const currentPage = ref(1)
    const pageSize = ref(20)

    const filters = ref({
      reportType: '',
      isActive: undefined
    })

    const formData = ref({
      field_name: '',
      field_type: 'VARCHAR',
      report_type: 'AMLO-1-01',
      field_group_cn: '',
      field_group_en: '',
      field_group_th: '',
      fill_order: 100,
      fillpos: '',
      field_cn_name: '',
      field_en_name: '',
      field_th_name: '',
      placeholder_cn: '',
      placeholder_en: '',
      placeholder_th: '',
      help_text_cn: '',
      help_text_en: '',
      help_text_th: '',
      is_required: false,
      is_active: true,
      validation_rule: {}
    })

    const validationRules = ref({
      min_length: undefined,
      max_length: undefined,
      pattern: '',
      min: undefined,
      max: undefined
    })

    const enumOptions = ref([''])

    // 计算属性
    const totalPages = computed(() => Math.ceil(fields.value.length / pageSize.value))
    
    const paginatedFields = computed(() => {
      const start = (currentPage.value - 1) * pageSize.value
      const end = start + pageSize.value
      return fields.value.slice(start, end)
    })

    // 获取字段标签（多语言）
    const getFieldLabel = (field) => {
      const locale = i18n.global.locale.value
      if (locale === 'th-TH' || locale === 'th') {
        return field.field_th_name || field.field_cn_name || field.field_en_name
      } else if (locale === 'en-US' || locale === 'en') {
        return field.field_en_name || field.field_cn_name || field.field_th_name
      } else {
        return field.field_cn_name || field.field_en_name || field.field_th_name
      }
    }

    // 获取字段分组（多语言）
    const getFieldGroup = (field) => {
      const locale = i18n.global.locale.value
      if (locale === 'th-TH' || locale === 'th') {
        return field.field_group_th || field.field_group_cn || field.field_group_en || field.field_group || '-'
      } else if (locale === 'en-US' || locale === 'en') {
        return field.field_group_en || field.field_group_cn || field.field_group_th || field.field_group || '-'
      } else {
        return field.field_group_cn || field.field_group_en || field.field_group_th || field.field_group || '-'
      }
    }

    // 获取字段类型徽章样式
    const getFieldTypeBadgeClass = (type) => {
      const classes = {
        'VARCHAR': 'bg-primary',
        'TEXT': 'bg-info',
        'INT': 'bg-success',
        'DECIMAL': 'bg-warning',
        'DATE': 'bg-danger',
        'DATETIME': 'bg-dark',
        'BOOLEAN': 'bg-secondary',
        'ENUM': 'bg-purple'
      }
      return classes[type] || 'bg-secondary'
    }

    // 加载字段列表
    const loadFields = async () => {
      loading.value = true
      try {
        const params = {}
        if (filters.value.reportType) params.report_type = filters.value.reportType
        if (filters.value.isActive !== undefined) params.is_active = filters.value.isActive

        const response = await complianceService.getReportFields(params)
        if (response.success) {
          fields.value = response.data
          currentPage.value = 1
        } else {
          console.error('加载字段失败:', response.message)
        }
      } catch (error) {
        console.error('Load fields error:', error)
      } finally {
        loading.value = false
      }
    }

    // 显示创建模态框
    const showCreateModal = () => {
      isEditMode.value = false
      currentRecord.value = null
      resetForm()
      openModal()
    }

    // 显示编辑模态框
    const showEditModal = (record) => {
      isEditMode.value = true
      currentRecord.value = record
      Object.assign(formData.value, {
        field_name: record.field_name,
        field_type: record.field_type,
        report_type: record.report_type,
        field_group_cn: record.field_group_cn || record.field_group,
        field_group_en: record.field_group_en,
        field_group_th: record.field_group_th,
        fill_order: record.fill_order,
        fillpos: record.fillpos || '',
        field_cn_name: record.field_cn_name,
        field_en_name: record.field_en_name,
        field_th_name: record.field_th_name,
        placeholder_cn: record.placeholder_cn,
        placeholder_en: record.placeholder_en,
        placeholder_th: record.placeholder_th,
        help_text_cn: record.help_text_cn,
        help_text_en: record.help_text_en,
        help_text_th: record.help_text_th,
        is_required: record.is_required,
        is_active: record.is_active
      })

      // 解析验证规则
      if (record.validation_rule) {
        validationRules.value.min_length = record.validation_rule.min_length
        validationRules.value.max_length = record.validation_rule.max_length
        validationRules.value.pattern = record.validation_rule.pattern
        validationRules.value.min = record.validation_rule.min
        validationRules.value.max = record.validation_rule.max
        if (record.validation_rule.options) {
          enumOptions.value = [...record.validation_rule.options]
        }
      }

      openModal()
    }

    // 提交表单
    const handleSubmit = async () => {
      try {
        const submitData = {
          ...formData.value,
          validation_rule: buildValidationRule()
        }

        let response
        if (isEditMode.value) {
          response = await complianceService.updateReportField(currentRecord.value.id, submitData)
        } else {
          response = await complianceService.createReportField(submitData)
        }

        if (response.success) {
          closeModal()
          loadFields()
        } else {
          alert(response.message || t('compliance.operationFailed'))
        }
      } catch (error) {
        console.error('Submit error:', error)
        alert(t('compliance.operationFailed'))
      }
    }

    // 重置表单
    const resetForm = () => {
      formData.value = {
        field_name: '',
        field_type: 'VARCHAR',
        report_type: filters.value.reportType || 'AMLO-1-01',
        field_group_cn: '',
        field_group_en: '',
        field_group_th: '',
        fill_order: 100,
        fillpos: '',
        field_cn_name: '',
        field_en_name: '',
        field_th_name: '',
        placeholder_cn: '',
        placeholder_en: '',
        placeholder_th: '',
        help_text_cn: '',
        help_text_en: '',
        help_text_th: '',
        is_required: false,
        is_active: true
      }
      validationRules.value = {
        min_length: undefined,
        max_length: undefined,
        pattern: '',
        min: undefined,
        max: undefined
      }
      enumOptions.value = ['']
      modalTab.value = 'basic'
    }

    // 切换字段状态
    const toggleFieldStatus = async (record) => {
      if (!confirm(t('compliance.confirmToggleStatus'))) return

      try {
        const response = await complianceService.updateReportField(record.id, {
          is_active: !record.is_active
        })

        if (response.success) {
          loadFields()
        } else {
          alert(response.message || t('compliance.operationFailed'))
        }
      } catch (error) {
        console.error('Toggle status error:', error)
        alert(t('compliance.operationFailed'))
      }
    }

    // 处理顺序变化
    const handleOrderChange = async (record) => {
      try {
        const response = await complianceService.updateReportField(record.id, {
          fill_order: record.fill_order
        })

        if (!response.success) {
          alert(response.message || t('compliance.operationFailed'))
          loadFields()
        }
      } catch (error) {
        console.error('Update order error:', error)
        loadFields()
      }
    }

    // 添加枚举选项
    const addEnumOption = () => {
      enumOptions.value.push('')
    }

    // 删除枚举选项
    const removeEnumOption = (index) => {
      if (enumOptions.value.length > 1) {
        enumOptions.value.splice(index, 1)
      }
    }

    // 构建验证规则
    const buildValidationRule = () => {
      const rule = {}

      if (validationRules.value.min_length) rule.min_length = validationRules.value.min_length
      if (validationRules.value.max_length) rule.max_length = validationRules.value.max_length
      if (validationRules.value.pattern) rule.pattern = validationRules.value.pattern
      if (validationRules.value.min !== undefined) rule.min = validationRules.value.min
      if (validationRules.value.max !== undefined) rule.max = validationRules.value.max

      if (formData.value.field_type === 'ENUM' && enumOptions.value.length > 0) {
        rule.options = enumOptions.value.filter(opt => opt.trim() !== '')
      }

      return Object.keys(rule).length > 0 ? rule : null
    }

    // 模态框控制
    const openModal = () => {
      if (fieldModalRef.value) {
        modalInstance = new Modal(fieldModalRef.value)
        modalInstance.show()
      }
    }

    const closeModal = () => {
      if (modalInstance) {
        modalInstance.hide()
      }
      resetForm()
    }

    onMounted(() => {
      loadFields()
    })

    return {
      loading,
      fields,
      isEditMode,
      modalTab,
      fieldModalRef,
      filters,
      formData,
      validationRules,
      enumOptions,
      currentPage,
      pageSize,
      totalPages,
      paginatedFields,
      getFieldLabel,
      getFieldGroup,
      getFieldTypeBadgeClass,
      loadFields,
      showCreateModal,
      showEditModal,
      handleSubmit,
      closeModal,
      toggleFieldStatus,
      handleOrderChange,
      addEnumOption,
      removeEnumOption,
      buildValidationRule
    }
  }
}
</script>

<style scoped>
.field-management-tab {
  min-height: 400px;
}

.toolbar {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 4px;
}

.bg-purple {
  background-color: #6f42c1 !important;
}

/* 分页按钮样式优化 */
.pagination .page-link {
  min-width: 80px;
  white-space: nowrap;
  text-align: center;
  padding: 0.375rem 0.75rem;
}

/* 针对中文和泰语的下一页按钮宽度调整 */
.pagination .page-link:lang(zh),
.pagination .page-link:lang(th) {
  min-width: 100px;
}
</style>

