import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import router from './router'
import api, { setGlobalI18n } from './services/api'
import i18n from './i18n'
import pageLogMixin from './mixins/pageLogMixin'
import 'bootstrap/dist/css/bootstrap.min.css'
import 'bootstrap/dist/js/bootstrap.bundle.min.js'
import './assets/main.css'
import * as bootstrap from 'bootstrap'

// 将bootstrap挂载到全局对象上
window.bootstrap = bootstrap

// Font Awesome
import { library } from '@fortawesome/fontawesome-svg-core'
import { fas } from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon } from '@fortawesome/vue-fontawesome'

// Add all icons to library
library.add(fas)

// Toast 提示功能
const Toast = {
  show(message, type = 'info', duration = 3000) {
    // 创建toast容器
    let container = document.querySelector('.toast-container')
    if (!container) {
      container = document.createElement('div')
      container.className = 'toast-container position-fixed top-0 end-0 p-3'
      container.style.zIndex = '1055'
      document.body.appendChild(container)
    }

    // 创建toast元素
    const toastId = 'toast-' + Date.now()
    const toastHtml = `
      <div id="${toastId}" class="toast" role="alert" aria-live="assertive" aria-atomic="true">
        <div class="toast-header">
          <div class="rounded me-2 ${getTypeColor(type)}" style="width: 20px; height: 20px;"></div>
          <strong class="me-auto">${getTypeTitle(type)}</strong>
          <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
          ${message}
        </div>
      </div>
    `
    
    container.insertAdjacentHTML('beforeend', toastHtml)
    
    // 显示toast
    const toastElement = document.getElementById(toastId)
    const toast = new bootstrap.Toast(toastElement, {
      delay: duration
    })
    toast.show()
    
    // 自动移除
    toastElement.addEventListener('hidden.bs.toast', () => {
      toastElement.remove()
    })
  },
  
  success(message, duration = 3000) {
    this.show(message, 'success', duration)
  },
  
  error(message, duration = 5000) {
    this.show(message, 'danger', duration)
  },
  
  warning(message, duration = 4000) {
    this.show(message, 'warning', duration)
  },
  
  info(message, duration = 3000) {
    this.show(message, 'info', duration)
  }
}

function getTypeColor(type) {
  const colors = {
    success: 'bg-success',
    danger: 'bg-danger',
    warning: 'bg-warning',
    info: 'bg-info'
  }
  return colors[type] || 'bg-info'
}

function getTypeTitle(type) {
  // 使用i18n实例获取翻译，添加安全检查
  const getTranslation = (key) => {
    try {
      return i18n.global.t(key)
    } catch (error) {
      // 如果i18n还没有初始化，返回默认值
      const fallbackTitles = {
        success: '成功',
        danger: '错误',
        warning: '警告',
        info: '提示'
      }
      return fallbackTitles[type] || '提示'
    }
  }
  
  const titles = {
    success: getTranslation('common.success_title'),
    danger: getTranslation('common.error_title'),
    warning: getTranslation('common.warning_title'),
    info: getTranslation('common.info_title')
  }
  return titles[type] || getTranslation('common.info_title')
}

const app = createApp(App)
const pinia = createPinia()

app.component('font-awesome-icon', FontAwesomeIcon)
app.config.globalProperties.$api = api
app.config.globalProperties.$toast = Toast

// 注册全局页面访问日志 Mixin
app.mixin(pageLogMixin)

app.use(router)
app.use(pinia)
app.use(i18n)

// 设置全局i18n实例用于API错误翻译
setGlobalI18n(i18n.global)

app.mount('#app')
