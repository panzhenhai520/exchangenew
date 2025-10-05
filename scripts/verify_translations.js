#!/usr/bin/env node

/**
 * ExchangeOK 翻译验证脚本
 * 用于检查翻译键的完整性和一致性
 */

const fs = require('fs');
const path = require('path');

const I18N_DIR = path.join(__dirname, '../src/i18n');

function loadTranslationFile(filePath) {
  try {
    const content = fs.readFileSync(filePath, 'utf8');
    // 简单的键提取，实际项目中可能需要更复杂的解析
    const keys = new Set();
    const lines = content.split('\n');
    
    for (const line of lines) {
      // 匹配翻译键模式
      const keyMatch = line.match(/^\s*([a-zA-Z_][a-zA-Z0-9_]*):\s*['"`]/);
      if (keyMatch) {
        keys.add(keyMatch[1]);
      }
    }
    
    return keys;
  } catch (error) {
    console.error(`❌ 读取文件失败: ${filePath}`, error.message);
    return new Set();
  }
}

function extractNestedKeys(obj, prefix = '') {
  const keys = new Set();
  
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    keys.add(fullKey);
    
    if (value && typeof value === 'object' && !Array.isArray(value)) {
      const nestedKeys = extractNestedKeys(value, fullKey);
      nestedKeys.forEach(k => keys.add(k));
    }
  }
  
  return keys;
}

function verifyTranslations() {
  console.log('🔍 ExchangeOK 翻译验证工具\n');
  
  const locales = ['zh-CN', 'en-US', 'th-TH'];
  const translationFiles = {};
  
  // 加载所有翻译文件
  for (const locale of locales) {
    const filePath = path.join(I18N_DIR, 'locales', `${locale}.js`);
    if (fs.existsSync(filePath)) {
      console.log(`✅ 加载 ${locale} 翻译文件`);
      translationFiles[locale] = filePath;
    } else {
      console.log(`❌ 缺失 ${locale} 翻译文件`);
    }
  }
  
  // 检查关键命名空间
  const criticalNamespaces = [
    'exchange',
    'eod', 
    'reports',
    'currencyManagement',
    'dashboard',
    'auth',
    'system',
    'common',
    'menu'
  ];
  
  console.log('\n📋 检查关键命名空间...');
  
  for (const locale of locales) {
    if (translationFiles[locale]) {
      const content = fs.readFileSync(translationFiles[locale], 'utf8');
      console.log(`\n${locale}:`);
      
      for (const namespace of criticalNamespaces) {
        if (content.includes(`${namespace}: {`)) {
          console.log(`  ✅ ${namespace}`);
        } else {
          console.log(`  ❌ ${namespace} (缺失)`);
        }
      }
    }
  }
  
  // 检查文件大小
  console.log('\n📊 文件大小统计:');
  for (const locale of locales) {
    if (translationFiles[locale]) {
      const stats = fs.statSync(translationFiles[locale]);
      const sizeKB = (stats.size / 1024).toFixed(1);
      console.log(`  ${locale}: ${sizeKB} KB`);
    }
  }
  
  // 检查特定键的存在
  console.log('\n🔑 检查关键翻译键...');
  const criticalKeys = [
    'exchange.title',
    'exchange.select_foreign_currency',
    'exchange.customer_payment',
    'eod.title',
    'eod.step1',
    'reports.title',
    'currencyManagement.title'
  ];
  
  for (const locale of locales) {
    if (translationFiles[locale]) {
      const content = fs.readFileSync(translationFiles[locale], 'utf8');
      console.log(`\n${locale}:`);
      
      for (const key of criticalKeys) {
        const keyParts = key.split('.');
        const namespace = keyParts[0];
        const subKey = keyParts[1];
        
        if (content.includes(`${namespace}: {`) && content.includes(`${subKey}:`)) {
          console.log(`  ✅ ${key}`);
        } else {
          console.log(`  ❌ ${key} (缺失)`);
        }
      }
    }
  }
  
  console.log('\n✅ 翻译验证完成');
}

function main() {
  const command = process.argv[2];
  
  switch (command) {
    case 'verify':
      verifyTranslations();
      break;
      
    default:
      console.log('使用方法:');
      console.log('  node verify_translations.js verify - 验证翻译完整性');
      break;
  }
}

if (require.main === module) {
  main();
}

module.exports = {
  verifyTranslations
}; 