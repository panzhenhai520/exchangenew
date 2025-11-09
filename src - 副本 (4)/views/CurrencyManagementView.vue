<template>
  <div class="currency-management-container">
    <!-- 页面标题 -->
    <div class="d-flex justify-content-between align-items-center mb-4">
      <h2 class="page-title-bold">
        <font-awesome-icon :icon="['fas', 'coins']" class="me-2" />
        {{ $t('currencyManagement.title') }}
      </h2>
      <div>
        <button class="btn btn-outline-info btn-sm me-2" @click="initTemplates" :disabled="loading">
          <i class="fas fa-database"></i>
          {{ $t('currencyManagement.initTemplates') }}
        </button>
        <button 
          class="btn btn-primary"
          @click="showAddModal"
          :disabled="loading">
          <i class="fas fa-plus me-2"></i>
          {{ $t('currencyManagement.addTemplate') }}
        </button>
      </div>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="text-center py-4">
      <div class="spinner-border text-primary" role="status">
        <span class="visually-hidden">{{ $t('common.loading') }}</span>
      </div>
    </div>

    <!-- 过滤器和币种模板列表 -->
    <div v-else class="card shadow-sm">
      <div class="card-body">
        <!-- 过滤器 -->
        <div class="row mb-3">
          <div class="col-md-3">
            <label class="form-label">{{ $t('currencyManagement.filter.title') }}</label>
            <select 
              v-model="filterStatus" 
              class="form-select"
              @change="applyFilter">
              <option value="all">{{ $t('currencyManagement.filter.all') }}</option>
              <option value="inUse">{{ $t('currencyManagement.filter.inUse') }}</option>
              <option value="notInUse">{{ $t('currencyManagement.filter.notInUse') }}</option>
            </select>
          </div>
          <div class="col-md-9 d-flex align-items-end">
            <div class="text-muted small">
              {{ $t('currencyManagement.filter.title') }}: 
              <span class="badge bg-info">{{ filteredTemplates.length }}</span> / 
              <span class="badge bg-secondary">{{ templates.length }}</span>
            </div>
          </div>
        </div>
        
        <div class="table-responsive">
          <table class="table table-hover">
            <thead class="table-light">
              <tr>
                <th>{{ $t('currencyManagement.serialNumber') }}</th>
                <th>{{ $t('currencyManagement.flag') }}</th>
                <th>{{ $t('currencyManagement.currencyCode') }}</th>
                <th>{{ $t('currencyManagement.currencyName') }}</th>
                <th>{{ $t('currencyManagement.country') }}</th>
                <th>{{ $t('currencyManagement.symbol') }}</th>
                <th>{{ $t('currencyManagement.status') }}</th>
                <th>{{ $t('common.actions') }}</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="(template, index) in filteredTemplates" :key="template.id">
                <td>{{ index + 1 }}</td>
                <td>
                  <CurrencyFlag 
                    :code="template.flag_code" 
                    :custom-filename="template.custom_flag_filename"
                    :width="32" 
                    :height="24"
                    class="flag-icon-large" />
                </td>
                <td>
                  <span class="badge bg-primary">{{ template.currency_code }}</span>
                </td>
                <td>{{ getCurrencyNameTranslated(template.currency_code, template.currency_name, template.custom_flag_filename) }}</td>
                <td>{{ getCountryNameTranslated(template.country || template.flag_code) }}</td>
                <td>
                  <span class="currency-symbol">{{ template.symbol }}</span>
                </td>
                <td>
                  <span :class="template.is_in_use ? 'badge bg-success' : 'badge bg-secondary'">
                    {{ template.is_in_use ? $t('currencyManagement.inUse') : $t('currencyManagement.notInUse') }}
                  </span>
                </td>
                <td>
                  <div class="btn-group btn-group-sm">
                    <button 
                      class="btn btn-outline-primary"
                      @click="editTemplate(template)"
                      :title="$t('common.edit')">
                      <i class="fas fa-edit"></i>
                    </button>
                    <button 
                      v-if="!template.is_in_use"
                      class="btn btn-outline-danger"
                      @click="confirmDelete(template)"
                      :title="$t('common.delete')">
                      <i class="fas fa-trash"></i>
                    </button>
                  </div>
                </td>
              </tr>
              <tr v-if="filteredTemplates.length === 0">
                <td colspan="8" class="text-center text-muted py-4">
                  {{ $t('currencyManagement.noData') }}
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>
    </div>

    <!-- 新增/编辑模态框 -->
    <div class="modal fade" id="templateModal" tabindex="-1">
      <div class="modal-dialog modal-lg">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">
              {{ isEdit ? $t('currencyManagement.editTemplate') : $t('currencyManagement.addTemplate') }}
            </h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <form @submit.prevent="saveTemplate">
              <!-- 快速选择区域 -->
              <div class="row mb-4">
                <div class="col-md-6">
                  <label class="form-label">{{ $t('currencyManagement.quickSelectCountry') }}</label>
                  <select 
                    class="form-select"
                    v-model="selectedCountry"
                    @change="onCountrySelect">
                    <option value="">{{ $t('currencyManagement.selectCountry') }}</option>
                    <option 
                      v-for="country in countries" 
                      :key="country.code" 
                      :value="country.code">
                      {{ getCountryNameTranslated(country.code) }} ({{ country.code }})
                    </option>
                  </select>
                </div>
                <div class="col-md-6">
                  <label class="form-label">{{ $t('currencyManagement.quickSelectCurrency') }}</label>
                  <select 
                    class="form-select"
                    v-model="selectedCurrency"
                    @change="onCurrencySelect">
                    <option value="">{{ $t('currencyManagement.selectCurrency') }}</option>
                    <option 
                      v-for="currency in currencies" 
                      :key="currency.code" 
                      :value="currency.code">
                      {{ currency.code }} - {{ getCurrencyNameTranslated(currency.code, currency.name) }}
                    </option>
                  </select>
                </div>
              </div>

              <div class="row">
                <div class="col-md-6">
                  <div class="mb-3">
                    <label class="form-label">{{ $t('currencyManagement.currencyCode') }} *</label>
                    <input 
                      type="text" 
                      class="form-control"
                      v-model="templateForm.currency_code"
                      :placeholder="$t('currencyManagement.currencyCodePlaceholder')"
                      maxlength="3"
                      required>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="mb-3">
                    <label class="form-label">{{ $t('currencyManagement.currencyName') }} *</label>
                    <input 
                      type="text" 
                      class="form-control"
                      v-model="templateForm.currency_name"
                      :placeholder="$t('currencyManagement.currencyNamePlaceholder')"
                      required>
                  </div>
                </div>
              </div>

              <div class="row">
                <div class="col-md-6">
                  <div class="mb-3">
                    <label class="form-label">{{ $t('currencyManagement.country') }} *</label>
                    <input 
                      type="text" 
                      class="form-control"
                      v-model="templateForm.country"
                      :placeholder="$t('currencyManagement.countryPlaceholder')"
                      required>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="mb-3">
                    <label class="form-label">{{ $t('currencyManagement.flagCode') }} *</label>
                    <input 
                      type="text" 
                      class="form-control"
                      v-model="templateForm.flag_code"
                      :placeholder="$t('currencyManagement.flagCodePlaceholder')"
                      maxlength="2"
                      required>
                  </div>
                </div>
              </div>

              <div class="row">
                <div class="col-md-6">
                  <div class="mb-3">
                    <label class="form-label">{{ $t('currencyManagement.symbol') }}</label>
                    <input 
                      type="text" 
                      class="form-control"
                      v-model="templateForm.symbol"
                      :placeholder="$t('currencyManagement.symbolPlaceholder')"
                      maxlength="5">
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="mb-3">
                    <label class="form-label">{{ $t('currencyManagement.preview') }}</label>
                    <div class="form-control d-flex align-items-center" style="height: auto; min-height: 38px;">
                      <CurrencyFlag 
                        v-if="templateForm.custom_flag_filename || templateForm.flag_code"
                        :code="templateForm.flag_code" 
                        :custom-filename="templateForm.custom_flag_filename"
                        :width="32" 
                        :height="24"
                        class="me-2 flag-icon-large" />
                      <span>{{ templateForm.currency_code }} - {{ templateForm.currency_name }}</span>
                    </div>
                  </div>
                </div>
              </div>

              <!-- 自定义图标上传区域 -->
              <div class="row">
                <div class="col-md-6">
                  <div class="mb-3">
                    <label class="form-label">{{ $t('currencyManagement.customFlag') }}</label>
                    <div class="d-flex align-items-center">
                      <input 
                        type="file" 
                        class="form-control"
                        ref="flagFileInput"
                        @change="onFlagFileChange"
                        accept=".png,.jpg,.jpeg,.svg"
                        style="display: none;">
                      <button 
                        type="button" 
                        class="btn btn-outline-primary me-2"
                        @click="$refs.flagFileInput.click()">
                        <i class="fas fa-upload me-1"></i>
                        {{ $t('currencyManagement.uploadFlag') }}
                      </button>
                      <button 
                        v-if="templateForm.custom_flag_filename"
                        type="button" 
                        class="btn btn-outline-danger btn-sm"
                        @click="removeCustomFlag">
                        <i class="fas fa-trash"></i>
                      </button>
                    </div>
                    <div v-if="templateForm.custom_flag_filename" class="mt-2">
                      <small class="text-success">
                        <i class="fas fa-check-circle me-1"></i>
                        {{ $t('currencyManagement.customFlagUploaded') }}
                      </small>
                    </div>
                  </div>
                </div>
                <div class="col-md-6">
                  <div class="mb-3">
                    <label class="form-label">{{ $t('currencyManagement.flagPreview') }}</label>
                    <div class="form-control d-flex align-items-center justify-content-center" style="height: 60px; background-color: #f8f9fa;">
                      <CurrencyFlag 
                        v-if="templateForm.custom_flag_filename || templateForm.flag_code"
                        :code="templateForm.flag_code" 
                        :custom-filename="templateForm.custom_flag_filename"
                        :width="48" 
                        :height="36"
                        class="flag-icon-large" />

                      <span v-else class="text-muted">
                        {{ $t('currencyManagement.noFlagSelected') }}
                      </span>
                    </div>
                  </div>
                </div>
              </div>

              <div class="mb-3">
                <label class="form-label">{{ $t('currencyManagement.description') }}</label>
                <textarea 
                  class="form-control"
                  v-model="templateForm.description"
                  :placeholder="$t('currencyManagement.descriptionPlaceholder')"
                  rows="3"></textarea>
              </div>
            </form>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              {{ $t('common.cancel') }}
            </button>
            <button 
              type="button" 
              class="btn btn-primary"
              @click="saveTemplate"
              :disabled="saving">
              <span v-if="saving" class="spinner-border spinner-border-sm me-2"></span>
              {{ isEdit ? $t('common.update') : $t('common.save') }}
            </button>
          </div>
        </div>
      </div>
    </div>

    <!-- 删除确认模态框 -->
    <div class="modal fade" id="deleteModal" tabindex="-1">
      <div class="modal-dialog">
        <div class="modal-content">
          <div class="modal-header">
            <h5 class="modal-title">{{ $t('common.confirmDelete') }}</h5>
            <button type="button" class="btn-close" data-bs-dismiss="modal"></button>
          </div>
          <div class="modal-body">
            <p v-if="deleteTarget">
              {{ $t('currencyManagement.deleteConfirmMessage', { 
                currencyCode: deleteTarget.currency_code,
                currencyName: deleteTarget.currency_name 
              }) }}
            </p>
          </div>
          <div class="modal-footer">
            <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">
              {{ $t('common.cancel') }}
            </button>
            <button 
              type="button" 
              class="btn btn-danger"
              @click="deleteTemplate"
              :disabled="deleting">
              <span v-if="deleting" class="spinner-border spinner-border-sm me-2"></span>
              {{ $t('common.delete') }}
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script>
/* global bootstrap */
import { ref, reactive, onMounted, getCurrentInstance } from 'vue'
import { useI18n } from 'vue-i18n'
import CurrencyFlag from '@/components/CurrencyFlag.vue'
import currencyManagementService from '@/services/api/currencyManagementService'
import { getCurrencyName } from '@/utils/currencyTranslator'
import { getCountryName } from '@/utils/countryTranslator'

export default {
  name: 'CurrencyManagementView',
  components: {
    CurrencyFlag
  },
  setup() {
    const { t, locale } = useI18n();
    const instance = getCurrentInstance();
    const templates = ref([]);
    const loading = ref(false);
    const saving = ref(false);
    const deleting = ref(false);
    const isEdit = ref(false);
    const deleteTarget = ref(null);
    const selectedCountry = ref('');
    const selectedCurrency = ref('');
    
    // 过滤相关
    const filterStatus = ref('all');
    const filteredTemplates = ref([]);
    
    // 翻译函数
    const getCurrencyNameTranslated = (currencyCode, fallbackName, customFlagFilename) => {
      // 🌟 自定义币种逻辑：如果有自定义图标，直接使用数据库中的名称
      if (customFlagFilename) {
        // console.log(`[自定义币种] ${currencyCode} 使用数据库名称: ${fallbackName}`);
        return fallbackName || currencyCode;
      }
      
      // 优先使用翻译，而不是数据库中的值
      const currentLang = locale.value === 'zh-CN' ? 'zh' : locale.value === 'en-US' ? 'en' : 'th';
      const translatedName = getCurrencyName(currencyCode, currentLang, null);
      if (translatedName && translatedName !== currencyCode) {
        return translatedName;
      }
      // 如果没有翻译，使用数据库中的自定义名称
      if (fallbackName) {
        return fallbackName;
      }
      return currencyCode;
    };
    
    const getCountryNameTranslated = (countryName) => {
      if (!countryName) return '';
      
      // 优先使用翻译，而不是数据库中的值
      const currentLang = locale.value === 'zh-CN' ? 'zh' : locale.value === 'en-US' ? 'en' : 'th';
      const translatedName = getCountryName(countryName, currentLang);
      if (translatedName && translatedName !== countryName) {
        return translatedName;
      }
      // 如果没有翻译，使用数据库中的自定义名称
      if (countryName && countryName !== '') {
        return countryName;
      }
      return countryName;
    };
    
    // 添加ISO数据
    const countries = ref([]);
    const currencies = ref([]);
    
    const templateForm = reactive({
      id: null,
      currency_code: '',
      currency_name: '',
      country: '',
      flag_code: '',
      symbol: '',
      description: '',
      custom_flag_filename: ''
    });

    // Toast 提示函数
    const showToast = (message, type = 'info') => {
      console.log(`[${type.toUpperCase()}] ${message}`);
      // 检查是否有全局toast
      if (instance?.proxy?.$toast) {
        instance.proxy.$toast[type](message);
      } else {
        // 降级到alert
        if (type === 'error') {
          alert('❌ ' + t('common.error') + ': ' + message);
        } else if (type === 'success') {
          alert('✅ ' + t('common.success') + ': ' + message);
        } else {
          alert('ℹ️ ' + t('common.info') + ': ' + message);
        }
      }
    };

    // 加载ISO数据
    const loadISOData = async () => {
      try {
        // 加载国家数据
        const countriesResponse = await currencyManagementService.getISOCountries();
        if (countriesResponse.data.success) {
          countries.value = countriesResponse.data.countries || [];
        }
        
        // 加载货币数据
        const currenciesResponse = await currencyManagementService.getISOCurrencies();
        if (currenciesResponse.data.success) {
          currencies.value = currenciesResponse.data.currencies || [];
        }
      } catch (error) {
        console.error('Load ISO data failed:', error);
      }
    };

    // 过滤方法
    const applyFilter = () => {
      if (filterStatus.value === 'all') {
        filteredTemplates.value = templates.value;
      } else if (filterStatus.value === 'inUse') {
        filteredTemplates.value = templates.value.filter(template => template.is_in_use);
      } else if (filterStatus.value === 'notInUse') {
        filteredTemplates.value = templates.value.filter(template => !template.is_in_use);
      }
    };

    // 加载币种模板列表
    const loadTemplates = async () => {
      loading.value = true;
      try {
        const response = await currencyManagementService.getCurrencyTemplates();
        templates.value = response.data.templates || [];
        // 初始化过滤后的数据
        applyFilter();
      } catch (error) {
        console.error('Load currency templates failed:', error);
        showToast(t('currencyManagement.messages.loadTemplatesFailed'), 'error');
      } finally {
        loading.value = false;
      }
    };

    // 国家选择事件  
    const onCountrySelect = () => {
      const country = countries.value.find(c => c.code === selectedCountry.value);
      if (country) {
        // 填充国家信息 - 使用翻译后的国家名称
        templateForm.country = getCountryNameTranslated(country.code);
        templateForm.flag_code = country.code;
        
        // 自动联动货币信息
        templateForm.currency_code = country.currency_code || '';
        templateForm.currency_name = getCurrencyNameTranslated(country.currency_code, country.name) || '';
        templateForm.symbol = country.currency_symbol || '';
        
        // 同步货币选择
        selectedCurrency.value = country.currency_code || '';
        
        console.log('Country selected:', getCountryNameTranslated(country.code), 'Currency:', country.currency_code);
      }
    };

    // 货币选择事件
    const onCurrencySelect = () => {
      const currency = currencies.value.find(c => c.code === selectedCurrency.value);
      if (currency) {
        templateForm.currency_code = currency.code;
        templateForm.currency_name = getCurrencyNameTranslated(currency.code, currency.name);
        templateForm.symbol = currency.symbol || getSymbolForCurrency(currency.code);
        
        // 如果货币只属于一个国家，自动填充国家信息
        const countryForCurrency = countries.value.find(c => c.currency_code === selectedCurrency.value);
        if (countryForCurrency) {
          templateForm.country = getCountryNameTranslated(countryForCurrency.code);
          templateForm.flag_code = countryForCurrency.code;
          selectedCountry.value = countryForCurrency.code;
        }
        
        console.log('Currency selected:', getCurrencyNameTranslated(currency.code), 'Country:', getCountryNameTranslated(countryForCurrency?.code));
      }
    };

    // 获取货币符号
    const getSymbolForCurrency = (currencyCode) => {
      const symbolMap = {
        'USD': '$', 'EUR': '€', 'GBP': '£', 'JPY': '¥', 'CNY': '¥',
        'HKD': 'HK$', 'SGD': 'S$', 'AUD': 'A$', 'CAD': 'C$', 'CHF': 'Fr.',
        'KRW': '₩', 'THB': '฿', 'INR': '₹', 'RUB': '₽', 'NZD': 'NZ$'
      };
      return symbolMap[currencyCode] || '';
    };

    // 显示新增模态框
    const showAddModal = () => {
      isEdit.value = false;
      resetForm();
      const modal = new bootstrap.Modal(document.getElementById('templateModal'));
      modal.show();
    };

    // 编辑币种模板
    const editTemplate = (template) => {
      isEdit.value = true;
      Object.assign(templateForm, template);
      selectedCountry.value = '';
      selectedCurrency.value = '';
      const modal = new bootstrap.Modal(document.getElementById('templateModal'));
      modal.show();
    };

    // 重置表单
    const resetForm = () => {
      Object.keys(templateForm).forEach(key => {
        templateForm[key] = key === 'id' ? null : '';
      });
      selectedCountry.value = '';
      selectedCurrency.value = '';
    };

    // 处理图标文件上传
    const onFlagFileChange = async (event) => {
      const file = event.target.files[0];
      if (!file) return;

      // 验证文件类型
      const allowedTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/svg+xml'];
      if (!allowedTypes.includes(file.type)) {
        showToast(t('currencyManagement.messages.invalidFileType'), 'error');
        return;
      }

      // 验证文件大小（最大2MB）
      if (file.size > 2 * 1024 * 1024) {
        showToast(t('currencyManagement.messages.fileTooLarge'), 'error');
        return;
      }

      try {
        // 读取文件为base64
        const base64 = await readFileAsBase64(file);
        
        // 上传到服务器
        const response = await currencyManagementService.uploadFlag({
          file_data: base64,
          filename: file.name
        });

        if (response.data.success) {
          templateForm.custom_flag_filename = response.data.filename;
          console.log('Upload successful, filename set to:', response.data.filename);
          console.log('templateForm.custom_flag_filename is now:', templateForm.custom_flag_filename);
          showToast(t('currencyManagement.messages.flagUploadSuccess'), 'success');
        } else {
          showToast(response.data.message || t('currencyManagement.messages.flagUploadFailed'), 'error');
        }
      } catch (error) {
        console.error('Upload flag failed:', error);
        showToast(t('currencyManagement.messages.flagUploadFailed'), 'error');
      }

      // 清空文件输入
      event.target.value = '';
    };

    // 读取文件为base64
    const readFileAsBase64 = (file) => {
      return new Promise((resolve, reject) => {
        const reader = new FileReader();
        reader.onload = () => resolve(reader.result);
        reader.onerror = reject;
        reader.readAsDataURL(file);
      });
    };

    // 移除自定义图标
    const removeCustomFlag = () => {
      templateForm.custom_flag_filename = '';
      showToast(t('currencyManagement.messages.customFlagRemoved'), 'info');
    };

    // 保存币种模板
    const saveTemplate = async () => {
      if (!templateForm.currency_code || !templateForm.currency_name || 
          !templateForm.country || !templateForm.flag_code) {
        showToast(t('currencyManagement.messages.fillRequiredFields'), 'error');
        return;
      }

      saving.value = true;
      try {
        templateForm.currency_code = templateForm.currency_code.toUpperCase();
        templateForm.flag_code = templateForm.flag_code.toUpperCase();

        let response;
        if (isEdit.value) {
          response = await currencyManagementService.updateCurrencyTemplate(
            templateForm.id, templateForm
          );
        } else {
          response = await currencyManagementService.addCurrencyTemplate(templateForm);
        }

        if (response.data.success) {
          showToast(response.data.message, 'success');
          const modal = bootstrap.Modal.getInstance(document.getElementById('templateModal'));
          if (modal) modal.hide();
          await loadTemplates();
        } else {
          showToast(response.data.message || t('currencyManagement.messages.operationFailed'), 'error');
        }
      } catch (error) {
        console.error('Save currency template failed:', error);
        const message = error.response?.data?.message || t('currencyManagement.messages.saveFailed');
        showToast(message, 'error');
      } finally {
        saving.value = false;
      }
    };

    // 确认删除
    const confirmDelete = (template) => {
      deleteTarget.value = template;
      const modal = new bootstrap.Modal(document.getElementById('deleteModal'));
      modal.show();
    };

    // 删除币种模板
    const deleteTemplate = async () => {
      if (!deleteTarget.value) return;

      deleting.value = true;
      try {
        const response = await currencyManagementService.deleteCurrencyTemplate(
          deleteTarget.value.id
        );

        if (response.data.success) {
          showToast(response.data.message, 'success');
          const modal = bootstrap.Modal.getInstance(document.getElementById('deleteModal'));
          if (modal) modal.hide();
          await loadTemplates();
        } else {
          showToast(response.data.message || t('currencyManagement.messages.deleteFailed'), 'error');
        }
      } catch (error) {
        console.error('Delete currency template failed:', error);
        const message = error.response?.data?.message || t('currencyManagement.messages.deleteFailed');
        showToast(message, 'error');
      } finally {
        deleting.value = false;
        deleteTarget.value = null;
      }
    };

    // 初始化币种模板
    const initTemplates = async () => {
      // 如果已有数据，先询问用户是否强制初始化
      if (templates.value.length > 0) {
        const confirmMessage = t('currencyManagement.messages.initConfirmMessage', { count: templates.value.length });
        if (!confirm(confirmMessage)) {
          return;
        }
      }
      
      loading.value = true;
      try {
        const force = templates.value.length > 0; // 如果有数据就使用force
        const response = await currencyManagementService.initCurrencyTemplates(force);
        if (response.data.success) {
          showToast(response.data.message, 'success');
          await loadTemplates();
        } else {
          showToast(response.data.message || t('currencyManagement.messages.initFailed'), 'error');
        }
      } catch (error) {
        console.error('Initialize currency templates failed:', error);
        const message = error.response?.data?.message || t('currencyManagement.messages.initFailed');
        showToast(message, 'error');
      } finally {
        loading.value = false;
      }
    };

    onMounted(async () => {
      await loadISOData();
      await loadTemplates();
    });

    return {
      t,
      templates,
      filteredTemplates,
      filterStatus,
      loading,
      saving,
      deleting,
      isEdit,
      deleteTarget,
      templateForm,
      selectedCountry,
      selectedCurrency,
      countries,
      currencies,
      onCurrencySelect,
      onCountrySelect,
      onFlagFileChange,
      removeCustomFlag,
      showAddModal,
      editTemplate,
      resetForm,
      saveTemplate,
      confirmDelete,
      deleteTemplate,
      initTemplates,
      applyFilter,
      getCurrencyNameTranslated,
      getCountryNameTranslated
    }
  }
}
</script>

<style scoped>
.currency-management-container {
  padding: 20px;
}

.btn-gradient {
  background: linear-gradient(45deg, #28a745, #20c997);
  border: none;
  color: white;
  transition: all 0.3s ease;
}

.btn-gradient:hover {
  transform: translateY(-2px);
  box-shadow: 0 4px 12px rgba(40, 167, 69, 0.3);
  color: white;
}

.card {
  border: none;
  border-radius: 10px;
}

.card-body {
  padding: 1.5rem;
}

.table th {
  font-weight: 600;
  color: #495057;
  border-bottom: 2px solid #dee2e6;
  vertical-align: middle;
  padding: 12px 8px;
}

.table td {
  vertical-align: middle;
  padding: 12px 8px;
}

.flag-icon {
  border-radius: 3px;
  box-shadow: 0 1px 3px rgba(0,0,0,0.2);
}

.flag-icon-large {
  border-radius: 4px;
  box-shadow: 0 2px 6px rgba(0,0,0,0.25);
  display: block;
  margin: 0 auto;
}

.currency-symbol {
  font-weight: 600;
  color: #28a745;
}

.badge {
  font-size: 0.85em;
}

.btn-group-sm .btn {
  padding: 0.25rem 0.5rem;
}

.modal-content {
  border-radius: 10px;
  border: none;
}

.modal-header {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border-radius: 10px 10px 0 0;
}

.modal-header .btn-close {
  filter: invert(1);
}

.form-label {
  font-weight: 600;
  color: #495057;
}

.form-control:focus, .form-select:focus {
  border-color: #667eea;
  box-shadow: 0 0 0 0.2rem rgba(102, 126, 234, 0.25);
}

@media (max-width: 768px) {
  .currency-management-container {
    padding: 10px;
  }
  
  .page-header {
    padding: 15px;
  }
  
  .table-responsive {
    font-size: 0.9rem;
  }
}
</style>
 