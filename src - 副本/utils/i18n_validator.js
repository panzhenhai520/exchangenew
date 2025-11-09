/**
 * i18n翻译验证工具
 * 用于检查翻译缺失和key不匹配的问题
 */

import fs from 'fs'
import path from 'path'

// 支持的语言列表
const SUPPORTED_LOCALES = ['zh-CN', 'en-US', 'th-TH']

// 加载所有语言文件
function loadLocales() {
  const locales = {}
  SUPPORTED_LOCALES.forEach(locale => {
    const filePath = path.join(__dirname, `../locales/${locale}.json`)
    if (fs.existsSync(filePath)) {
      const content = fs.readFileSync(filePath, 'utf8')
      locales[locale] = JSON.parse(content)
    } else {
      console.warn(`语言文件不存在: ${filePath}`)
    }
  })
  return locales
}

// 递归获取所有翻译key
function getAllKeys(obj, prefix = '') {
  const keys = []
  for (const key in obj) {
    const fullKey = prefix ? `${prefix}.${key}` : key
    if (typeof obj[key] === 'object' && obj[key] !== null) {
      keys.push(...getAllKeys(obj[key], fullKey))
    } else {
      keys.push(fullKey)
    }
  }
  return keys
}

// 扫描Vue文件中使用的翻译key
function scanVueFiles(directory) {
  const usedKeys = new Set()
  const vueFiles = []
  
  function scanDirectory(dir) {
    const files = fs.readdirSync(dir)
    files.forEach(file => {
      const filePath = path.join(dir, file)
      const stat = fs.statSync(filePath)
      
      if (stat.isDirectory() && !file.startsWith('.') && file !== 'node_modules') {
        scanDirectory(filePath)
      } else if (file.endsWith('.vue')) {
        vueFiles.push(filePath)
      }
    })
  }
  
  scanDirectory(directory)
  
  // 扫描Vue文件中的翻译key
  vueFiles.forEach(filePath => {
    const content = fs.readFileSync(filePath, 'utf8')
    // 匹配 $t('xxx') 和 t('xxx') 模式
    const matches = content.match(/\$?t\(['"]([\w.]+)['"]\)/g)
    if (matches) {
      matches.forEach(match => {
        const key = match.match(/['"]([\w.]+)['"]/)[1]
        usedKeys.add(key)
      })
    }
  })
  
  return Array.from(usedKeys)
}

// 验证翻译完整性
function validateTranslations() {
  console.log('🔍 开始验证多语言翻译...')
  
  const locales = loadLocales()
  const usedKeys = scanVueFiles(path.join(__dirname, '../'))
  
  const results = {
    missingKeys: {},
    unusedKeys: {},
    inconsistentKeys: []
  }
  
  // 获取所有翻译key（以中文为基准）
  const baseLocale = 'zh-CN'
  const allKeysInBase = getAllKeys(locales[baseLocale])
  
  // 检查每种语言的翻译完整性
  SUPPORTED_LOCALES.forEach(locale => {
    if (!locales[locale]) return
    
    const keysInLocale = getAllKeys(locales[locale])
    const missingInLocale = allKeysInBase.filter(key => !keysInLocale.includes(key))
    const extraInLocale = keysInLocale.filter(key => !allKeysInBase.includes(key))
    
    if (missingInLocale.length > 0) {
      results.missingKeys[locale] = missingInLocale
    }
    
    if (extraInLocale.length > 0) {
      results.inconsistentKeys.push({
        locale,
        extraKeys: extraInLocale
      })
    }
  })
  
  // 检查未使用的翻译key
  const unusedKeys = allKeysInBase.filter(key => !usedKeys.includes(key))
  if (unusedKeys.length > 0) {
    results.unusedKeys = unusedKeys
  }
  
  // 检查代码中使用但翻译中缺失的key
  const missingInCode = usedKeys.filter(key => !allKeysInBase.includes(key))
  if (missingInCode.length > 0) {
    results.missingInCode = missingInCode
  }
  
  return results
}

// 生成验证报告
function generateReport() {
  const results = validateTranslations()
  let report = '📊 多语言翻译验证报告\n'
  report += '=' .repeat(50) + '\n\n'
  
  // 缺失的翻译
  if (Object.keys(results.missingKeys).length > 0) {
    report += '❌ 缺失的翻译:\n'
    Object.entries(results.missingKeys).forEach(([locale, keys]) => {
      report += `  ${locale}: ${keys.length} 个缺失\n`
      keys.slice(0, 5).forEach(key => report += `    - ${key}\n`)
      if (keys.length > 5) report += `    ... 还有 ${keys.length - 5} 个\n`
    })
    report += '\n'
  }
  
  // 代码中使用但翻译缺失的key
  if (results.missingInCode && results.missingInCode.length > 0) {
    report += '🚨 代码中使用但翻译文件中缺失的key:\n'
    results.missingInCode.forEach(key => report += `  - ${key}\n`)
    report += '\n'
  }
  
  // 不一致的翻译key
  if (results.inconsistentKeys.length > 0) {
    report += '⚠️  不一致的翻译key:\n'
    results.inconsistentKeys.forEach(item => {
      report += `  ${item.locale}: ${item.extraKeys.length} 个额外key\n`
    })
    report += '\n'
  }
  
  // 未使用的翻译
  if (results.unusedKeys && results.unusedKeys.length > 0) {
    report += `💡 未使用的翻译 (${results.unusedKeys.length} 个):\n`
    results.unusedKeys.slice(0, 10).forEach(key => report += `  - ${key}\n`)
    if (results.unusedKeys.length > 10) {
      report += `  ... 还有 ${results.unusedKeys.length - 10} 个\n`
    }
    report += '\n'
  }
  
  if (Object.keys(results.missingKeys).length === 0 && 
      (!results.missingInCode || results.missingInCode.length === 0)) {
    report += '✅ 所有翻译都是完整的！\n'
  }
  
  return report
}

// 自动修复翻译缺失
function autoFix() {
  console.log('🔧 自动修复翻译缺失...')
  
  const results = validateTranslations()
  const locales = loadLocales()
  
  // 为缺失的key添加占位符翻译
  Object.entries(results.missingKeys).forEach(([locale, missingKeys]) => {
    missingKeys.forEach(key => {
      const keyParts = key.split('.')
      let obj = locales[locale]
      
      // 创建嵌套对象路径
      for (let i = 0; i < keyParts.length - 1; i++) {
        if (!obj[keyParts[i]]) {
          obj[keyParts[i]] = {}
        }
        obj = obj[keyParts[i]]
      }
      
      // 添加占位符翻译
      const lastKey = keyParts[keyParts.length - 1]
      obj[lastKey] = `[${locale}] ${key}` // 占位符格式
    })
    
    // 保存修复后的文件
    const filePath = path.join(__dirname, `../locales/${locale}.json`)
    fs.writeFileSync(filePath, JSON.stringify(locales[locale], null, 2), 'utf8')
    console.log(`✅ 已修复 ${locale} 的 ${missingKeys.length} 个缺失翻译`)
  })
}

// 命令行接口
if (require.main === module) {
  const command = process.argv[2]
  
  switch (command) {
    case 'validate':
      console.log(generateReport())
      break
    case 'fix':
      autoFix()
      break
    default:
      console.log('使用方法:')
      console.log('  node i18n_validator.js validate  - 验证翻译完整性')
      console.log('  node i18n_validator.js fix       - 自动修复缺失的翻译')
  }
}

export { validateTranslations, generateReport, autoFix } 