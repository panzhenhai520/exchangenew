const fs = require('fs');
const path = require('path');

// 前端翻译文件路径
const frontendLocalesDir = path.join(__dirname, '../i18n/locales');

// 后端翻译文件输出路径
const backendLocalesDir = path.join(__dirname, '../locales');

// 支持的语言
const languages = ['zh-CN', 'en-US', 'th-TH'];

// 确保输出目录存在
if (!fs.existsSync(backendLocalesDir)) {
    fs.mkdirSync(backendLocalesDir, { recursive: true });
}

// 转换函数
function convertFile(lang) {
    const inputFile = path.join(frontendLocalesDir, `${lang}.js`);
    const outputFile = path.join(backendLocalesDir, `${lang}.json`);
    
    try {
        // 读取前端翻译文件
        const content = fs.readFileSync(inputFile, 'utf8');
        
        // 移除 'export default' 并添加 'module.exports ='
        const processedContent = content.replace('export default', 'module.exports =');
        
        // 写入临时文件
        const tempFile = path.join(backendLocalesDir, `temp_${lang}.js`);
        fs.writeFileSync(tempFile, processedContent);
        
        // 加载并转换为 JSON
        delete require.cache[require.resolve(tempFile)];
        const translations = require(tempFile);
        
        // 写入 JSON 文件
        fs.writeFileSync(outputFile, JSON.stringify(translations, null, 2));
        
        // 删除临时文件
        fs.unlinkSync(tempFile);
        
        console.log(`✓ 转换成功: ${lang}.js -> ${lang}.json`);
        
    } catch (error) {
        console.error(`✗ 转换失败 ${lang}:`, error.message);
    }
}

// 转换所有语言文件
console.log('开始转换翻译文件...');
languages.forEach(convertFile);
console.log('转换完成！'); 