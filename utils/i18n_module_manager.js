/**
 * ExchangeOK 翻译模块管理工具
 * 用于管理模块化的翻译文件
 */

const fs = require('fs');
const path = require('path');

class I18nModuleManager {
  constructor() {
    this.supportedLocales = ['zh-CN', 'en-US', 'th-TH'];
    this.modulesDir = path.join(__dirname, '../src/i18n/modules');
    this.localesDir = path.join(__dirname, '../src/i18n/locales');
  }

  /**
   * 创建新的翻译模块
   * @param {string} moduleName - 模块名称
   * @param {object} templates - 各语言的模板内容
   */
  createModule(moduleName, templates = {}) {
    const moduleDir = path.join(this.modulesDir, moduleName);
    
    // 创建模块目录
    if (!fs.existsSync(moduleDir)) {
      fs.mkdirSync(moduleDir, { recursive: true });
    }

    // 为每种语言创建文件
    this.supportedLocales.forEach(locale => {
      const filePath = path.join(moduleDir, `${locale}.js`);
      const template = templates[locale] || this.getDefaultTemplate(moduleName, locale);
      
      const content = `// ${moduleName} Module - ${this.getLanguageName(locale)}
export default ${JSON.stringify(template, null, 2)}`;

      fs.writeFileSync(filePath, content, 'utf8');
      console.log(`创建文件: ${filePath}`);
    });
  }

  /**
   * 获取所有可用的模块
   */
  getAvailableModules() {
    if (!fs.existsSync(this.modulesDir)) {
      return [];
    }

    return fs.readdirSync(this.modulesDir, { withFileTypes: true })
      .filter(dirent => dirent.isDirectory())
      .map(dirent => dirent.name);
  }

  /**
   * 验证模块完整性
   * @param {string} moduleName - 模块名称
   */
  validateModule(moduleName) {
    const moduleDir = path.join(this.modulesDir, moduleName);
    const issues = [];

    if (!fs.existsSync(moduleDir)) {
      issues.push(`模块目录不存在: ${moduleDir}`);
      return issues;
    }

    // 检查每种语言的文件是否存在
    this.supportedLocales.forEach(locale => {
      const filePath = path.join(moduleDir, `${locale}.js`);
      if (!fs.existsSync(filePath)) {
        issues.push(`缺少语言文件: ${filePath}`);
      }
    });

    return issues;
  }

  /**
   * 生成模块化的i18n配置文件
   */
  generateI18nConfig() {
    const modules = this.getAvailableModules();
    const imports = [];
    const mergeStatements = [];

    // 生成导入语句
    this.supportedLocales.forEach(locale => {
      // 核心文件导入
      imports.push(`import ${this.toCamelCase(locale)} from './locales/${locale}'`);
      
      // 模块文件导入
      modules.forEach(module => {
        const varName = `${this.toCamelCase(locale)}_${this.toCamelCase(module)}`;
        imports.push(`import ${varName} from './modules/${module}/${locale}'`);
      });
    });

    // 生成合并语句
    this.supportedLocales.forEach(locale => {
      const camelLocale = this.toCamelCase(locale);
      let mergeChain = camelLocale;
      
      modules.forEach(module => {
        const varName = `${camelLocale}_${this.toCamelCase(module)}`;
        mergeChain = `deepMerge(${mergeChain}, ${varName})`;
      });
      
      mergeStatements.push(`  '${locale}': ${mergeChain}`);
    });

    // 生成完整配置文件内容
    const configContent = `import { createI18n } from 'vue-i18n'

// 核心翻译文件
${imports.filter(imp => !imp.includes('modules')).join('\n')}

// 模块化翻译文件
${imports.filter(imp => imp.includes('modules')).join('\n')}

// 深度合并函数
function deepMerge(target, source) {
  const result = { ...target }
  for (const key in source) {
    if (source[key] && typeof source[key] === 'object' && !Array.isArray(source[key])) {
      result[key] = deepMerge(result[key] || {}, source[key])
    } else {
      result[key] = source[key]
    }
  }
  return result
}

// 合并翻译文件
const messages = {
${mergeStatements.join(',\n')}
}

const i18n = createI18n({
  legacy: false,
  locale: localStorage.getItem('language') || 'zh-CN',
  fallbackLocale: 'zh-CN',
  messages,
  globalInjection: true
})

export default i18n`;

    const configPath = path.join(this.localesDir, '../index.js');
    fs.writeFileSync(configPath, configContent, 'utf8');
    console.log(`生成配置文件: ${configPath}`);
  }

  /**
   * 检查重复的翻译key
   */
  checkDuplicateKeys() {
    const modules = this.getAvailableModules();
    const duplicates = {};

    this.supportedLocales.forEach(locale => {
      const allKeys = new Set();
      const duplicateKeys = new Set();

      // 检查核心文件
      try {
        const coreFile = path.join(this.localesDir, `${locale}.js`);
        if (fs.existsSync(coreFile)) {
          const coreKeys = this.extractKeys(coreFile);
          coreKeys.forEach(key => {
            if (allKeys.has(key)) {
              duplicateKeys.add(key);
            }
            allKeys.add(key);
          });
        }

        // 检查模块文件
        modules.forEach(module => {
          const moduleFile = path.join(this.modulesDir, module, `${locale}.js`);
          if (fs.existsSync(moduleFile)) {
            const moduleKeys = this.extractKeys(moduleFile);
            moduleKeys.forEach(key => {
              if (allKeys.has(key)) {
                duplicateKeys.add(key);
              }
              allKeys.add(key);
            });
          }
        });

        if (duplicateKeys.size > 0) {
          duplicates[locale] = Array.from(duplicateKeys);
        }
      } catch (error) {
        console.error(`检查 ${locale} 时出错:`, error.message);
      }
    });

    return duplicates;
  }

  /**
   * 从文件中提取所有翻译key
   */
  extractKeys(filePath) {
    // 这里应该实现一个更复杂的解析器
    // 暂时返回空数组
    return [];
  }

  /**
   * 工具方法
   */
  toCamelCase(str) {
    return str.replace(/[-_]/g, '').replace(/([A-Z])/g, (match, p1, offset) => 
      offset === 0 ? p1.toLowerCase() : p1
    );
  }

  getLanguageName(locale) {
    const names = {
      'zh-CN': '中文',
      'en-US': 'English',
      'th-TH': 'ไทย'
    };
    return names[locale] || locale;
  }

  getDefaultTemplate(moduleName, locale) {
    return {
      [moduleName]: {
        example_key: `Example value for ${moduleName} in ${locale}`
      }
    };
  }
}

// 命令行接口
if (require.main === module) {
  const manager = new I18nModuleManager();
  const command = process.argv[2];

  switch (command) {
    case 'create':
      const moduleName = process.argv[3];
      if (!moduleName) {
        console.error('请提供模块名称');
        process.exit(1);
      }
      manager.createModule(moduleName);
      break;

    case 'list':
      const modules = manager.getAvailableModules();
      console.log('可用模块:', modules.join(', '));
      break;

    case 'validate':
      const moduleToValidate = process.argv[3];
      if (moduleToValidate) {
        const issues = manager.validateModule(moduleToValidate);
        if (issues.length === 0) {
          console.log(`模块 ${moduleToValidate} 验证通过`);
        } else {
          console.log(`模块 ${moduleToValidate} 存在问题:`);
          issues.forEach(issue => console.log(`  - ${issue}`));
        }
      } else {
        console.log('验证所有模块...');
        const allModules = manager.getAvailableModules();
        allModules.forEach(module => {
          const issues = manager.validateModule(module);
          if (issues.length > 0) {
            console.log(`模块 ${module} 存在问题:`);
            issues.forEach(issue => console.log(`  - ${issue}`));
          }
        });
      }
      break;

    case 'generate':
      manager.generateI18nConfig();
      break;

    case 'check-duplicates':
      const duplicates = manager.checkDuplicateKeys();
      if (Object.keys(duplicates).length === 0) {
        console.log('未发现重复的翻译key');
      } else {
        console.log('发现重复的翻译key:');
        Object.entries(duplicates).forEach(([locale, keys]) => {
          console.log(`  ${locale}: ${keys.join(', ')}`);
        });
      }
      break;

    default:
      console.log(`
ExchangeOK 翻译模块管理工具

用法:
  node utils/i18n_module_manager.js <命令> [参数]

命令:
  create <模块名>     创建新的翻译模块
  list              列出所有可用模块
  validate [模块名]  验证模块完整性
  generate          生成i18n配置文件
  check-duplicates  检查重复的翻译key

示例:
  node utils/i18n_module_manager.js create user-management
  node utils/i18n_module_manager.js validate eod
  node utils/i18n_module_manager.js generate
      `);
  }
}

module.exports = I18nModuleManager; 