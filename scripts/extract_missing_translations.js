const fs = require('fs');
const path = require('path');

// 配置路径
const BACKUP_FILE = 'F:\\BAK\\locales\\zh-CN.json';
const CURRENT_EOD_FILE = 'src\\i18n\\modules\\eod\\zh-CN.js';
const CURRENT_QUERIES_FILE = 'src\\i18n\\modules\\queries\\zh-CN.js';

// 需要提取的key模式（基于实际备份文件结构）
const EOD_KEYS = [
  'selected_transactions',
  'foreign_currency_short',
  'local_currency_short',
  'sell_transaction',
  'buy_transaction',
  'reversal_transaction',
  'adjust_balance_transaction',
  'initial_balance_transaction'
];

const QUERIES_KEYS = [
  'initial_balance'
];

function extractNestedValue(obj, keyPath) {
  const keys = keyPath.split('.');
  let current = obj;
  
  for (const key of keys) {
    if (current && typeof current === 'object' && key in current) {
      current = current[key];
    } else {
      return null;
    }
  }
  
  return current;
}

function findKeysInObject(obj, prefix = '') {
  const results = {};
  
  for (const [key, value] of Object.entries(obj)) {
    const fullKey = prefix ? `${prefix}.${key}` : key;
    
    if (typeof value === 'object' && value !== null && !Array.isArray(value)) {
      Object.assign(results, findKeysInObject(value, fullKey));
    } else {
      results[fullKey] = value;
    }
  }
  
  return results;
}

function decodeChineseText(text) {
  // 简单的编码转换，处理常见的编码问题
  if (typeof text !== 'string') return text;
  
  // 这里可能需要根据实际的编码问题进行调整
  // 目前先返回原文本，后续可以根据需要添加解码逻辑
  return text;
}

function main() {
  console.log('=== 翻译key提取和比较工具 ===\n');
  
  try {
    // 读取备份文件
    console.log('1. 读取备份文件...');
    const backupContent = fs.readFileSync(BACKUP_FILE, 'utf8');
    const backupData = JSON.parse(backupContent);
    console.log('✅ 备份文件读取成功\n');
    
    // 提取所有key
    console.log('2. 提取备份文件中的所有key...');
    const backupKeys = findKeysInObject(backupData);
    console.log(`✅ 找到 ${Object.keys(backupKeys).length} 个key\n`);
    
    // 检查EOD相关key
    console.log('3. 检查EOD相关key...');
    const eodResults = {};
    for (const key of EOD_KEYS) {
      const value = backupKeys[key];
      if (value) {
        eodResults[key] = decodeChineseText(value);
        console.log(`✅ 找到: ${key} = "${value}"`);
      } else {
        console.log(`❌ 未找到: ${key}`);
      }
    }
    console.log('');
    
    // 检查queries相关key
    console.log('4. 检查queries相关key...');
    const queriesResults = {};
    for (const key of QUERIES_KEYS) {
      const value = backupKeys[key];
      if (value) {
        queriesResults[key] = decodeChineseText(value);
        console.log(`✅ 找到: ${key} = "${value}"`);
      } else {
        console.log(`❌ 未找到: ${key}`);
      }
    }
    console.log('');
    
    // 搜索包含特定关键词的key
    console.log('5. 搜索包含关键词的key...');
    const searchKeywords = ['selected', 'foreign', 'local', 'sell', 'buy', 'reversal', 'adjust', 'initial'];
    const foundKeys = {};
    
    for (const [key, value] of Object.entries(backupKeys)) {
      for (const keyword of searchKeywords) {
        if (key.toLowerCase().includes(keyword.toLowerCase())) {
          foundKeys[key] = value;
          console.log(`🔍 找到相关key: ${key} = "${value}"`);
        }
      }
    }
    console.log('');
    
    // 生成补充代码
    console.log('6. 生成补充代码...\n');
    
    if (Object.keys(eodResults).length > 0) {
      console.log('=== EOD模块补充代码 ===');
      console.log('// 添加到 src/i18n/modules/eod/zh-CN.js 的step5部分:');
      console.log('"step5": {');
      for (const [key, value] of Object.entries(eodResults)) {
        console.log(`  "${key}": "${value}",`);
      }
      console.log('},');
      console.log('');
    }
    
    if (Object.keys(queriesResults).length > 0) {
      console.log('=== Queries模块补充代码 ===');
      console.log('// 添加到 src/i18n/modules/queries/zh-CN.js:');
      for (const [key, value] of Object.entries(queriesResults)) {
        console.log(`"${key}": "${value}",`);
      }
      console.log('');
    }
    
    // 保存结果到文件
    const outputFile = 'missing_translations.json';
    const outputData = {
      eod: eodResults,
      queries: queriesResults,
      foundKeys: foundKeys,
      timestamp: new Date().toISOString()
    };
    
    fs.writeFileSync(outputFile, JSON.stringify(outputData, null, 2), 'utf8');
    console.log(`✅ 结果已保存到 ${outputFile}`);
    
    // 显示所有找到的相关key
    console.log('\n=== 所有相关key ===');
    for (const [key, value] of Object.entries(foundKeys)) {
      console.log(`${key}: "${value}"`);
    }
    
  } catch (error) {
    console.error('❌ 错误:', error.message);
  }
}

main(); 