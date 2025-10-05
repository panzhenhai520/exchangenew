<template>
  <span 
    class="currency-flag"
    :style="flagStyle"
  >
    <img
      :src="flagSrc"
      :alt="code"
      @error="handleError"
      style="width: 100%; height: 100%;"
    />
  </span>
</template>

<script>
// 使用 Map 对象来存储货币代码映射
const currencyToCountry = new Map([
  ['USD', 'us'],
  ['EUR', 'eu'],
  ['GBP', 'gb'],
  ['JPY', 'jp'],
  ['CNY', 'cn'],
  ['HKD', 'hk'],
  ['TWD', 'tw'],
  ['KRW', 'kr'],
  ['SGD', 'sg'],
  ['THB', 'th'],
  ['IDR', 'id'],
  ['MYR', 'my'],
  ['PHP', 'ph'],
  ['INR', 'in'],
  ['AUD', 'au'],
  ['NZD', 'nz'],
  ['CAD', 'ca'],
  ['CHF', 'ch'],
  ['SEK', 'se'],
  ['DKK', 'dk'],
  ['NOK', 'no'],
  ['RUB', 'ru'],
  ['AED', 'ae'],
  ['SAR', 'sa'],
  ['BRL', 'br'],
  ['ZAR', 'za'],
  ['TRY', 'tr'],
  ['MXN', 'mx'],
  ['PLN', 'pl'],
  ['VND', 'vn'],
  ['BND', 'bn'],
  ['BHD', 'bh']
]);

export default {
  name: 'CurrencyFlag',
  props: {
    code: {
      type: String,
      required: true,
      validator: function(value) {
        return typeof value === 'string' && value.length > 0;
      }
    },
    customFilename: {
      type: String,
      default: ''
    },
    width: {
      type: [String, Number],
      default: '24'
    },
    height: {
      type: [String, Number],
      default: '16'
    }
  },
  data() {
    return {
      hasError: false,
      basePath: process.env.BASE_URL || '/'
    };
  },
  computed: {
    flagStyle() {
      return {
        width: typeof this.width === 'number' ? `${this.width}px` : this.width,
        height: typeof this.height === 'number' ? `${this.height}px` : this.height,
        display: 'inline-block',
        verticalAlign: 'middle',
        overflow: 'hidden',
        borderRadius: '2px',
        border: '1px solid #ddd',
        backgroundColor: '#fff'
      };
    },
    normalizedCode() {
      return (this.code || '').trim().toUpperCase();
    },
    flagSrc() {
      if (this.hasError) {
        return `/flags/unknown.svg`;
      }

      // 优先使用自定义图标
      if (this.customFilename) {

        return `/flags/${this.customFilename}`;
      }

      const inputCode = this.normalizedCode;
      if (!inputCode) {
        console.warn('Empty code provided');
        return `/flags/unknown.svg`;
      }

      // 首先检查是否是2位的国家代码（flag_code）
      if (inputCode.length === 2) {
        return `/flags/${inputCode.toLowerCase()}.svg`;
      }

      // 如果是3位代码，尝试从货币代码映射到国家代码
      const countryCode = currencyToCountry.get(inputCode);
      if (countryCode) {
        return `/flags/${countryCode.toLowerCase()}.svg`;
      }

      console.warn(`No country code mapping for: ${inputCode}`);
      return `/flags/unknown.svg`;
    }
  },
  methods: {
    handleError(e) {
      console.warn(`Failed to load flag for currency: ${this.normalizedCode}, customFilename: ${this.customFilename}`, e);
      this.hasError = true;
    },
    resetError() {
      this.hasError = false;
    }
  },
  watch: {
    code: {
      immediate: true,
      handler() {
        this.hasError = false;
      }
    },
    customFilename: {
      immediate: true,
      handler() {
        this.hasError = false;
      }
    }
  }
};
</script>

<style scoped>
.currency-flag {
  display: inline-block;
  vertical-align: middle;
  line-height: 0;
}

.currency-flag img {
  display: block;
  max-width: 100%;
  height: auto;
}
</style> 