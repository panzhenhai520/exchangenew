#!/usr/bin/env node

/**
 * ExchangeOK i18n 补充缺失翻译key脚本
 * 从src_last版本补充缺失的翻译key到当前版本
 */

const fs = require('fs');
const path = require('path');

const I18N_DIR = path.join(__dirname, '../src/i18n');
const SRC_LAST_DIR = path.join(__dirname, '../src_last/i18n');
const LOCALES = ['zh-CN', 'en-US', 'th-TH'];

function loadLocaleObj(filePath) {
  if (!fs.existsSync(filePath)) return {};
  let content = fs.readFileSync(filePath, 'utf8');
  content = content.replace(/^\s*export\s+default\s+/, '').replace(/;\s*$/, '');
  // eslint-disable-next-line no-eval
  return eval('(' + content + ')');
}

function saveLocaleObj(filePath, obj) {
  const code = `export default ${JSON.stringify(obj, null, 2)}`;
  fs.writeFileSync(filePath, code, 'utf8');
}

function supplementMissingKeys() {
  console.log('🔧 补充缺失的翻译key...\n');
  
  // 从src_last加载完整版本
  const srcLastObjs = {};
  for (const locale of LOCALES) {
    const file = path.join(SRC_LAST_DIR, 'locales', `${locale}.js`);
    srcLastObjs[locale] = loadLocaleObj(file);
  }
  
  // 加载当前版本
  const currentObjs = {};
  for (const locale of LOCALES) {
    const file = path.join(I18N_DIR, 'locales', `${locale}.js`);
    currentObjs[locale] = loadLocaleObj(file);
  }
  
  // 需要补充的key列表（从控制台错误中发现的）
  const missingKeys = [
    // EOD相关
    'eod.eod_status',
    'eod.status.pending',
    
    // Dashboard相关
    'dashboard.no_business_stats',
    'dashboard.loading_business_stats',
    'dashboard.reload',
    'dashboard.no_data',
    'dashboard.no_eod_data',
    
    // Rates相关
    'rates.currency_count'
  ];
  
  // 补充缺失的key
  for (const locale of LOCALES) {
    console.log(`处理 ${locale}...`);
    let hasChanges = false;
    
    for (const keyPath of missingKeys) {
      const keys = keyPath.split('.');
      const namespace = keys[0];
      const subKey = keys[1];
      const finalKey = keys[2];
      
      // 确保命名空间存在
      if (!currentObjs[locale][namespace]) {
        currentObjs[locale][namespace] = {};
        hasChanges = true;
      }
      
      // 检查并补充缺失的key
      if (finalKey) {
        // 三级key: eod.status.pending
        if (!currentObjs[locale][namespace][subKey]) {
          currentObjs[locale][namespace][subKey] = {};
        }
        if (!currentObjs[locale][namespace][subKey][finalKey]) {
          // 从src_last获取
          if (srcLastObjs[locale] && 
              srcLastObjs[locale][namespace] && 
              srcLastObjs[locale][namespace][subKey] && 
              srcLastObjs[locale][namespace][subKey][finalKey]) {
            currentObjs[locale][namespace][subKey][finalKey] = srcLastObjs[locale][namespace][subKey][finalKey];
            console.log(`  补充 ${keyPath}: ${currentObjs[locale][namespace][subKey][finalKey]}`);
            hasChanges = true;
          } else {
            // 使用占位符
            currentObjs[locale][namespace][subKey][finalKey] = `[${locale}] ${finalKey}`;
            console.log(`  补充 ${keyPath}: [占位符]`);
            hasChanges = true;
          }
        }
      } else {
        // 二级key: eod.eod_status, dashboard.no_business_stats
        if (!currentObjs[locale][namespace][subKey]) {
          // 从src_last获取
          if (srcLastObjs[locale] && 
              srcLastObjs[locale][namespace] && 
              srcLastObjs[locale][namespace][subKey]) {
            currentObjs[locale][namespace][subKey] = srcLastObjs[locale][namespace][subKey];
            console.log(`  补充 ${keyPath}: ${currentObjs[locale][namespace][subKey]}`);
            hasChanges = true;
          } else {
            // 使用占位符
            currentObjs[locale][namespace][subKey] = `[${locale}] ${subKey}`;
            console.log(`  补充 ${keyPath}: [占位符]`);
            hasChanges = true;
          }
        }
      }
    }
    
    // 保存修改
    if (hasChanges) {
      const file = path.join(I18N_DIR, 'locales', `${locale}.js`);
      saveLocaleObj(file, currentObjs[locale]);
      console.log(`  ✅ ${locale} 已更新`);
    } else {
      console.log(`  ✓ ${locale} 无需更新`);
    }
  }
  
  console.log('\n✅ 缺失key补充完成！');
}

if (require.main === module) {
  try {
    supplementMissingKeys();
  } catch (error) {
    console.error('❌ 补充失败:', error.message);
  }
}

module.exports = { supplementMissingKeys }; 