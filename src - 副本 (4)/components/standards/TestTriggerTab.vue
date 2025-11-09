<template>
  <div class="test-trigger-tab">
    <div class="alert alert-info">
      <font-awesome-icon :icon="['fas', 'info-circle']" class="me-2" />
      <strong>{{ $t('compliance.testTriggerHelp') }}</strong>
      <p class="mb-0 mt-2">{{ $t('compliance.testTriggerDesc') }}</p>
    </div>

    <!-- 测试配置 -->
    <div class="card mb-3">
      <div class="card-header">
        <h6 class="mb-0">{{ $t('compliance.testConfiguration') }}</h6>
      </div>
      <div class="card-body">
        <div class="row">
          <!-- 选择报告类型 -->
          <div class="col-md-6 mb-3">
            <label class="form-label">{{ $t('compliance.selectReportType') }} <span class="text-danger">*</span></label>
            <select class="form-select" v-model="testConfig.reportType" @change="onReportTypeChange">
              <option value="">{{ $t('compliance.pleaseSelect') }}</option>
              <optgroup :label="$t('compliance.amloReports')">
                <option value="AMLO-1-01">AMLO-1-01 (CTR) - {{ $t('compliance.ctrDesc') }}</option>
                <option value="AMLO-1-02">AMLO-1-02 (ATR) - {{ $t('compliance.atrDesc') }}</option>
                <option value="AMLO-1-03">AMLO-1-03 (STR) - {{ $t('compliance.strDesc') }}</option>
              </optgroup>
              <optgroup :label="$t('compliance.botReports')">
                <option value="BOT_BuyFX">BOT Buy FX - {{ $t('compliance.botBuyDesc') }}</option>
                <option value="BOT_SellFX">BOT Sell FX - {{ $t('compliance.botSellDesc') }}</option>
                <option value="BOT_FCD">BOT FCD - {{ $t('compliance.botFcdDesc') }}</option>
                <option value="BOT_Provider">BOT Provider - {{ $t('compliance.botProviderDesc') }}</option>
              </optgroup>
            </select>
          </div>

          <!-- 选择触发规则 -->
          <div class="col-md-6 mb-3">
            <label class="form-label">{{ $t('compliance.selectTriggerRule') }}</label>
            <select class="form-select" v-model="testConfig.selectedRule" @change="onRuleChange" :disabled="!testConfig.reportType">
              <option value="">{{ $t('compliance.autoDetect') }}</option>
              <option v-for="rule in availableRules" :key="rule.id" :value="rule.id">
                {{ getRuleName(rule) }} ({{ $t('compliance.priority') }}: {{ rule.priority }})
              </option>
            </select>
          </div>
        </div>

        <!-- 动态测试字段 -->
        <div v-if="testConfig.reportType" class="border-top pt-3">
          <h6 class="mb-3">{{ $t('compliance.testDataInput') }}</h6>
          
          <div class="row">
            <!-- 根据触发规则动态生成测试字段 -->
            <div v-for="field in testFields" :key="field.name" :class="field.colClass || 'col-md-6'">
              <div class="mb-3">
                <label class="form-label">
                  {{ field.label }}
                  <span v-if="field.required" class="text-danger">*</span>
                  <small v-if="field.help" class="text-muted ms-2">({{ field.help }})</small>
                  <!-- 新增：条件标记 -->
                  <span v-if="field.hasCondition" class="badge bg-info ms-2" style="font-size: 0.65em;">
                    <font-awesome-icon :icon="['fas', 'bullseye']" class="me-1" />
                    触发条件
                  </span>
                </label>
                
                <!-- 新增：显示触发条件详情 -->
                <div v-if="field.conditions && field.conditions.length > 0" class="small text-primary mb-2 p-2 bg-light rounded">
                  <font-awesome-icon :icon="['fas', 'info-circle']" class="me-1" />
                  <strong>触发条件：</strong>
                  <span v-for="(cond, idx) in field.conditions" :key="idx">
                    <span v-if="idx > 0" class="mx-1">{{ field.ruleLogic || 'AND' }}</span>
                    <code class="text-danger">{{ cond.operator }} {{ cond.value }}</code>
                  </span>
                </div>

                <!-- 数字输入 -->
                <input
                  v-if="field.type === 'number'"
                  type="number"
                  class="form-control"
                  v-model.number="testData[field.name]"
                  :placeholder="field.placeholder"
                  :step="field.step || 0.01"
                />

                <!-- 文本输入 -->
                <input
                  v-else-if="field.type === 'text'"
                  type="text"
                  class="form-control"
                  v-model="testData[field.name]"
                  :placeholder="field.placeholder"
                />

                <!-- 选择框 -->
                <select
                  v-else-if="field.type === 'select'"
                  class="form-select"
                  v-model="testData[field.name]"
                >
                  <option value="">{{ $t('compliance.pleaseSelect') }}</option>
                  <option v-for="option in field.options" :key="option.value" :value="option.value">
                    {{ option.label }}
                  </option>
                </select>

                <!-- 布尔值 -->
                <div v-else-if="field.type === 'boolean'" class="form-check form-switch mt-2">
                  <input
                    class="form-check-input"
                    type="checkbox"
                    :id="`test-${field.name}`"
                    v-model="testData[field.name]"
                  />
                  <label class="form-check-label" :for="`test-${field.name}`">
                    {{ testData[field.name] ? $t('common.yes') : $t('common.no') }}
                  </label>
                </div>
                
                <!-- 信息显示 -->
                <div v-else-if="field.type === 'info'" class="alert alert-info py-2 small">
                  {{ field.value }}
                </div>
                
                <!-- 新增：实时验证反馈 -->
                <div 
                  v-if="field.conditions && field.conditions.length > 0 && testData[field.name] !== null && testData[field.name] !== ''" 
                  class="small mt-2"
                >
                  <div v-for="(cond, idx) in field.conditions" :key="'check-'+idx" class="mb-1">
                    <font-awesome-icon 
                      :icon="['fas', checkCondition(testData[field.name], cond) ? 'check-circle' : 'times-circle']" 
                      :class="checkCondition(testData[field.name], cond) ? 'text-success' : 'text-muted'"
                      class="me-1"
                    />
                    <span :class="checkCondition(testData[field.name], cond) ? 'text-success fw-bold' : 'text-muted'">
                      {{ testData[field.name] }} {{ cond.operator }} {{ cond.value }}
                      {{ checkCondition(testData[field.name], cond) ? '✓ 满足' : '✗ 未满足' }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </div>

          <!-- 操作按钮 -->
          <div class="d-flex justify-content-end gap-2 mt-3">
            <button class="btn btn-outline-secondary" @click="resetTestData">
              <font-awesome-icon :icon="['fas', 'redo']" class="me-1" />
              {{ $t('common.reset') }}
            </button>
            <button class="btn btn-primary" @click="testTrigger" :disabled="testing">
              <span v-if="testing" class="spinner-border spinner-border-sm me-2"></span>
              <font-awesome-icon v-else :icon="['fas', 'play']" class="me-1" />
              {{ $t('compliance.testTriggerCheck') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 测试结果（增强版） -->
    <div v-if="testResult" class="card mt-4">
      <div 
        class="card-header" 
        :class="testResult.triggered ? 'bg-danger text-white' : 'bg-success text-white'"
      >
        <h6 class="mb-0">
          <font-awesome-icon 
            :icon="['fas', testResult.triggered ? 'exclamation-triangle' : 'check-circle']" 
            class="me-2" 
          />
          {{ testResult.triggered ? '✓ 触发条件满足' : '✗ 未触发' }}
        </h6>
      </div>
      <div class="card-body">
        <!-- 触发详情 -->
        <div v-if="testResult.triggered">
          <div class="row">
            <div class="col-md-6">
              <h6><font-awesome-icon :icon="['fas', 'clipboard-list']" class="me-2" />触发信息</h6>
              <table class="table table-sm table-bordered">
                <tr>
                  <td class="bg-light" style="width: 40%;"><strong>报告类型</strong></td>
                  <td><span class="badge bg-primary">{{ testResult.reportType }}</span></td>
                </tr>
                <tr>
                  <td class="bg-light"><strong>触发规则</strong></td>
                  <td>{{ testResult.ruleName }}</td>
                </tr>
                <tr v-if="testResult.message">
                  <td class="bg-light"><strong>规则描述</strong></td>
                  <td>{{ testResult.message }}</td>
                </tr>
                <tr>
                  <td class="bg-light"><strong>允许继续交易</strong></td>
                  <td>
                    <span :class="testResult.allowContinue ? 'badge bg-success' : 'badge bg-warning'">
                      {{ testResult.allowContinue ? '是' : '否' }}
                    </span>
                  </td>
                </tr>
              </table>
            </div>
            
            <div class="col-md-6">
              <h6><font-awesome-icon :icon="['fas', 'check-double']" class="me-2" />条件匹配详情</h6>
              
              <!-- 满足的条件 -->
              <div v-if="testResult.matched_conditions && testResult.matched_conditions.length > 0">
                <div class="alert alert-success py-2 mb-2">
                  <strong><font-awesome-icon :icon="['fas', 'check']" class="me-1" />满足的条件：</strong>
                  <div v-for="(cond, index) in testResult.matched_conditions" :key="'m-'+index" class="ms-3 mt-1 small">
                    <font-awesome-icon :icon="['fas', 'check-circle']" class="text-success me-1" />
                    <code>{{ cond.field }}</code>: 
                    <strong>{{ cond.actual_value }}</strong> {{ cond.operator }} {{ cond.expected_value }}
                  </div>
                </div>
              </div>
              
              <!-- 未满足的条件 -->
              <div v-if="testResult.unmatched_conditions && testResult.unmatched_conditions.length > 0">
                <div class="alert alert-warning py-2 mb-2">
                  <strong><font-awesome-icon :icon="['fas', 'times']" class="me-1" />未满足的条件：</strong>
                  <div v-for="(cond, index) in testResult.unmatched_conditions" :key="'u-'+index" class="ms-3 mt-1 small">
                    <font-awesome-icon :icon="['fas', 'times-circle']" class="text-warning me-1" />
                    <code>{{ cond.field }}</code>: 
                    {{ cond.actual_value || '(未输入)' }} {{ cond.operator }} {{ cond.expected_value }}
                  </div>
                </div>
              </div>
              
              <div v-if="(!testResult.matched_conditions || testResult.matched_conditions.length === 0) && (!testResult.unmatched_conditions || testResult.unmatched_conditions.length === 0)">
                <div class="alert alert-info py-2 small">
                  无详细条件信息
                </div>
              </div>
            </div>
          </div>
          
          <!-- 客户历史统计（跨网点） -->
          <div v-if="testResult.customer_stats" class="mt-3 border-top pt-3">
            <h6><font-awesome-icon :icon="['fas', 'history']" class="me-2" />客户历史统计（跨网点）</h6>
            <div class="row">
              <div class="col-md-4">
                <div class="card bg-light">
                  <div class="card-body py-2">
                    <div class="text-muted small">累计交易次数（30天）</div>
                    <div class="h4 mb-0 text-primary">{{ testResult.customer_stats.transaction_count_30d || 0 }}笔</div>
                  </div>
                </div>
              </div>
              <div class="col-md-4">
                <div class="card bg-light">
                  <div class="card-body py-2">
                    <div class="text-muted small">累计金额（30天）</div>
                    <div class="h4 mb-0 text-success">{{ formatCurrency(testResult.customer_stats.cumulative_amount_30d || 0) }} THB</div>
                  </div>
                </div>
              </div>
              <div class="col-md-4">
                <div class="card bg-light">
                  <div class="card-body py-2">
                    <div class="text-muted small">最后交易日期</div>
                    <div class="h6 mb-0">{{ testResult.customer_stats.last_transaction_date || '-' }}</div>
                  </div>
                </div>
              </div>
            </div>
            
            <!-- 网点分解 -->
            <div v-if="testResult.customer_stats.branch_breakdown && testResult.customer_stats.branch_breakdown.length > 0" class="mt-2">
              <div class="small text-muted mb-1"><font-awesome-icon :icon="['fas', 'sitemap']" class="me-1" />网点分解：</div>
              <div class="d-flex flex-wrap gap-2">
                <span 
                  v-for="branch in testResult.customer_stats.branch_breakdown" 
                  :key="branch.branch_id"
                  class="badge bg-info"
                  style="font-size: 0.85em;"
                >
                  Branch {{ branch.branch_id }}: {{ branch.count }}笔, {{ formatCurrency(branch.amount) }} THB
                </span>
              </div>
            </div>
          </div>
          
          <!-- 操作按钮 -->
          <div class="mt-4 d-flex gap-2">
            <button class="btn btn-primary" @click="previewDynamicForm">
              <font-awesome-icon :icon="['fas', 'file-alt']" class="me-1" />
              查看填报表单
            </button>
            <button class="btn btn-success" @click="generateTestPDF">
              <font-awesome-icon :icon="['fas', 'file-pdf']" class="me-1" />
              生成测试PDF
            </button>
          </div>
        </div>
        
        <!-- 未触发时的提示 -->
        <div v-else>
          <div class="alert alert-success">
            <font-awesome-icon :icon="['fas', 'info-circle']" class="me-2" />
            <strong>根据当前输入的数据，未满足触发条件。</strong>
          </div>
          
          <!-- 显示所有条件的检查结果 -->
          <div v-if="testResult.all_conditions && testResult.all_conditions.length > 0" class="mt-3">
            <h6>条件检查结果：</h6>
            <div class="list-group">
              <div 
                v-for="(cond, index) in testResult.all_conditions" 
                :key="index"
                class="list-group-item"
                :class="cond.matched ? 'list-group-item-success' : 'list-group-item-light'"
              >
                <div class="d-flex justify-content-between align-items-center">
                  <div>
                    <font-awesome-icon 
                      :icon="['fas', cond.matched ? 'check' : 'times']" 
                      :class="cond.matched ? 'text-success' : 'text-muted'"
                      class="me-2"
                    />
                    <strong>{{ cond.field }}:</strong>
                    <code>{{ cond.actual_value || '(未输入)' }} {{ cond.operator }} {{ cond.expected_value }}</code>
                  </div>
                  <span :class="cond.matched ? 'badge bg-success' : 'badge bg-secondary'">
                    {{ cond.matched ? '✓ 满足' : '✗ 未满足' }}
                  </span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- 动态表单预览模态框 -->
    <div class="modal fade" id="formPreviewModal" tabindex="-1" ref="formPreviewModalRef">
      <div class="modal-dialog modal-xl">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ $t('compliance.dynamicFormPreview') }} - {{ testConfig.reportType }}
            </h5>
            <button type="button" class="btn-close" @click="closeFormPreview"></button>
          </div>
          <div class="modal-body">
            <div v-if="formPreviewLoading" class="text-center py-4">
              <div class="spinner-border" role="status">
                <span class="visually-hidden">{{ $t('common.loading') }}</span>
              </div>
            </div>
            <DynamicForm
              v-else-if="formPreviewData"
              :report-type="testConfig.reportType"
              :initial-data="testData"
              :show-check-trigger="false"
              @submit="handleTestFormSubmit"
            />
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" @click="closeFormPreview">{{ $t('common.close') }}</button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
import { ref, computed, watch, onMounted } from 'vue'
import { useI18n } from 'vue-i18n'
import i18n from '@/i18n'
import complianceService from '@/services/api/complianceService'
import api from '@/services/api'
import DynamicForm from '@/components/amlo/DynamicForm/DynamicForm.vue'
import { Modal } from 'bootstrap'

export default {
  name: 'TestTriggerTab',
  components: {
    DynamicForm
  },
  setup() {
    const { t } = useI18n()

    const testing = ref(false)
    const testResult = ref(null)
    const formPreviewLoading = ref(false)
    const formPreviewData = ref(null)
    const formPreviewModalRef = ref(null)
    let formPreviewModalInstance = null

    const allRules = ref([])
    const allFields = ref([])  // 新增：所有字段定义
    const currentRate = ref(null)

    const testConfig = ref({
      reportType: '',
      selectedRule: ''
    })

    const testData = ref({
      // 基础字段（所有触发规则可能需要）
      total_amount: null,        // 本币金额（与实际交易字段一致）
      amount: null,              // 外币金额
      currency_code: '',         // 币种代码
      direction: 'buy',          // 交易方向
      payment_method: 'cash',    // 支付方式
      customer_age: null,        // 客户年龄
      use_fcd: false,            // 是否使用FCD账户
      funding_source: '',        // 资金来源
      customer_id: '',           // 客户证件号
      test_trigger_field: null   // 测试触发字段
    })

    // 计算属性：可用的规则
    const availableRules = computed(() => {
      if (!testConfig.value.reportType) return []
      return allRules.value.filter(r => r.report_type === testConfig.value.reportType && r.is_active)
    })

    // 获取字段的多语言名称
    const getFieldLabel = (fieldDef) => {
      if (!fieldDef) return ''
      const locale = i18n.global.locale.value
      if (locale === 'th-TH' || locale === 'th') {
        return fieldDef.field_th_name || fieldDef.field_cn_name || fieldDef.field_en_name || fieldDef.field_name
      } else if (locale === 'en-US' || locale === 'en') {
        return fieldDef.field_en_name || fieldDef.field_cn_name || fieldDef.field_th_name || fieldDef.field_name
      } else {
        return fieldDef.field_cn_name || fieldDef.field_en_name || fieldDef.field_th_name || fieldDef.field_name
      }
    }

    // 获取字段的多语言占位符
    const getFieldPlaceholder = (fieldDef) => {
      if (!fieldDef || !fieldDef.placeholder) return ''
      try {
        const placeholders = JSON.parse(fieldDef.placeholder)
        const locale = i18n.global.locale.value
        if (locale === 'th-TH' || locale === 'th') {
          return placeholders.th || placeholders.cn || placeholders.en || ''
        } else if (locale === 'en-US' || locale === 'en') {
          return placeholders.en || placeholders.cn || placeholders.th || ''
        } else {
          return placeholders.cn || placeholders.en || placeholders.th || ''
        }
      } catch (e) {
        return fieldDef.placeholder || ''
      }
    }

    // 映射字段类型
    const mapFieldType = (dbFieldType) => {
      const typeMap = {
        'VARCHAR': 'text',
        'TEXT': 'text',
        'INT': 'number',
        'DECIMAL': 'number',
        'DATE': 'date',
        'BOOLEAN': 'boolean',
        'SELECT': 'select'
      }
      return typeMap[dbFieldType] || 'text'
    }

    // 动态测试字段（根据触发规则生成）
    const testFields = computed(() => {
      const fields = []

      if (!testConfig.value.reportType) return fields

      // 解析选中规则的条件，动态生成测试字段
      const selectedRule = allRules.value.find(r => r.id === testConfig.value.selectedRule)
      console.log('🔍 [TestTrigger] selectedRule:', selectedRule)
      
      let conditions = []
      let ruleLogic = 'AND'
      if (selectedRule?.rule_expression) {
        try {
          const ruleExpr = typeof selectedRule.rule_expression === 'string' ? 
            JSON.parse(selectedRule.rule_expression) : 
            selectedRule.rule_expression
          conditions = ruleExpr.conditions || []
          ruleLogic = ruleExpr.logic || 'AND'
        } catch (e) {
          console.error('解析规则表达式失败:', e)
        }
      }
      
      console.log('🔍 [TestTrigger] conditions:', conditions)
      console.log('🔍 [TestTrigger] ruleLogic:', ruleLogic)

      // 创建字段-条件映射（同一字段可能有多个条件）
      const fieldConditions = {}
      conditions.forEach(cond => {
        if (!fieldConditions[cond.field]) {
          fieldConditions[cond.field] = []
        }
        fieldConditions[cond.field].push(cond)
      })

      // 提取条件中涉及的字段
      const requiredFields = new Set()
      conditions.forEach(condition => {
        requiredFields.add(condition.field)
      })
      
      console.log('🔍 [TestTrigger] requiredFields:', Array.from(requiredFields))
      console.log('🔍 [TestTrigger] fieldConditions:', fieldConditions)
      
      // 如果没有找到规则或规则解析失败，强制显示基本字段
      if (!selectedRule || conditions.length === 0) {
        console.log('🔍 [TestTrigger] 规则解析失败，使用默认字段')
        // 强制添加测试触发字段和交易金额字段（使用实际交易字段名）
        requiredFields.add('test_trigger_field')
        requiredFields.add('total_amount')
      }

      // 首先，添加规则条件中涉及的字段（从数据库获取定义）
      const processedFields = new Set()  // 防止重复添加
      
      requiredFields.forEach(fieldName => {
        // 从allFields中查找字段定义
        const fieldDef = allFields.value.find(f => 
          f.field_name === fieldName && 
          f.report_type === testConfig.value.reportType &&
          f.is_active
        )
        
        if (fieldDef) {
          console.log('🔍 [TestTrigger] 找到字段定义:', fieldName, fieldDef)
          
          // 根据字段类型构建字段配置
          const fieldConfig = {
            name: fieldName,
            label: getFieldLabel(fieldDef),
            type: mapFieldType(fieldDef.field_type),
            required: fieldDef.is_required || false,
            colClass: 'col-md-4',
            placeholder: getFieldPlaceholder(fieldDef),
            
            // 新增：添加条件信息
            conditions: fieldConditions[fieldName] || [],
            hasCondition: !!fieldConditions[fieldName],
            ruleLogic: ruleLogic
          }
          
          // 如果字段有条件，生成条件提示文本
          if (fieldConditions[fieldName] && fieldConditions[fieldName].length > 0) {
            fieldConfig.conditionHints = fieldConditions[fieldName].map(cond => 
              `${cond.operator} ${cond.value}`
            )
          }
          
          // 如果是数字类型，添加step
          if (fieldConfig.type === 'number') {
            fieldConfig.step = fieldDef.field_type === 'INT' ? 1 : 0.01
          }
          
          // 如果是选择类型，添加options（从validation_rule中获取）
          if (fieldConfig.type === 'select' && fieldDef.validation_rule) {
            try {
              const validationRule = typeof fieldDef.validation_rule === 'string' 
                ? JSON.parse(fieldDef.validation_rule) 
                : fieldDef.validation_rule
              if (validationRule.options) {
                fieldConfig.options = validationRule.options.map(opt => ({
                  value: opt.value || opt,
                  label: opt.label || opt
                }))
              }
            } catch (e) {
              console.error('解析validation_rule失败:', e)
            }
          }
          
          fields.push(fieldConfig)
          processedFields.add(fieldName)
        } else {
          console.log('🔍 [TestTrigger] 未找到字段定义，使用默认配置:', fieldName)
        }
      })

      // 基础字段：交易方向和币种（总是显示，即使没有在规则中）
      if (!processedFields.has('direction')) {
        fields.push({
          name: 'direction',
          label: t('compliance.direction'),
          type: 'select',
          required: true,
          colClass: 'col-md-4',
          options: [
            { value: 'buy', label: t('transaction.buy') },
            { value: 'sell', label: t('transaction.sell') }
          ],
          help: t('compliance.directionHelp')
        })
      }

      if (!processedFields.has('currency_code')) {
        fields.push({
          name: 'currency_code',
          label: t('compliance.currencyCode'),
          type: 'text',
          required: true,
          colClass: 'col-md-4',
          placeholder: 'USD, EUR, JPY...',
          help: t('compliance.currencyCodeHelp')
        })
      }

      // 添加外币金额字段（用于汇率转换）- 如果还没有添加
      if (!processedFields.has('amount') && (requiredFields.has('total_amount') || requiredFields.has('amount'))) {
        fields.push({
          name: 'amount',
          label: '外币金额',
          type: 'number',
          required: false,
          colClass: 'col-md-4',
          placeholder: '20000',
          help: '外币金额，用于汇率转换计算',
          step: 0.01
        })
      }

      // 如果规则中包含金额相关字段且还没有处理
      if (!processedFields.has('total_amount') && (requiredFields.has('total_amount') || requiredFields.has('verification_amount') || requiredFields.has('local_amount') || requiredFields.has('amount'))) {
        fields.push({
          name: 'total_amount',
          label: '交易金额(本币)',
          type: 'number',
          required: true,
          colClass: 'col-md-4',
          placeholder: '5000000',
          help: '交易金额（泰铢），与实际交易字段一致',
          step: 0.01
        })
      }

      // 注释掉硬编码的字段定义，因为它们现在从数据库加载
      // 只有在数据库中找不到定义时才使用这些默认值
      // 这些字段已经在上面的processedFields循环中处理了

      // 客户证件号（用于历史查询）
      fields.push({
        name: 'customer_id',
        label: t('compliance.customerId'),
        type: 'text',
        required: false,
        colClass: 'col-md-6',
        placeholder: '1234567890123',
        help: t('compliance.customerIdHelp')
      })

      // 显示当前汇率信息
      if (currentRate.value) {
        fields.push({
          name: '_rate_info',
          label: t('compliance.currentRate'),
          type: 'info',
          colClass: 'col-md-6',
          value: `1 ${testData.value.currency_code} = ${currentRate.value.sell_rate} THB`
        })
      }

      return fields
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
    
    // 新增：检查单个条件是否满足
    const checkCondition = (actualValue, condition) => {
      if (actualValue === null || actualValue === undefined || actualValue === '') {
        return false
      }
      
      const operator = condition.operator
      const expectedValue = condition.value
      
      try {
        switch (operator) {
          case '>':
            return parseFloat(actualValue) > parseFloat(expectedValue)
          case '>=':
            return parseFloat(actualValue) >= parseFloat(expectedValue)
          case '<':
            return parseFloat(actualValue) < parseFloat(expectedValue)
          case '<=':
            return parseFloat(actualValue) <= parseFloat(expectedValue)
          case '=':
          case '==':
            return String(actualValue) === String(expectedValue)
          case '!=':
            return String(actualValue) !== String(expectedValue)
          case 'IN':
            return Array.isArray(expectedValue) && expectedValue.includes(actualValue)
          case 'NOT IN':
            return Array.isArray(expectedValue) && !expectedValue.includes(actualValue)
          default:
            return false
        }
      } catch (e) {
        console.error('检查条件失败:', e)
        return false
      }
    }
    
    // 新增：格式化货币
    const formatCurrency = (amount) => {
      if (!amount) return '0'
      return new Intl.NumberFormat('en-US', {
        minimumFractionDigits: 0,
        maximumFractionDigits: 2
      }).format(amount)
    }

    // 加载所有字段定义
    const loadAllFields = async () => {
      try {
        console.log('🔍 [TestTrigger] 开始加载字段定义...')
        const response = await complianceService.getFieldDefinitions()
        console.log('🔍 [TestTrigger] 字段API响应:', response)
        if (response.success) {
          allFields.value = response.data
          console.log('🔍 [TestTrigger] 加载的字段数量:', allFields.value.length)
        } else {
          console.error('🔍 [TestTrigger] 字段加载失败:', response.message)
        }
      } catch (error) {
        console.error('Load fields error:', error)
      }
    }

    // 加载所有规则
    const loadAllRules = async () => {
      try {
        console.log('🔍 [TestTrigger] 开始加载规则...')
        const response = await complianceService.getTriggerRules({})
        console.log('🔍 [TestTrigger] 规则API响应:', response)
        if (response.success) {
          allRules.value = response.data
          console.log('🔍 [TestTrigger] 加载的规则数量:', allRules.value.length)
          console.log('🔍 [TestTrigger] 规则列表:', allRules.value)
        } else {
          console.error('🔍 [TestTrigger] 规则加载失败:', response.message)
        }
      } catch (error) {
        console.error('Load rules error:', error)
      }
    }

    // 加载最近的汇率（优先使用最大面值汇率）
    const loadCurrentRate = async (currencyCode) => {
      try {
        console.log('🔍 [TestTrigger] 加载汇率:', currencyCode)
        
        // 优先尝试获取最大面值汇率
        try {
          const maxDenomResponse = await api.get(
            `/api/rates/max_denomination_rate/${currencyCode}`,
            { params: { direction: testData.value.direction } }
          )
          
          if (maxDenomResponse.data.success && maxDenomResponse.data.data) {
            currentRate.value = maxDenomResponse.data.data
            console.log(`✓ 使用${currentRate.value.rate_type}汇率:`, currentRate.value)
            
            if (currentRate.value.rate_type === 'denomination') {
              console.log(`  最大面值: ${currentRate.value.max_denomination} ${currentRate.value.denomination_type}`)
            }
            
            // 自动计算本币金额
            if (testData.value.amount && currencyCode) {
              calculateLocalAmount()
            }
            return
          }
        } catch (error) {
          console.warn('面值汇率查询失败，回退到标准汇率:', error)
        }
        
        // 回退到标准汇率
        const response = await api.get(`/api/rates/current/${currencyCode}`)
        console.log('🔍 [TestTrigger] 标准汇率响应:', response.data)
        if (response.data.success && response.data.rate) {
          currentRate.value = {
            ...response.data.rate,
            rate_type: 'standard'
          }
          console.log('🔍 [TestTrigger] 使用标准汇率:', currentRate.value)
          
          // 自动计算本币金额
          if (testData.value.amount && currencyCode) {
            calculateLocalAmount()
          }
        }
      } catch (error) {
        console.error('Load rate error:', error)
      }
    }

    // 计算本币金额（外币金额 * 汇率）
    const calculateLocalAmount = () => {
      if (testData.value.amount && currentRate.value && testData.value.currency_code) {
        // 根据交易方向选择汇率
        let rate
        if (testData.value.direction === 'buy') {
          // 客户买入外币 = 银行卖出外币，使用卖出汇率
          rate = currentRate.value.sell_rate || currentRate.value.rate
        } else {
          // 客户卖出外币 = 银行买入外币，使用买入汇率
          rate = currentRate.value.buy_rate || currentRate.value.rate
        }
        
        if (rate) {
          const localAmount = testData.value.amount * rate
          testData.value.total_amount = Math.round(localAmount * 100) / 100
          
          console.log('🔍 [TestTrigger] 汇率转换:', {
            foreignAmount: testData.value.amount,
            currency: testData.value.currency_code,
            direction: testData.value.direction,
            rate: rate,
            localAmount: testData.value.total_amount
          })
          
          // 如果设置了USD等值字段，也计算USD等值
          if (testData.value.currency_code !== 'USD') {
            calculateUSDEquivalent()
          } else {
            testData.value.usd_equivalent = testData.value.amount
          }
        }
      }
    }

    // 计算美元等值
    const calculateUSDEquivalent = async () => {
      if (!testData.value.total_amount) return

      try {
        // 获取USD汇率，将本币金额转换为USD等值
        const response = await api.get('rates/current/USD')
        if (response.data.success && response.data.rate) {
          // 使用卖出汇率将本币转换为USD
          const usdRate = response.data.rate.sell_rate || response.data.rate.rate
          if (usdRate) {
            testData.value.usd_equivalent = Math.round((testData.value.total_amount / usdRate) * 100) / 100
            console.log('🔍 [TestTrigger] USD等值计算:', {
              localAmount: testData.value.total_amount,
              usdRate: usdRate,
              usdEquivalent: testData.value.usd_equivalent
            })
          }
        }
      } catch (error) {
        console.error('Calculate USD equivalent error:', error)
      }
    }

    // 报告类型变化
    const onReportTypeChange = () => {
      testConfig.value.selectedRule = ''
      testResult.value = null
      resetTestData()
    }

    // 规则变化
    const onRuleChange = () => {
      testResult.value = null
    }

    // 重置测试数据
    const resetTestData = () => {
      testData.value = {
        total_amount: null,
        amount: null,
        currency_code: '',
        direction: 'buy',
        payment_method: 'cash',
        customer_age: null,
        use_fcd: false,
        funding_source: '',
        customer_id: '',
        test_trigger_field: null
      }
    }

    // 测试触发（增强版 - 与实际交易使用相同逻辑）
    const testTrigger = async () => {
      if (!testConfig.value.reportType) {
        alert('请先选择报告类型')
        return
      }
      
      testing.value = true
      testResult.value = null

      try {
        console.log('🧪 [TestTrigger] 开始测试触发检查...')
        console.log('🧪 [TestTrigger] 报告类型:', testConfig.value.reportType)
        console.log('🧪 [TestTrigger] 测试数据:', testData.value)
        
        // 如果有客户证件号，先查询客户历史（与实际交易相同）
        let customerStats = null
        if (testData.value.customer_id && testData.value.customer_id.trim()) {
          try {
            const historyResponse = await api.get(`/api/repform/customer-history/${testData.value.customer_id}`)
            if (historyResponse.data.success) {
              customerStats = historyResponse.data.data
              console.log('🧪 [TestTrigger] 客户历史统计:', customerStats)
            }
          } catch (error) {
            console.warn('查询客户历史失败:', error)
          }
        }
        
        // 构建测试数据（与实际交易数据结构一致）
        const checkData = {
          report_type: testConfig.value.reportType,
          data: {
            ...testData.value,
            // 如果有客户统计，添加到数据中供规则引擎使用
            ...(customerStats ? {
              cumulative_amount_30d: customerStats.cumulative_amount_30d,
              transaction_count_30d: customerStats.transaction_count_30d
            } : {})
          },
          branch_id: 1  // TODO: 使用当前用户的branch_id
        }
        
        console.log('🧪 [TestTrigger] 发送触发检查请求:', checkData)
        
        const response = await api.post('repform/check-trigger', checkData)
        
        console.log('🧪 [TestTrigger] 触发检查响应:', response.data)

        if (response.data.success) {
          const triggers = response.data.triggers
          const stats = response.data.customer_stats || customerStats

          // 根据报告类型解析触发结果
          let triggerData = null
          if (testConfig.value.reportType.startsWith('AMLO')) {
            triggerData = triggers.amlo
          } else if (testConfig.value.reportType.startsWith('BOT')) {
            triggerData = triggers.bot
          }

          // 构建增强的测试结果
          testResult.value = {
            triggered: triggerData?.triggered || false,
            reportType: triggerData?.report_type || testConfig.value.reportType,
            message: triggerData?.message_cn || triggerData?.message || '',
            allowContinue: triggerData?.allow_continue !== false,
            ruleName: triggerData?.rule_name || testConfig.value.reportType,
            
            // 新增：条件匹配详情
            matched_conditions: triggerData?.matched_conditions || [],
            unmatched_conditions: triggerData?.unmatched_conditions || [],
            all_conditions: [
              ...(triggerData?.matched_conditions || []),
              ...(triggerData?.unmatched_conditions || [])
            ],
            
            // 新增：客户统计（包含网点分解）
            customer_stats: stats,
            
            // 保留完整响应
            raw_response: response.data
          }
          
          console.log('🧪 [TestTrigger] 测试结果:', testResult.value)
          
          // 如果触发且有客户统计，显示详细信息
          if (testResult.value.triggered && stats) {
            console.log('🧪 [TestTrigger] 客户历史详情:')
            console.log(`  累计交易: ${stats.transaction_count_30d}笔`)
            console.log(`  累计金额: ${stats.cumulative_amount_30d} THB`)
            if (stats.branch_breakdown) {
              console.log('  网点分解:')
              stats.branch_breakdown.forEach(b => {
                console.log(`    Branch ${b.branch_id}: ${b.count}笔, ${b.amount} THB`)
              })
            }
          }
        }
      } catch (error) {
        console.error('Test trigger error:', error)
        alert(t('compliance.testFailed') + ': ' + (error.response?.data?.message || error.message))
      } finally {
        testing.value = false
      }
    }

    // 预览动态表单
    const previewDynamicForm = async () => {
      formPreviewLoading.value = true
      
      try {
        const response = await api.get(`/api/repform/form-definition/${testConfig.value.reportType}`, {
          params: { language: 'zh' }
        })

        if (response.data.success) {
          formPreviewData.value = response.data.data
          openFormPreviewModal()
        }
      } catch (error) {
        console.error('Load form definition error:', error)
        alert(t('compliance.loadFormFailed'))
      } finally {
        formPreviewLoading.value = false
      }
    }

    // 生成测试PDF
    const generateTestPDF = async () => {
      try {
        const response = await api.post('/amlo/generate-test-pdf', {
          report_type: testConfig.value.reportType,
          data: testData.value
        })

        if (response.data.success) {
          alert(t('compliance.pdfGenerateSuccess') + '\n' + t('compliance.pdfPath') + ': ' + response.data.pdf_path)
        }
      } catch (error) {
        console.error('Generate PDF error:', error)
        alert(t('compliance.pdfGenerateFailed'))
      }
    }

    // 处理测试表单提交
    const handleTestFormSubmit = (formData) => {
      console.log('测试表单提交:', formData)
      alert(t('compliance.testFormSubmitSuccess'))
      closeFormPreviewModal()
    }

    // 模态框控制
    const openFormPreviewModal = () => {
      if (formPreviewModalRef.value) {
        formPreviewModalInstance = new Modal(formPreviewModalRef.value)
        formPreviewModalInstance.show()
      }
    }

    const closeFormPreview = () => {
      if (formPreviewModalInstance) {
        formPreviewModalInstance.hide()
      }
    }

    const closeFormPreviewModal = closeFormPreview  // 别名，供模板使用

    // 监听验证金额变化，自动计算美元等值
    watch(() => testData.value.verification_amount, (newValue) => {
      if (newValue && newValue > 0) {
        calculateUSDEquivalent()
      }
    })

    // 监听币种变化，加载汇率
    watch(() => testData.value.currency_code, (newValue) => {
      if (newValue && newValue.length === 3) {
        loadCurrentRate(newValue)
      }
    })

    onMounted(() => {
      loadAllFields()  // 加载字段定义
      loadAllRules()   // 加载规则
    })

    // 监听币种变化，自动加载汇率
    watch(() => testData.value.currency_code, (newValue) => {
      if (newValue) {
        loadCurrentRate(newValue)
      }
    })

    // 监听外币金额变化，自动计算本币金额
    watch(() => testData.value.amount, () => {
      if (testData.value.amount && testData.value.currency_code) {
        calculateLocalAmount()
      }
    })

    // 监听交易方向变化，重新计算汇率
    watch(() => testData.value.direction, () => {
      if (testData.value.amount && testData.value.currency_code && currentRate.value) {
        calculateLocalAmount()
      }
    })

    return {
      testing,
      testResult,
      formPreviewLoading,
      formPreviewData,
      formPreviewModalRef,
      testConfig,
      testData,
      testFields,
      availableRules,
      getRuleName,
      onReportTypeChange,
      onRuleChange,
      resetTestData,
      testTrigger,
      previewDynamicForm,
      generateTestPDF,
      handleTestFormSubmit,
      closeFormPreview,
      closeFormPreviewModal,
      checkCondition,  // 新增
      formatCurrency,   // 新增
      currentRate      // 新增
    }
  }
}
</script>

<style scoped>
.test-trigger-tab {
  min-height: 400px;
}

.toolbar {
  padding: 12px;
  background: #f8f9fa;
  border-radius: 4px;
}
</style>

