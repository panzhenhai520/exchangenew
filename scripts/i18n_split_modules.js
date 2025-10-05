#!/usr/bin/env node

/**
 * ExchangeOK i18n 模块化分离脚本
 * 按一级命名空间自动分离为modules下的独立三语言文件
 */

const fs = require('fs');
const path = require('path');

const I18N_DIR = path.join(__dirname, '../src/i18n');
const LOCALES = ['zh-CN', 'en-US', 'th-TH'];
const MODULES_DIR = path.join(I18N_DIR, 'modules');

// 需要分离的一级命名空间
const NAMESPACES = [
  'login', 'dashboard', 'exchange', 'auth', 'system', 'logs', 'balance_adjust',
  'reports', 'rates', 'transaction', 'customer', 'branch', 'common', 'menu',
  'user_menu', 'footer', 'defaults', 'calculation', 'balance', 'transactions',
  'printSettings', 'logManagement', 'currencyManagement', 'eod', 'local_stock_query'
];

function loadLocaleObj(locale) {
  const file = path.join(I18N_DIR, 'locales', `${locale}.js`);
  if (!fs.existsSync(file)) throw new Error(`缺失翻译文件: ${file}`);
  let content = fs.readFileSync(file, 'utf8');
  // 兼容 export default {...} 或 export default {...};
  content = content.replace(/^\s*export\s+default\s+/, '').replace(/;\s*$/, '');
  // eslint-disable-next-line no-eval
  return eval('(' + content + ')');
}

function writeModuleFile(namespace, locale, obj) {
  const dir = path.join(MODULES_DIR, namespace);
  if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });
  const file = path.join(dir, `${locale}.js`);
  const code = `// ${namespace}模块 - ${locale}翻译\nexport default ${JSON.stringify({ [namespace]: obj }, null, 2)}`;
  fs.writeFileSync(file, code, 'utf8');
}

function splitModules() {
  const localeObjs = {};
  for (const locale of LOCALES) {
    localeObjs[locale] = loadLocaleObj(locale);
  }
  const report = [];
  for (const ns of NAMESPACES) {
    for (const locale of LOCALES) {
      const obj = localeObjs[locale][ns] || {};
      writeModuleFile(ns, locale, obj);
      report.push(`${ns} [${locale}]: ${Object.keys(obj).length} keys`);
    }
  }
  // 统计未分离的顶级key
  for (const locale of LOCALES) {
    const rest = Object.keys(localeObjs[locale]).filter(k => !NAMESPACES.includes(k));
    if (rest.length > 0) {
      report.push(`\n[${locale}] 未分离顶级key: ${rest.join(', ')}`);
    }
  }
  fs.writeFileSync(path.join(I18N_DIR, 'split_report.txt'), report.join('\n'), 'utf8');
  console.log('✅ 模块分离完成，详情见 split_report.txt');
}

if (require.main === module) {
  splitModules();
}

module.exports = { splitModules }; 