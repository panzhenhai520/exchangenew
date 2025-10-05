/**
 * ExchangeOK 模块化翻译文件转换工具
 * 将前端的.js翻译文件转换为后端的.json文件
 * 支持模块化的翻译文件结构
 */

const fs = require('fs');
const path = require('path');

// 配置
const config = {
  // 前端翻译文件目录
  frontendLocalesDir: path.join(__dirname, '../src/i18n/locales'),
  frontendModulesDir: path.join(__dirname, '../src/i18n/modules'),
  
  // 后端翻译文件目录
  backendLocalesDir: path.join(__dirname, '../src/locales'),
  
  // 支持的语言
  supportedLocales: ['zh-CN', 'en-US', 'th-TH'],
  
  // 需要转换给后端的模块（可配置）
  backendModules: ['eod', 'exchange'] // reports模块可能不需要传给后端
};

class ModularI18nConverter {
  constructor() {
    this.ensureDirectories();
  }

  /**
   * 确保目录存在
   */
  ensureDirectories() {
    if (!fs.existsSync(config.backendLocalesDir)) {
      fs.mkdirSync(config.backendLocalesDir, { recursive: true });
    }
  }

  /**
   * 深度合并对象
   */
  deepMerge(target, source) {
    const result = { ...target };
    for (const key in source) {
      if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
        result[key] = this.deepMerge(result[key] || {}, source[key]);
      } else {
        result[key] = source[key];
      }
    }
    return result;
  }

  /**
   * 动态导入ES模块文件
   */
  async importESModule(filePath) {
    try {
      // 将路径转换为file:// URL
      const fileUrl = `file://${path.resolve(filePath)}`;
      const module = await import(fileUrl + `?t=${Date.now()}`); // 添加时间戳避免缓存
      return module.default;
    } catch (error) {
      console.error(`导入文件失败 ${filePath}:`, error.message);
      return null;
    }
  }

  /**
   * 读取并合并指定语言的所有翻译文件
   */
  async mergeTranslationFiles(locale) {
    let mergedTranslations = {};

    // 1. 读取核心翻译文件
    const coreFile = path.join(config.frontendLocalesDir, `${locale}.js`);
    if (fs.existsSync(coreFile)) {
      const coreTranslations = await this.importESModule(coreFile);
      if (coreTranslations) {
        mergedTranslations = this.deepMerge(mergedTranslations, coreTranslations);
        console.log(`✓ 已加载核心文件: ${locale}.js`);
      }
    }

    // 2. 读取模块翻译文件
    for (const moduleName of config.backendModules) {
      const moduleFile = path.join(config.frontendModulesDir, moduleName, `${locale}.js`);
      if (fs.existsSync(moduleFile)) {
        const moduleTranslations = await this.importESModule(moduleFile);
        if (moduleTranslations) {
          mergedTranslations = this.deepMerge(mergedTranslations, moduleTranslations);
          console.log(`✓ 已加载模块文件: ${moduleName}/${locale}.js`);
        }
      } else {
        console.warn(`⚠ 模块文件不存在: ${moduleName}/${locale}.js`);
      }
    }

    return mergedTranslations;
  }

  /**
   * 过滤出后端需要的翻译内容
   */
  filterBackendTranslations(translations) {
    // 定义后端需要的翻译键
    const backendKeys = [
      'auth',        // 认证相关
      'system',      // 系统消息
      'errors',      // 错误信息
      'eod',         // 日结流程
      'exchange',    // 兑换业务
      'validation',  // 验证消息
      'status',      // 状态信息
      'common'       // 通用消息
    ];

    const filteredTranslations = {};
    
    backendKeys.forEach(key => {
      if (translations[key]) {
        filteredTranslations[key] = translations[key];
      }
    });

    // 如果某些嵌套结构中包含后端需要的内容，也要提取
    Object.keys(translations).forEach(key => {
      if (typeof translations[key] === 'object') {
        const nestedFiltered = {};
        let hasBackendContent = false;

        Object.keys(translations[key]).forEach(nestedKey => {
          // 检查是否包含错误信息、状态信息等后端关心的内容
          if (nestedKey.includes('error') || 
              nestedKey.includes('status') || 
              nestedKey.includes('message') ||
              nestedKey.includes('validation')) {
            nestedFiltered[nestedKey] = translations[key][nestedKey];
            hasBackendContent = true;
          }
        });

        if (hasBackendContent && !filteredTranslations[key]) {
          filteredTranslations[key] = nestedFiltered;
        }
      }
    });

    return filteredTranslations;
  }

  /**
   * 转换单个语言的翻译文件
   */
  async convertLanguage(locale) {
    console.log(`\n开始转换语言: ${locale}`);

    try {
      // 1. 合并所有翻译文件
      const mergedTranslations = await this.mergeTranslationFiles(locale);
      
      if (Object.keys(mergedTranslations).length === 0) {
        console.warn(`⚠ ${locale} 没有找到任何翻译内容`);
        return false;
      }

      // 2. 过滤出后端需要的翻译
      const backendTranslations = this.filterBackendTranslations(mergedTranslations);

      // 3. 生成后端JSON文件
      const outputPath = path.join(config.backendLocalesDir, `${locale}.json`);
      const jsonContent = JSON.stringify(backendTranslations, null, 2);
      
      fs.writeFileSync(outputPath, jsonContent, 'utf8');
      
      // 4. 统计信息
      const totalKeys = this.countKeys(mergedTranslations);
      const backendKeys = this.countKeys(backendTranslations);
      
      console.log(`✓ ${locale} 转换完成:`);
      console.log(`  - 总翻译键数: ${totalKeys}`);
      console.log(`  - 后端翻译键数: ${backendKeys}`);
      console.log(`  - 输出文件: ${outputPath}`);
      
      return true;
    } catch (error) {
      console.error(`✗ ${locale} 转换失败:`, error.message);
      return false;
    }
  }

  /**
   * 递归计算翻译键的数量
   */
  countKeys(obj, count = 0) {
    for (const key in obj) {
      if (typeof obj[key] === 'object' && obj[key] !== null) {
        count = this.countKeys(obj[key], count);
      } else {
        count++;
      }
    }
    return count;
  }

  /**
   * 转换所有语言
   */
  async convertAll() {
    console.log('='.repeat(60));
    console.log('ExchangeOK 模块化翻译文件转换工具');
    console.log('='.repeat(60));
    
    const results = {};
    
    for (const locale of config.supportedLocales) {
      const success = await this.convertLanguage(locale);
      results[locale] = success;
    }

    // 输出汇总信息
    console.log('\n' + '='.repeat(60));
    console.log('转换结果汇总:');
    console.log('='.repeat(60));
    
    let successCount = 0;
    Object.entries(results).forEach(([locale, success]) => {
      const status = success ? '✓ 成功' : '✗ 失败';
      console.log(`${locale}: ${status}`);
      if (success) successCount++;
    });
    
    console.log(`\n总计: ${successCount}/${config.supportedLocales.length} 个语言转换成功`);
    
    if (successCount === config.supportedLocales.length) {
      console.log('\n🎉 所有翻译文件转换完成！');
    } else {
      console.log('\n⚠ 部分翻译文件转换失败，请检查错误信息');
    }
  }

  /**
   * 验证转换结果
   */
  async validateConversion() {
    console.log('\n验证转换结果...');
    
    for (const locale of config.supportedLocales) {
      const outputPath = path.join(config.backendLocalesDir, `${locale}.json`);
      
      if (!fs.existsSync(outputPath)) {
        console.error(`✗ 缺少输出文件: ${outputPath}`);
        continue;
      }

      try {
        const content = fs.readFileSync(outputPath, 'utf8');
        const parsed = JSON.parse(content);
        const keyCount = this.countKeys(parsed);
        console.log(`✓ ${locale}.json 验证通过 (${keyCount} 个翻译键)`);
      } catch (error) {
        console.error(`✗ ${locale}.json 验证失败:`, error.message);
      }
    }
  }

  /**
   * 显示配置信息
   */
  showConfig() {
    console.log('\n当前配置:');
    console.log(`  前端核心文件目录: ${config.frontendLocalesDir}`);
    console.log(`  前端模块文件目录: ${config.frontendModulesDir}`);
    console.log(`  后端输出目录: ${config.backendLocalesDir}`);
    console.log(`  支持的语言: ${config.supportedLocales.join(', ')}`);
    console.log(`  后端模块: ${config.backendModules.join(', ')}`);
  }
}

// 命令行接口
async function main() {
  const converter = new ModularI18nConverter();
  const command = process.argv[2];

  switch (command) {
    case 'convert':
      const locale = process.argv[3];
      if (locale) {
        await converter.convertLanguage(locale);
      } else {
        await converter.convertAll();
      }
      break;

    case 'validate':
      await converter.validateConversion();
      break;

    case 'config':
      converter.showConfig();
      break;

    default:
      console.log(`
ExchangeOK 模块化翻译文件转换工具

用法:
  node utils/convert_i18n_modular.js <命令> [参数]

命令:
  convert [语言]    转换翻译文件 (不指定语言则转换所有)
  validate         验证转换结果
  config           显示当前配置

示例:
  node utils/convert_i18n_modular.js convert
  node utils/convert_i18n_modular.js convert zh-CN
  node utils/convert_i18n_modular.js validate
      `);
  }
}

// 如果直接运行此脚本
if (require.main === module) {
  main().catch(console.error);
}

module.exports = { ModularI18nConverter, config }; 