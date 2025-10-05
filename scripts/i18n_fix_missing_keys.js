#!/usr/bin/env node

/**
 * ExchangeOK i18n 修复缺失翻译key脚本
 * 直接修复模块文件中的缺失key
 */

const fs = require('fs');
const path = require('path');

const MODULES_DIR = path.join(__dirname, '../src/i18n/modules');
const SRC_LAST_DIR = path.join(__dirname, '../src_last/i18n');
const LOCALES = ['zh-CN', 'en-US', 'th-TH'];

function loadLocaleObj(filePath) {
  if (!fs.existsSync(filePath)) return {};
  let content = fs.readFileSync(filePath, 'utf8');
  content = content.replace(/^\s*export\s+default\s+/, '').replace(/;\s*$/, '');
  // eslint-disable-next-line no-eval
  return eval('(' + content + ')');
}

function saveModuleFile(moduleName, locale, obj) {
  const dir = path.join(MODULES_DIR, moduleName);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, `${locale}.js`);
  const code = `// ${moduleName}模块 - ${locale}翻译\nexport default ${JSON.stringify({ [moduleName]: obj }, null, 2)}`;
  fs.writeFileSync(file, code, 'utf8');
}

function fixMissingKeys() {
  console.log('🔧 修复模块翻译key...\n');
  
  // 从src_last加载完整版本
  const srcLastObjs = {};
  for (const locale of LOCALES) {
    const file = path.join(SRC_LAST_DIR, 'locales', `${locale}.js`);
    srcLastObjs[locale] = loadLocaleObj(file);
  }
  
  // 需要修复的key映射
  const missingKeysMap = {
    'dashboard': [
      'loading',
      'loading_data', 
      'no_business_stats',
      'reload',
      'no_data',
      'no_eod_data',
      'no_unresolved_alerts'
    ],
    'eod': [
      'eod_status',
      'status.processing'
    ],
    'rates': [
      'currency_count'
    ]
  };
  
  // 修复每个模块
  for (const [moduleName, keys] of Object.entries(missingKeysMap)) {
    console.log(`处理 ${moduleName} 模块...`);
    
    for (const locale of LOCALES) {
      const moduleFile = path.join(MODULES_DIR, moduleName, `${locale}.js`);
      let currentModule = {};
      
      if (fs.existsSync(moduleFile)) {
        try {
          const moduleContent = loadLocaleObj(moduleFile);
          currentModule = moduleContent[moduleName] || {};
        } catch (error) {
          console.log(`  跳过 ${locale} (解析错误): ${error.message}`);
          continue;
        }
      }
      
      let hasChanges = false;
      
      // 修复缺失的key
      for (const keyPath of keys) {
        const keyParts = keyPath.split('.');
        
        if (keyParts.length === 1) {
          // 一级key
          const key = keyParts[0];
          if (!currentModule[key]) {
            // 从src_last获取
            if (srcLastObjs[locale] && 
                srcLastObjs[locale][moduleName] && 
                srcLastObjs[locale][moduleName][key]) {
              currentModule[key] = srcLastObjs[locale][moduleName][key];
              console.log(`  补充 ${locale} ${moduleName}.${key}: ${currentModule[key]}`);
            } else {
              // 使用占位符
              currentModule[key] = `[${locale}] ${key}`;
              console.log(`  补充 ${locale} ${moduleName}.${key}: [占位符]`);
            }
            hasChanges = true;
          }
        } else if (keyParts.length === 2) {
          // 二级key: status.processing
          const subKey = keyParts[0];
          const finalKey = keyParts[1];
          
          if (!currentModule[subKey]) {
            currentModule[subKey] = {};
          }
          
          if (!currentModule[subKey][finalKey]) {
            // 从src_last获取
            if (srcLastObjs[locale] && 
                srcLastObjs[locale][moduleName] && 
                srcLastObjs[locale][moduleName][subKey] && 
                srcLastObjs[locale][moduleName][subKey][finalKey]) {
              currentModule[subKey][finalKey] = srcLastObjs[locale][moduleName][subKey][finalKey];
              console.log(`  补充 ${locale} ${moduleName}.${subKey}.${finalKey}: ${currentModule[subKey][finalKey]}`);
            } else {
              // 使用占位符
              currentModule[subKey][finalKey] = `[${locale}] ${finalKey}`;
              console.log(`  补充 ${locale} ${moduleName}.${subKey}.${finalKey}: [占位符]`);
            }
            hasChanges = true;
          }
        }
      }
      
      // 保存修改
      if (hasChanges) {
        saveModuleFile(moduleName, locale, currentModule);
        console.log(`  ✅ ${locale} 已更新`);
      } else {
        console.log(`  ✓ ${locale} 无需更新`);
      }
    }
  }
  
  console.log('\n✅ 模块key修复完成！');
}

if (require.main === module) {
  try {
    fixMissingKeys();
  } catch (error) {
    console.error('❌ 修复失败:', error.message);
  }
}

module.exports = { fixMissingKeys }; 