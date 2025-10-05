<template>
  <div class="language-switcher">
    <div class="dropdown">
      <button 
        class="btn btn-outline-light btn-sm dropdown-toggle" 
        type="button" 
        @click="toggleDropdown"
        ref="dropdownToggle"
      >
        <font-awesome-icon :icon="['fas', 'globe']" class="me-1" />
        {{ languages.find(lang => lang.code === currentLanguage)?.name || '中文' }}
      </button>
      <ul class="dropdown-menu dropdown-menu-end" :class="{ show: isOpen }" ref="dropdownMenu">
        <li v-for="lang in languages" :key="lang.code">
          <a 
            class="dropdown-item" 
            :class="{ active: currentLanguage === lang.code }" 
            href="#" 
            @click.prevent="changeLanguage(lang.code)"
          >
            {{ lang.name }}
          </a>
        </li>
      </ul>
    </div>
  </div>
</template>

<script>
export default {
  name: 'LanguageSwitcher',
  props: {
    currentLanguage: {
      type: String,
      default: 'zh-CN'
    }
  },
  data() {
    return {
      isOpen: false,
      languages: [
        { code: 'zh-CN', name: '中文' },
        { code: 'en-US', name: 'English' },
        { code: 'th-TH', name: 'ไทย' }
      ]
    };
  },
  mounted() {
    // 添加全局点击事件来关闭下拉菜单
    document.addEventListener('click', this.handleClickOutside);
  },
  beforeUnmount() {
    // 清理事件监听器
    document.removeEventListener('click', this.handleClickOutside);
  },
  methods: {
    toggleDropdown(event) {
      event.preventDefault();
      event.stopPropagation();
      this.isOpen = !this.isOpen;
    },
    changeLanguage(langCode) {
      this.isOpen = false;
      this.$emit('language-change', langCode);
    },
    handleClickOutside(event) {
      if (!this.$el.contains(event.target)) {
        this.isOpen = false;
      }
    }
  }
};
</script>

<style scoped>
.language-switcher {
  display: inline-block;
}
.dropdown-item.active {
  background-color: #0d6efd;
  color: white;
}
</style>
