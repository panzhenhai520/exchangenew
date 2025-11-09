<template>
  <div class="trigger-rules-tab">
    <!-- 工具栏 -->
    <div class="toolbar mb-3">
      <div class="d-flex justify-content-between align-items-center">
        <div class="d-flex gap-2">
          <!-- 报告类型筛选 -->
          <select
            v-model="filters.reportType"
            class="form-select form-select-sm"
            style="width: 200px"
            @change="loadRules"
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
            @change="loadRules"
          >
            <option :value="undefined">{{ $t('compliance.allStatus') }}</option>
            <option :value="true">{{ $t('common.active') }}</option>
            <option :value="false">{{ $t('common.inactive') }}</option>
          </select>

          <button class="btn btn-sm btn-outline-primary" @click="loadRules">
            <font-awesome-icon :icon="['fas', 'sync']" />
            {{ $t('common.refresh') }}
          </button>
        </div>

        <button class="btn btn-sm btn-primary" @click="showCreateModal">
          <font-awesome-icon :icon="['fas', 'plus']" class="me-1" />
          {{ $t('compliance.createRule') }}
        </button>
      </div>
    </div>

    <!-- 规则列表表格 -->
    <div class="table-responsive">
      <table class="table table-sm table-hover">
        <thead class="table-light">
          <tr>
            <th width="50">#</th>
            <th width="200">{{ $t('compliance.ruleName') }}</th>
            <th width="120">{{ $t('compliance.reportType') }}</th>
            <th width="80" class="text-center">{{ $t('compliance.priority') }}</th>
            <th width="250">{{ $t('compliance.description') }}</th>
            <th width="100" class="text-center">{{ $t('compliance.allowContinue') }}</th>
            <th width="80" class="text-center">{{ $t('compliance.status') }}</th>
            <th width="150" class="text-center">{{ $t('common.action') }}</th>
          </tr>
        </thead>
        <tbody>
          <tr v-if="loading">
            <td colspan="8" class="text-center py-4">
              <div class="spinner-border spinner-border-sm" role="status">
                <span class="visually-hidden">{{ $t('common.loading') }}</span>
              </div>
            </td>
          </tr>
          <tr v-else-if="rules.length === 0">
            <td colspan="8" class="text-center py-4 text-muted">
              {{ $t('compliance.noRulesFound') }}
            </td>
          </tr>
          <tr v-else v-for="(rule, index) in paginatedRules" :key="rule.id">
            <td>{{ (currentPage - 1) * pageSize + index + 1 }}</td>
            <td>{{ getRuleName(rule) }}</td>
            <td><span class="badge" :class="getReportTypeBadgeClass(rule.report_type)">{{ rule.report_type }}</span></td>
            <td class="text-center">
              <span class="badge" :class="getPriorityBadgeClass(rule.priority)">{{ rule.priority }}</span>
            </td>
            <td>
              <span class="text-truncate d-inline-block" style="max-width: 250px" :title="getDescription(rule)">
                {{ getDescription(rule) }}
              </span>
            </td>
            <td class="text-center">
              <span class="badge" :class="rule.allow_continue ? 'bg-success' : 'bg-warning'">
                {{ rule.allow_continue ? $t('common.yes') : $t('common.no') }}
              </span>
            </td>
            <td class="text-center">
              <span class="badge" :class="rule.is_active ? 'bg-success' : 'bg-secondary'">
                {{ rule.is_active ? $t('common.active') : $t('common.inactive') }}
              </span>
            </td>
            <td class="text-center">
              <button class="btn btn-sm btn-outline-primary me-1" @click="showEditModal(rule)" :title="$t('common.edit')">
                <font-awesome-icon :icon="['fas', 'edit']" />
              </button>
              <button
                class="btn btn-sm"
                :class="rule.is_active ? 'btn-outline-warning' : 'btn-outline-success'"
                @click="toggleRuleStatus(rule)"
                :title="rule.is_active ? $t('common.disable') : $t('common.enable')"
              >
                <font-awesome-icon :icon="['fas', rule.is_active ? 'ban' : 'check']" />
              </button>
              <button
                class="btn btn-sm btn-outline-danger ms-1"
                @click="deleteRule(rule)"
                :title="$t('common.delete')"
              >
                <font-awesome-icon :icon="['fas', 'trash']" />
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

    <!-- 创建/编辑规则模态框 -->
    <div class="modal fade" id="ruleModal" tabindex="-1" ref="ruleModalRef">
      <div class="modal-dialog modal-xl modal-dialog-scrollable" style="max-width: 98vw;">
        <div class="modal-content" style="max-height: 95vh;">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ isEditMode ? $t('compliance.editRule') : $t('compliance.createRule') }}
            </h5>
            <button type="button" class="btn-close" @click="closeModal"></button>
          </div>
          <div class="modal-body">
            <form>
              <!-- 规则名称 - 多语言折叠 -->
              <div class="mb-3">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <label class="form-label mb-0">{{ $t('compliance.ruleName') }} <span class="text-danger">*</span></label>
                  <button type="button" class="btn btn-sm btn-outline-secondary" @click="toggleRuleNameCollapse">
                    <font-awesome-icon :icon="['fas', ruleNameCollapsed ? 'chevron-down' : 'chevron-up']" class="me-1" />
                    {{ ruleNameCollapsed ? '展开多语言' : '折叠多语言' }}
                  </button>
                </div>
                
                <div v-if="!ruleNameCollapsed" class="row g-2">
                  <div class="col-md-4">
                    <label class="form-label form-label-sm">{{ $t('compliance.ruleNameChinese') }} <span class="text-danger">*</span></label>
                    <input type="text" class="form-control form-control-sm" v-model="formData.rule_name" placeholder="中文规则名称" />
                  </div>
                  <div class="col-md-4">
                    <label class="form-label form-label-sm">{{ $t('compliance.ruleNameEnglish') }}</label>
                    <input type="text" class="form-control form-control-sm" v-model="formData.rule_name_en" placeholder="English Rule Name" />
                  </div>
                  <div class="col-md-4">
                    <label class="form-label form-label-sm">{{ $t('compliance.ruleNameThai') }}</label>
                    <input type="text" class="form-control form-control-sm" v-model="formData.rule_name_th" placeholder="ชื่อกฎภาษาไทย" />
                  </div>
                </div>
                <div v-else class="form-control form-control-sm bg-light">
                  {{ formData.rule_name || '未设置规则名称' }}
                </div>
              </div>

              <!-- 基本信息 - 横向布局 -->
              <div class="row g-2 mb-3">
                <div class="col-md-6">
                  <label class="form-label form-label-sm">{{ $t('compliance.reportType') }} <span class="text-danger">*</span></label>
                  <select class="form-select form-select-sm" v-model="formData.report_type">
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
                <div class="col-md-3">
                  <label class="form-label form-label-sm">{{ $t('compliance.priority') }} <span class="text-danger">*</span></label>
                  <input type="number" class="form-control form-control-sm" v-model.number="formData.priority" placeholder="100" />
                  <small class="text-muted">数字越大优先级越高</small>
                </div>
                <div class="col-md-3">
                  <label class="form-label form-label-sm">{{ $t('compliance.allowContinue') }}</label>
                  <div class="form-check form-switch mt-2">
                    <input class="form-check-input" type="checkbox" id="allowContinue" v-model="formData.allow_continue" />
                    <label class="form-check-label form-label-sm" for="allowContinue">{{ $t('compliance.allowContinue') }}</label>
                  </div>
                </div>
              </div>

              <!-- 描述和警告消息 - 横向布局 -->
              <div class="row g-2 mb-3">
                <div class="col-md-6">
                  <label class="form-label form-label-sm">{{ $t('compliance.description') }}</label>
                  <textarea class="form-control form-control-sm" v-model="formData.description_cn" rows="2" placeholder="规则描述..."></textarea>
                </div>
                <div class="col-md-6">
                  <label class="form-label form-label-sm">{{ $t('compliance.warningMessage') }}</label>
                  <textarea class="form-control form-control-sm" v-model="formData.message_cn" rows="2" placeholder="触发时的警告消息..."></textarea>
                </div>
              </div>

              <!-- 高级模式规则构建器 -->
              <div class="mb-3">
                <div class="d-flex justify-content-between align-items-center mb-2">
                  <label class="form-label mb-0">{{ $t('compliance.ruleExpression') }} <span class="text-danger">*</span></label>
                  <button type="button" class="btn btn-sm btn-outline-success" @click="addCondition">
                    <font-awesome-icon :icon="['fas', 'plus']" class="me-1" />
                    {{ $t('compliance.addCondition') }}
                  </button>
                </div>
                
                <div class="rule-builder p-3 border rounded bg-light">
                  <div class="alert alert-info alert-sm mb-2">
                    <small>{{ $t('compliance.ruleExpressionHelp') }}</small>
                  </div>

                  <!-- 逻辑运算符选择 -->
                  <div class="mb-2">
                    <label class="form-label form-label-sm">{{ $t('compliance.logicOperator') }}</label>
                    <div class="btn-group btn-group-sm" role="group">
                      <input
                        type="radio"
                        class="btn-check"
                        id="logicAND"
                        value="AND"
                        v-model="ruleLogic"
                      />
                      <label class="btn btn-outline-primary" for="logicAND">AND</label>

                      <input
                        type="radio"
                        class="btn-check"
                        id="logicOR"
                        value="OR"
                        v-model="ruleLogic"
                      />
                      <label class="btn btn-outline-primary" for="logicOR">OR</label>
                    </div>
                  </div>

                  <!-- 条件列表 - 优化布局 -->
                  <div class="conditions-list">
                    <div v-for="(condition, index) in ruleConditions" :key="index" class="condition-item mb-2 p-2 border rounded bg-white">
                      <div class="d-flex justify-content-between align-items-center mb-1">
                        <small class="text-muted">条件 {{ index + 1 }}</small>
                        <button 
                          type="button" 
                          class="btn btn-sm btn-outline-danger" 
                          @click="removeCondition(index)"
                          :disabled="ruleConditions.length === 1"
                        >
                          <font-awesome-icon :icon="['fas', 'trash']" />
                        </button>
                      </div>
                      
                      <!-- 字段搜索区域 -->
                      <div v-if="fieldSearchVisible" class="mb-3">
                        <div class="input-group input-group-sm">
                          <span class="input-group-text">
                            <font-awesome-icon :icon="['fas', 'search']" />
                          </span>
                          <input 
                            type="text" 
                            class="form-control field-search-input" 
                            v-model="fieldSearchQuery"
                            placeholder="搜索字段名称、分组或代码..."
                            @input="fieldSearchQuery = $event.target.value"
                          />
                          <button 
                            class="btn btn-outline-secondary" 
                            type="button"
                            @click="fieldSearchQuery = ''"
                            title="清空搜索"
                          >
                            <font-awesome-icon :icon="['fas', 'times']" />
                          </button>
                        </div>
                        <small class="text-muted">
                          <font-awesome-icon :icon="['fas', 'info-circle']" class="me-1" />
                          找到 {{ filteredFieldOptions.length }} 个字段
                          <span v-if="fieldSearchQuery" class="ms-2">
                            (搜索: "{{ fieldSearchQuery }}")
                          </span>
                        </small>
                      </div>

                      <div class="row g-2 align-items-end">
                        <div class="col-lg-4 col-md-6">
                          <div class="d-flex justify-content-between align-items-center mb-1">
                            <label class="form-label form-label-sm mb-0">字段</label>
                            <button 
                              type="button" 
                              class="btn btn-sm btn-outline-info" 
                              @click="fieldSearchVisible = !fieldSearchVisible"
                              :title="fieldSearchVisible ? '隐藏搜索 (ESC)' : '显示搜索 (Ctrl+F)'"
                            >
                              <font-awesome-icon :icon="['fas', fieldSearchVisible ? 'search-minus' : 'search']" />
                            </button>
                          </div>
                          
                          <select
                            v-model="condition.field"
                            class="form-select form-select-sm"
                            @change="onFieldChange(condition)"
                          >
                            <option value="">{{ $t('compliance.selectField') }}</option>
                            <optgroup 
                              v-for="group in groupedFieldOptions" 
                              :key="group.name" 
                              :label="group.label"
                            >
                              <option 
                                v-for="field in group.fields" 
                                :key="field.field_name" 
                                :value="field.field_name"
                              >
                                {{ getFieldDisplayName(field) }}
                              </option>
                            </optgroup>
                          </select>
                          
                          <!-- 显示当前选中字段的名称 -->
                          <div v-if="condition.field" class="mt-1">
                            <small class="text-muted">
                              当前字段: {{ getFieldDisplayName(getFieldByFieldName(condition.field)) }}
                            </small>
                          </div>
                        </div>

                        <div class="col-lg-2 col-md-3">
                          <label class="form-label form-label-sm mb-1">操作符</label>
                          <select v-model="condition.operator" class="form-select form-select-sm">
                            <option value="=">=</option>
                            <option value="!=">!=</option>
                            <option value=">=">&gt;=</option>
                            <option value="<=">&lt;=</option>
                            <option value=">">&gt;</option>
                            <option value="<">&lt;</option>
                          </select>
                        </div>

                        <div class="col-lg-4 col-md-6">
                          <label class="form-label form-label-sm mb-1">值</label>
                          <!-- 布尔值字段 -->
                          <select
                            v-if="isBooleanField(condition.field)"
                            v-model="condition.value"
                            class="form-select form-select-sm"
                          >
                            <option value="true">{{ $t('common.yes') }}</option>
                            <option value="false">{{ $t('common.no') }}</option>
                          </select>
                          <!-- 交易方向字段 -->
                          <select
                            v-else-if="condition.field === 'direction'"
                            v-model="condition.value"
                            class="form-select form-select-sm"
                          >
                            <option value="buy">{{ $t('transaction.buy') }}</option>
                            <option value="sell">{{ $t('transaction.sell') }}</option>
                          </select>
                          <!-- 支付方式字段 -->
                          <select
                            v-else-if="condition.field === 'payment_method'"
                            v-model="condition.value"
                            class="form-select form-select-sm"
                          >
                            <option value="cash">{{ $t('standards.trigger.cash') }}</option>
                            <option value="instrument_cheque">{{ $t('standards.trigger.instrument_cheque') }}</option>
                            <option value="instrument_draft">{{ $t('standards.trigger.instrument_draft') }}</option>
                            <option value="instrument_other">{{ $t('standards.trigger.instrument_other') }}</option>
                            <option value="other">{{ $t('standards.trigger.other_method') }}</option>
                          </select>
                          <!-- 普通输入 -->
                          <input
                            v-else
                            type="text"
                            class="form-control form-control-sm"
                            v-model="condition.value"
                            :placeholder="getFieldPlaceholder(condition.field)"
                          />
                        </div>

                        <div class="col-lg-2 col-md-3 d-flex align-items-end">
                          <button 
                            type="button" 
                            class="btn btn-sm btn-outline-danger w-100" 
                            @click="removeCondition(index)"
                            :disabled="ruleConditions.length === 1"
                          >
                            <font-awesome-icon :icon="['fas', 'trash']" />
                          </button>
                        </div>
                      </div>
                    </div>
                  </div>

                  <!-- JSON预览 -->
                  <div class="json-preview mt-2 p-2 bg-light rounded">
                    <small class="text-muted">{{ $t('compliance.jsonPreview') }}:</small>
                    <pre class="mb-0 mt-1 small"><code>{{ JSON.stringify(buildRuleExpression(), null, 2) }}</code></pre>
                  </div>
                </div>
              </div>

              <!-- 状态 -->
              <div class="mb-3">
                <div class="form-check form-switch">
                  <input class="form-check-input" type="checkbox" id="ruleActive" v-model="formData.is_active" />
                  <label class="form-check-label" for="ruleActive">{{ $t('compliance.activeRule') }}</label>
                </div>
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
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { useI18n } from 'vue-i18n'
import i18n from '@/i18n'
import complianceService from '@/services/api/complianceService'
import { Modal } from 'bootstrap'

export default {
  name: 'TriggerRulesTab',
  setup() {
    const { t } = useI18n()

    const loading = ref(false)
    const rules = ref([])
    const isEditMode = ref(false)
    const currentRecord = ref(null)
    const ruleModalRef = ref(null)
    let modalInstance = null

    // 折叠状态
    const ruleNameCollapsed = ref(true)  // 默认折叠多语言字段

    // 切换规则名称折叠状态
    const toggleRuleNameCollapse = () => {
      ruleNameCollapsed.value = !ruleNameCollapsed.value
    }

    const currentPage = ref(1)
    const pageSize = ref(10)
    
    // 字段选项（从字段定义API加载）
    const fieldOptions = ref([])
    
    // 字段搜索
    const fieldSearchQuery = ref('')
    const fieldSearchVisible = ref(false)

    const filters = ref({
      reportType: '',
      isActive: undefined
    })

    const formData = ref({
      rule_name: '',
      rule_name_en: '',
      rule_name_th: '',
      report_type: '',
      priority: 50,
      allow_continue: true,
      description_cn: '',
      message_cn: '',
      rule_expression: {},
      is_active: true
    })

    // 规则条件数组（用于构建器）
    const ruleConditions = ref([
      { field: '', operator: '>=', value: '' }
    ])

    // 规则逻辑运算符
    const ruleLogic = ref('AND')

    // 计算属性
    const totalPages = computed(() => Math.ceil(rules.value.length / pageSize.value))
    
    const paginatedRules = computed(() => {
      const start = (currentPage.value - 1) * pageSize.value
      const end = start + pageSize.value
      return rules.value.slice(start, end)
    })

    // 过滤后的字段选项
    const filteredFieldOptions = computed(() => {
      if (!fieldSearchQuery.value.trim()) {
        return fieldOptions.value
      }
      
      const query = fieldSearchQuery.value.toLowerCase()
      return fieldOptions.value.filter(field => {
        const fieldName = getFieldDisplayName(field).toLowerCase()
        const fieldGroup = getFieldGroupDisplayName(field).toLowerCase()
        return fieldName.includes(query) || fieldGroup.includes(query) || field.field_name.toLowerCase().includes(query)
      })
    })

    // 分组字段选项（去重处理）
    const groupedFieldOptions = computed(() => {
      const groups = {}
      const processedFields = new Set() // 用于去重
      
      filteredFieldOptions.value.forEach(field => {
        // 使用字段名作为唯一标识符去重
        if (processedFields.has(field.field_name)) {
          return // 跳过重复字段
        }
        
        processedFields.add(field.field_name)
        const groupName = field.field_group_cn || field.field_group || '其他'
        
        if (!groups[groupName]) {
          groups[groupName] = {
            name: groupName,
            label: getFieldGroupDisplayName(field),
            fields: []
          }
        }
        groups[groupName].fields.push(field)
      })
      
      return Object.values(groups)
    })

    // 获取规则名称（多语言）
    const getRuleName = (rule) => {
      const locale = i18n.global.locale.value
      if (locale === 'th-TH' || locale === 'th') {
        return rule.rule_name_th || rule.rule_name || rule.rule_name_en
      } else if (locale === 'en-US' || locale === 'en') {
        return rule.rule_name_en || rule.rule_name || rule.rule_name_th
      } else {
        return rule.rule_name || rule.rule_name_en || rule.rule_name_th
      }
    }

    // 根据字段名获取字段对象
    const getFieldByFieldName = (fieldName) => {
      return fieldOptions.value.find(field => field.field_name === fieldName)
    }

    // 获取字段显示名称（多语言）
    const getFieldDisplayName = (field) => {
      if (!field) return ''
      const locale = i18n.global.locale.value
      if (locale === 'th-TH' || locale === 'th') {
        return field.field_th_name || field.field_cn_name || field.field_en_name
      } else if (locale === 'en-US' || locale === 'en') {
        return field.field_en_name || field.field_cn_name || field.field_th_name
      } else {
        return field.field_cn_name || field.field_en_name || field.field_th_name
      }
    }

    // 获取字段分组显示名称（多语言）
    const getFieldGroupDisplayName = (field) => {
      const locale = i18n.global.locale.value
      if (locale === 'th-TH' || locale === 'th') {
        return field.field_group_th || field.field_group_cn || field.field_group_en || field.field_group
      } else if (locale === 'en-US' || locale === 'en') {
        return field.field_group_en || field.field_group_cn || field.field_group_th || field.field_group
      } else {
        return field.field_group_cn || field.field_group_en || field.field_group_th || field.field_group
      }
    }

    // 获取描述（多语言）
    const getDescription = (rule) => {
      const locale = i18n.global.locale.value
      if (locale === 'th-TH' || locale === 'th') {
        return rule.description_th || rule.description_cn || rule.description_en || '-'
      } else if (locale === 'en-US' || locale === 'en') {
        return rule.description_en || rule.description_cn || rule.description_th || '-'
      } else {
        return rule.description_cn || rule.description_en || rule.description_th || '-'
      }
    }

    // 获取报告类型徽章样式
    const getReportTypeBadgeClass = (type) => {
      if (type && type.startsWith('AMLO')) return 'bg-primary'
      if (type && type.startsWith('BOT')) return 'bg-success'
      return 'bg-secondary'
    }

    // 获取优先级徽章样式
    const getPriorityBadgeClass = (priority) => {
      if (priority >= 80) return 'bg-danger'
      if (priority >= 50) return 'bg-warning text-dark'
      return 'bg-info'
    }

    // 加载字段选项
    const loadFieldOptions = async () => {
      try {
        const response = await complianceService.getReportFields()
        if (response.success) {
          fieldOptions.value = response.data.filter(field => field.is_active)
        } else {
          console.error('加载字段选项失败:', response.message)
        }
      } catch (error) {
        console.error('Load field options error:', error)
      }
    }

    // 加载规则列表
    const loadRules = async () => {
      loading.value = true
      try {
        const params = {}
        if (filters.value.reportType) params.report_type = filters.value.reportType
        if (filters.value.isActive !== undefined) params.is_active = filters.value.isActive

        const response = await complianceService.getTriggerRules(params)
        if (response.success) {
          rules.value = response.data
          currentPage.value = 1
        } else {
          console.error('加载规则失败:', response.message)
        }
      } catch (error) {
        console.error('Load rules error:', error)
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
        rule_name: record.rule_name,
        rule_name_en: record.rule_name_en,
        rule_name_th: record.rule_name_th,
        report_type: record.report_type,
        priority: record.priority,
        allow_continue: record.allow_continue,
        description_cn: record.description_cn,
        message_cn: record.message_cn || record.warning_message_cn,
        rule_expression: record.rule_expression,
        is_active: record.is_active
      })

      // 解析rule_expression到条件构建器
      if (record.rule_expression && record.rule_expression.conditions) {
        ruleConditions.value = record.rule_expression.conditions.map(c => ({ ...c }))
        ruleLogic.value = record.rule_expression.logic || 'AND'
      } else {
        ruleConditions.value = [{ field: '', operator: '>=', value: '' }]
        ruleLogic.value = 'AND'
      }

      openModal()
    }

    // 提交表单
    const handleSubmit = async () => {
      try {
        // 验证必填字段
        if (!formData.value.rule_name || !formData.value.report_type || !formData.value.priority) {
          alert(t('compliance.pleaseFillRequired'))
          return
        }

        // 构建完整的rule_expression
        const ruleExpression = buildRuleExpression()
        
        if (!ruleExpression.conditions || ruleExpression.conditions.length === 0) {
          alert(t('compliance.pleaseAddCondition'))
          return
        }

        const submitData = {
          ...formData.value,
          rule_expression: ruleExpression
        }

        // 兼容旧版后端：移除未支持的消息字段以避免数据库列缺失错误
        ;['message_cn', 'message_en', 'message_th'].forEach((key) => {
          if (Object.prototype.hasOwnProperty.call(submitData, key)) {
            submitData[key] = undefined
          }
        })

        let response
        if (isEditMode.value) {
          response = await complianceService.updateTriggerRule(currentRecord.value.id, submitData)
        } else {
          response = await complianceService.createTriggerRule(submitData)
        }

        if (response.success) {
          closeModal()
          loadRules()
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
        rule_name: '',
        rule_name_en: '',
        rule_name_th: '',
        report_type: '',
        priority: 50,
        allow_continue: true,
        description_cn: '',
        message_cn: '',
        rule_expression: {},
        is_active: true
      }
      ruleConditions.value = [{ field: '', operator: '>=', value: '' }]
      ruleLogic.value = 'AND'
    }

    // 切换规则状态
    const toggleRuleStatus = async (record) => {
      if (!confirm(t('compliance.confirmToggleStatus'))) return

      try {
        const response = await complianceService.updateTriggerRule(record.id, {
          is_active: !record.is_active
        })

        if (response.success) {
          loadRules()
        } else {
          alert(response.message || t('compliance.operationFailed'))
        }
      } catch (error) {
        console.error('Toggle status error:', error)
        alert(t('compliance.operationFailed'))
      }
    }

    const deleteRule = async (record) => {
      if (!confirm(t('compliance.confirmDeleteRule'))) {
        return
      }

      try {
        const response = await complianceService.deleteTriggerRule(record.id)

        if (response.success) {
          loadRules()
        } else {
          alert(response.message || t('compliance.operationFailed'))
        }
      } catch (error) {
        console.error('Delete rule error:', error)
        alert(t('compliance.operationFailed'))
      }
    }

    // 添加条件
    const addCondition = () => {
      ruleConditions.value.push({ field: '', operator: '>=', value: '' })
    }

    // 删除条件
    const removeCondition = (index) => {
      if (ruleConditions.value.length > 1) {
        ruleConditions.value.splice(index, 1)
      }
    }

    // 构建规则表达式
    const buildRuleExpression = () => {
      return {
        logic: ruleLogic.value,
        conditions: ruleConditions.value.filter(c => c.field && c.value !== '')
      }
    }

    // 判断是否为布尔值字段
    const isBooleanField = (field) => {
      return field === 'use_fcd'
    }

    // 字段变化时的处理
    const onFieldChange = (condition) => {
      // 根据字段类型设置默认操作符和值
      if (isBooleanField(condition.field)) {
        condition.operator = '='
        condition.value = 'true'
      } else if (condition.field === 'direction') {
        condition.operator = '='
        condition.value = 'buy'
      } else if (condition.field === 'payment_method') {
        condition.operator = '='
        condition.value = 'cash'
      } else if (condition.field === 'funding_source') {
        condition.operator = '='
        condition.value = 'other'
      } else if (condition.field === 'total_amount' || condition.field === 'verification_amount') {
        condition.operator = '>='
        condition.value = '5000000'  // 默认500万泰铢
      } else if (condition.field === 'usd_equivalent') {
        condition.operator = '>='
        condition.value = '20000'    // 默认2万美元等值
      } else if (condition.field === 'customer_age') {
        condition.operator = '>='
        condition.value = '70'       // 默认70岁
      } else if (condition.field === 'test_trigger_field') {
        condition.operator = '='
        condition.value = '1'        // 默认等于1
      } else if (condition.field === 'currency_code') {
        condition.operator = '='
        condition.value = 'USD'      // 默认美元
      } else {
        condition.operator = '='
        condition.value = ''
      }
    }

    // 获取字段的占位符文本
    const getFieldPlaceholder = (field) => {
      if (!field) {
        return t('compliance.enterValue')
      }
      
      const fieldName = String(field)
      
      if (fieldName.includes('amount') || fieldName === 'usd_equivalent') {
        return t('compliance.enterAmount')
      } else if (fieldName === 'currency_code') {
        return t('compliance.enterCurrencyCode')
      } else if (fieldName === 'customer_age') {
        return t('compliance.enterAge')
      }
      return t('compliance.enterValue')
    }

    // 模态框控制
    const openModal = () => {
      if (ruleModalRef.value) {
        modalInstance = new Modal(ruleModalRef.value)
        modalInstance.show()
      }
    }

    const closeModal = () => {
      if (modalInstance) {
        modalInstance.hide()
      }
      resetForm()
    }

    // 键盘快捷键支持
    const handleKeydown = (event) => {
      // Ctrl+F 打开搜索
      if (event.ctrlKey && event.key === 'f') {
        event.preventDefault()
        fieldSearchVisible.value = true
        // 聚焦到搜索框
        setTimeout(() => {
          const searchInput = document.querySelector('.field-search-input')
          if (searchInput) {
            searchInput.focus()
          }
        }, 100)
      }
      // ESC 关闭搜索
      if (event.key === 'Escape') {
        fieldSearchVisible.value = false
        fieldSearchQuery.value = ''
      }
    }

    onMounted(() => {
      loadRules()
      loadFieldOptions()
      // 添加键盘事件监听
      document.addEventListener('keydown', handleKeydown)
    })

    onUnmounted(() => {
      // 移除键盘事件监听
      document.removeEventListener('keydown', handleKeydown)
    })

    return {
      loading,
      rules,
      isEditMode,
      ruleModalRef,
      filters,
      formData,
      ruleConditions,
      ruleLogic,
      currentPage,
      pageSize,
      totalPages,
      paginatedRules,
      fieldOptions,
      groupedFieldOptions,
      getRuleName,
      getFieldByFieldName,
      getFieldDisplayName,
      getFieldGroupDisplayName,
      getDescription,
      getReportTypeBadgeClass,
      getPriorityBadgeClass,
      // 折叠状态
      ruleNameCollapsed,
      toggleRuleNameCollapse,
      // 字段搜索
      fieldSearchQuery,
      fieldSearchVisible,
      filteredFieldOptions,
      loadRules,
      loadFieldOptions,
      showCreateModal,
      showEditModal,
      handleSubmit,
      closeModal,
      deleteRule,
      toggleRuleStatus,
      addCondition,
      removeCondition,
      buildRuleExpression,
      isBooleanField,
      onFieldChange,
      getFieldPlaceholder
    }
  }
}
</script>

<style scoped>
.trigger-rules-tab {
  min-height: 400px;
}

.toolbar {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 4px;
}

.rule-builder {
  background: #fafafa;
}

.condition-item {
  padding: 6px;
  background: white;
  border-radius: 4px;
  margin-bottom: 8px;
}

.json-preview {
  max-height: 150px;
  overflow-y: auto;
}

.json-preview pre {
  font-size: 10px;
  margin: 0;
}

/* 优化模态框布局 */
.modal-xl {
  max-width: 98vw;
}

.modal-body {
  max-height: 90vh;
  overflow-y: auto;
}

/* 折叠按钮样式 */
.btn-outline-secondary {
  border-color: #6c757d;
  color: #6c757d;
}

.btn-outline-secondary:hover {
  background-color: #6c757d;
  border-color: #6c757d;
  color: white;
}

/* 紧凑的表单布局 */
.form-label-sm {
  font-size: 0.75rem;
  font-weight: 500;
  margin-bottom: 0.2rem;
}

.form-control-sm, .form-select-sm {
  padding: 0.2rem 0.4rem;
  font-size: 0.8rem;
}

/* 减少间距 */
.mb-3 {
  margin-bottom: 0.6rem !important;
}

.mb-2 {
  margin-bottom: 0.4rem !important;
}

/* 折叠内容样式 */
.collapse-content {
  background-color: #f8f9fa;
  border: 1px solid #dee2e6;
  border-radius: 0.375rem;
  padding: 0.5rem;
}

/* 紧凑的表单布局 */
.form-control-sm, .form-select-sm {
  padding: 0.2rem 0.4rem;
  font-size: 0.8rem;
}

.form-label-sm {
  font-size: 0.75rem;
  font-weight: 500;
  margin-bottom: 0.2rem;
}

/* 减少间距 */
.mb-2 {
  margin-bottom: 0.4rem !important;
}

.mb-3 {
  margin-bottom: 0.6rem !important;
}

.mt-2 {
  margin-top: 0.4rem !important;
}

.mt-3 {
  margin-top: 0.6rem !important;
}

/* 条件项紧凑布局 */
.condition-item .row {
  margin: 0;
}

.condition-item .col-lg-4,
.condition-item .col-lg-2,
.condition-item .col-md-6,
.condition-item .col-md-3 {
  padding: 0.2rem;
}

/* 按钮组紧凑 */
.btn-group-sm .btn {
  padding: 0.15rem 0.3rem;
  font-size: 0.75rem;
}

/* 条件列表最大高度 */
.conditions-list {
  max-height: 250px;
  overflow-y: auto;
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

