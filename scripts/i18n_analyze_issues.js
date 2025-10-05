#!/usr/bin/env node

/**
 * ExchangeOK i18n 问题分析和修复脚本
 * 分析缺失的翻译键和结构问题
 */

const fs = require('fs');
const path = require('path');

const I18N_DIR = path.join(__dirname, '../src/i18n');
const LOCALES = ['zh-CN', 'en-US', 'th-TH'];
const MODULES_DIR = path.join(I18N_DIR, 'modules');

function loadLocaleObj(locale) {
  const file = path.join(I18N_DIR, 'locales', `${locale}.js`);
  if (!fs.existsSync(file)) throw new Error(`缺失翻译文件: ${file}`);
  let content = fs.readFileSync(file, 'utf8');
  content = content.replace(/^\s*export\s+default\s+/, '').replace(/;\s*$/, '');
  // eslint-disable-next-line no-eval
  return eval('(' + content + ')');
}

function analyzeIssues() {
  console.log('🔍 分析翻译文件问题...\n');
  
  const localeObjs = {};
  for (const locale of LOCALES) {
    localeObjs[locale] = loadLocaleObj(locale);
  }
  
  // 1. 检查缺失的命名空间
  console.log('1. 缺失的命名空间分析:');
  const allNamespaces = new Set();
  for (const locale of LOCALES) {
    Object.keys(localeObjs[locale]).forEach(ns => allNamespaces.add(ns));
  }
  
  const missingNamespaces = {};
  for (const locale of LOCALES) {
    missingNamespaces[locale] = [];
    for (const ns of allNamespaces) {
      if (!localeObjs[locale][ns]) {
        missingNamespaces[locale].push(ns);
      }
    }
  }
  
  for (const locale of LOCALES) {
    if (missingNamespaces[locale].length > 0) {
      console.log(`   ${locale}: 缺失 ${missingNamespaces[locale].join(', ')}`);
    }
  }
  
  // 2. 检查未分离的顶级键
  console.log('\n2. 未分离的顶级键分析:');
  for (const locale of LOCALES) {
    const topLevelKeys = Object.keys(localeObjs[locale]);
    const unseparated = topLevelKeys.filter(k => 
      !['login', 'dashboard', 'exchange', 'auth', 'system', 'logs', 'balance_adjust',
        'reports', 'rates', 'transaction', 'customer', 'branch', 'common', 'menu',
        'user_menu', 'footer', 'defaults', 'calculation', 'balance', 'transactions',
        'printSettings', 'logManagement', 'currencyManagement', 'eod', 'local_stock_query'].includes(k)
    );
    if (unseparated.length > 0) {
      console.log(`   ${locale}: ${unseparated.join(', ')}`);
    }
  }
  
  // 3. 检查EOD模块的键数量差异
  console.log('\n3. EOD模块键数量分析:');
  for (const locale of LOCALES) {
    const eodKeys = localeObjs[locale].eod ? Object.keys(localeObjs[locale].eod) : [];
    console.log(`   ${locale}: ${eodKeys.length} keys`);
  }
  
  // 4. 检查step6, step7, step8结构
  console.log('\n4. Step6-8结构分析:');
  for (const locale of LOCALES) {
    const hasStep6 = localeObjs[locale].step6 ? '✓' : '✗';
    const hasStep7 = localeObjs[locale].step7 ? '✓' : '✗';
    const hasStep8 = localeObjs[locale].step8 ? '✓' : '✗';
    console.log(`   ${locale}: step6${hasStep6} step7${hasStep7} step8${hasStep8}`);
  }
  
  return { localeObjs, missingNamespaces };
}

function generateFixPlan() {
  console.log('\n📋 修复方案:');
  console.log('\n方案1: 补充缺失的命名空间');
  console.log('  - 为th-TH补充auth和system命名空间');
  console.log('  - 从zh-CN或en-US复制基础结构');
  
  console.log('\n方案2: 修复EOD模块键数量差异');
  console.log('  - 分析th-TH中缺失的EOD键');
  console.log('  - 从其他语言补充缺失的翻译');
  
  console.log('\n方案3: 处理未分离的顶级键');
  console.log('  - 将step6, step7, step8移动到eod命名空间下');
  console.log('  - 更新模块分离脚本');
  
  console.log('\n方案4: 验证和测试');
  console.log('  - 重新运行模块分离');
  console.log('  - 验证所有语言的键数量一致');
}

if (require.main === module) {
  try {
    const { localeObjs, missingNamespaces } = analyzeIssues();
    generateFixPlan();
    
    // 保存分析结果
    const report = {
      timestamp: new Date().toISOString(),
      missingNamespaces,
      recommendations: [
        '为th-TH补充auth和system命名空间',
        '修复EOD模块的键数量差异',
        '将step6-8移动到eod命名空间下',
        '重新运行模块分离脚本'
      ]
    };
    
    fs.writeFileSync(
      path.join(I18N_DIR, 'analysis_report.json'), 
      JSON.stringify(report, null, 2), 
      'utf8'
    );
    
    console.log('\n✅ 分析完成，详情见 analysis_report.json');
  } catch (error) {
    console.error('❌ 分析失败:', error.message);
  }
}

module.exports = { analyzeIssues, generateFixPlan }; 