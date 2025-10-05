#!/usr/bin/env node

/**
 * ExchangeOK i18n 回退脚本
 * 用于在模块化翻译分离失败时快速回退到基础翻译文件
 */

const fs = require('fs');
const path = require('path');

const I18N_DIR = path.join(__dirname, '../src/i18n');

function backupCurrentConfig() {
  const currentIndex = path.join(I18N_DIR, 'index.js');
  const backupPath = path.join(I18N_DIR, `index.backup.${Date.now()}.js`);
  
  if (fs.existsSync(currentIndex)) {
    fs.copyFileSync(currentIndex, backupPath);
    console.log(`✅ 已备份当前配置到: ${backupPath}`);
    return backupPath;
  } else {
    console.log('⚠️  当前没有 index.js 文件');
    return null;
  }
}

function rollbackToBackup() {
  const backupIndex = path.join(I18N_DIR, 'index.backup.js');
  const currentIndex = path.join(I18N_DIR, 'index.js');
  
  if (fs.existsSync(backupIndex)) {
    fs.copyFileSync(backupIndex, currentIndex);
    console.log('✅ 已回退到基础翻译配置');
    return true;
  } else {
    console.log('❌ 未找到备份配置文件 index.backup.js');
    return false;
  }
}

function switchToModular() {
  const modularIndex = path.join(I18N_DIR, 'index.modular.js');
  const currentIndex = path.join(I18N_DIR, 'index.js');
  
  if (fs.existsSync(modularIndex)) {
    fs.copyFileSync(modularIndex, currentIndex);
    console.log('✅ 已切换到模块化翻译配置');
    return true;
  } else {
    console.log('❌ 未找到模块化配置文件 index.modular.js');
    return false;
  }
}

function checkTranslationFiles() {
  const requiredFiles = [
    'locales/zh-CN.js',
    'locales/en-US.js', 
    'locales/th-TH.js',
    'modules/eod/zh-CN.js',
    'modules/eod/en-US.js',
    'modules/eod/th-TH.js',
    'modules/exchange/zh-CN.js',
    'modules/exchange/en-US.js',
    'modules/exchange/th-TH.js',
    'modules/reports/zh-CN.js',
    'modules/reports/en-US.js',
    'modules/reports/th-TH.js'
  ];
  
  console.log('🔍 检查翻译文件完整性...');
  const missingFiles = [];
  
  requiredFiles.forEach(file => {
    const filePath = path.join(I18N_DIR, file);
    if (!fs.existsSync(filePath)) {
      missingFiles.push(file);
      console.log(`❌ 缺失: ${file}`);
    } else {
      console.log(`✅ 存在: ${file}`);
    }
  });
  
  if (missingFiles.length > 0) {
    console.log(`\n⚠️  发现 ${missingFiles.length} 个缺失的翻译文件`);
    return false;
  } else {
    console.log('\n✅ 所有翻译文件完整');
    return true;
  }
}

function main() {
  const command = process.argv[2];
  
  console.log('🔄 ExchangeOK i18n 配置管理工具\n');
  
  switch (command) {
    case 'backup':
      backupCurrentConfig();
      break;
      
    case 'rollback':
      rollbackToBackup();
      break;
      
    case 'modular':
      switchToModular();
      break;
      
    case 'check':
      checkTranslationFiles();
      break;
      
    case 'safe-modular':
      console.log('🛡️  安全切换到模块化配置...');
      backupCurrentConfig();
      if (checkTranslationFiles()) {
        switchToModular();
        console.log('✅ 安全切换到模块化配置完成');
      } else {
        console.log('❌ 翻译文件不完整，切换失败');
      }
      break;
      
    default:
      console.log('使用方法:');
      console.log('  node i18n_rollback.js backup     - 备份当前配置');
      console.log('  node i18n_rollback.js rollback   - 回退到基础配置');
      console.log('  node i18n_rollback.js modular    - 切换到模块化配置');
      console.log('  node i18n_rollback.js check      - 检查翻译文件完整性');
      console.log('  node i18n_rollback.js safe-modular - 安全切换到模块化配置');
      break;
  }
}

if (require.main === module) {
  main();
}

module.exports = {
  backupCurrentConfig,
  rollbackToBackup,
  switchToModular,
  checkTranslationFiles
}; 