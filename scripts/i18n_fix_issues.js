#!/usr/bin/env node

/**
 * ExchangeOK i18n 问题修复脚本
 * 修复缺失的翻译键和结构问题
 */

const fs = require('fs');
const path = require('path');

const I18N_DIR = path.join(__dirname, '../src/i18n');
const LOCALES = ['zh-CN', 'en-US', 'th-TH'];

function loadLocaleObj(locale) {
  const file = path.join(I18N_DIR, 'locales', `${locale}.js`);
  if (!fs.existsSync(file)) throw new Error(`缺失翻译文件: ${file}`);
  let content = fs.readFileSync(file, 'utf8');
  content = content.replace(/^\s*export\s+default\s+/, '').replace(/;\s*$/, '');
  // eslint-disable-next-line no-eval
  return eval('(' + content + ')');
}

function saveLocaleObj(locale, obj) {
  const file = path.join(I18N_DIR, 'locales', `${locale}.js`);
  const code = `export default ${JSON.stringify(obj, null, 2)}`;
  fs.writeFileSync(file, code, 'utf8');
}

function fixMissingNamespaces() {
  console.log('🔧 修复缺失的命名空间...');
  
  const localeObjs = {};
  for (const locale of LOCALES) {
    localeObjs[locale] = loadLocaleObj(locale);
  }
  
  // 为th-TH补充auth命名空间
  if (!localeObjs['th-TH'].auth) {
    console.log('  为th-TH补充auth命名空间');
    localeObjs['th-TH'].auth = {
      login_required: 'ต้องเข้าสู่ระบบ',
      access_denied: 'ปฏิเสธการเข้าถึง',
      session_expired: 'เซสชันหมดอายุ',
      invalid_token: 'โทเค็นไม่ถูกต้อง',
      permission_denied: 'ไม่มีสิทธิ์',
      unauthorized: 'ไม่ได้รับอนุญาต',
      forbidden: 'ห้ามเข้าถึง'
    };
  }
  
  // 为th-TH补充system命名空间
  if (!localeObjs['th-TH'].system) {
    console.log('  为th-TH补充system命名空间');
    localeObjs['th-TH'].system = {
      error: 'ข้อผิดพลาดระบบ',
      success: 'สำเร็จ',
      warning: 'คำเตือน',
      info: 'ข้อมูล'
    };
  }
  
  // 保存修复后的文件
  for (const locale of LOCALES) {
    saveLocaleObj(locale, localeObjs[locale]);
  }
}

function fixStepKeys() {
  console.log('🔧 修复step6-8键结构...');
  
  const localeObjs = {};
  for (const locale of LOCALES) {
    localeObjs[locale] = loadLocaleObj(locale);
  }
  
  // 将step6, step7, step8移动到eod命名空间下
  for (const locale of LOCALES) {
    if (localeObjs[locale].step6 || localeObjs[locale].step7 || localeObjs[locale].step8) {
      console.log(`  处理${locale}的step键`);
      
      // 确保eod命名空间存在
      if (!localeObjs[locale].eod) {
        localeObjs[locale].eod = {};
      }
      
      // 移动step6
      if (localeObjs[locale].step6) {
        localeObjs[locale].eod.step6 = localeObjs[locale].step6;
        delete localeObjs[locale].step6;
      }
      
      // 移动step7
      if (localeObjs[locale].step7) {
        localeObjs[locale].eod.step7 = localeObjs[locale].step7;
        delete localeObjs[locale].step7;
      }
      
      // 移动step8
      if (localeObjs[locale].step8) {
        localeObjs[locale].eod.step8 = localeObjs[locale].step8;
        delete localeObjs[locale].step8;
      }
    }
  }
  
  // 保存修复后的文件
  for (const locale of LOCALES) {
    saveLocaleObj(locale, localeObjs[locale]);
  }
}

function analyzeEodDifferences() {
  console.log('🔍 分析EOD模块键数量差异...');
  
  const localeObjs = {};
  for (const locale of LOCALES) {
    localeObjs[locale] = loadLocaleObj(locale);
  }
  
  const eodKeys = {};
  for (const locale of LOCALES) {
    eodKeys[locale] = localeObjs[locale].eod ? Object.keys(localeObjs[locale].eod) : [];
  }
  
  // 找出所有EOD键
  const allEodKeys = new Set();
  for (const locale of LOCALES) {
    eodKeys[locale].forEach(key => allEodKeys.add(key));
  }
  
  // 分析缺失的键
  for (const locale of LOCALES) {
    const missingKeys = Array.from(allEodKeys).filter(key => !eodKeys[locale].includes(key));
    if (missingKeys.length > 0) {
      console.log(`  ${locale} 缺失EOD键: ${missingKeys.length}个`);
      console.log(`    缺失: ${missingKeys.join(', ')}`);
    }
  }
  
  return { eodKeys, allEodKeys };
}

function fixEodKeys() {
  console.log('🔧 修复EOD模块键数量差异...');
  
  const localeObjs = {};
  for (const locale of LOCALES) {
    localeObjs[locale] = loadLocaleObj(locale);
  }
  
  // 确保所有语言都有eod命名空间
  for (const locale of LOCALES) {
    if (!localeObjs[locale].eod) {
      localeObjs[locale].eod = {};
    }
  }
  
  // 找出最完整的EOD键集合（以中文为准）
  const zhEodKeys = Object.keys(localeObjs['zh-CN'].eod);
  
  // 为其他语言补充缺失的键
  for (const locale of ['en-US', 'th-TH']) {
    const currentKeys = Object.keys(localeObjs[locale].eod);
    const missingKeys = zhEodKeys.filter(key => !currentKeys.includes(key));
    
    if (missingKeys.length > 0) {
      console.log(`  为${locale}补充${missingKeys.length}个EOD键`);
      
      // 从中文复制缺失的键（作为占位符）
      for (const key of missingKeys) {
        if (localeObjs['zh-CN'].eod[key]) {
          localeObjs[locale].eod[key] = `[${locale}] ${localeObjs['zh-CN'].eod[key]}`;
        }
      }
    }
  }
  
  // 保存修复后的文件
  for (const locale of LOCALES) {
    saveLocaleObj(locale, localeObjs[locale]);
  }
}

function main() {
  try {
    console.log('🚀 开始修复i18n问题...\n');
    
    // 1. 修复缺失的命名空间
    fixMissingNamespaces();
    
    // 2. 修复step键结构
    fixStepKeys();
    
    // 3. 分析EOD差异
    analyzeEodDifferences();
    
    // 4. 修复EOD键数量差异
    fixEodKeys();
    
    console.log('\n✅ 修复完成！');
    console.log('\n下一步:');
    console.log('1. 重新运行模块分离脚本: node scripts/i18n_split_modules.js');
    console.log('2. 检查分离结果');
    console.log('3. 手动完善缺失的翻译内容');
    
  } catch (error) {
    console.error('❌ 修复失败:', error.message);
  }
}

if (require.main === module) {
  main();
}

module.exports = { 
  fixMissingNamespaces, 
  fixStepKeys, 
  analyzeEodDifferences, 
  fixEodKeys 
}; 