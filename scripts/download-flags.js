const https = require('https');
const fs = require('fs');
const path = require('path');

const FLAGS_DIR = path.join(__dirname, '../public/flags');

// 确保目录存在
if (!fs.existsSync(FLAGS_DIR)) {
  fs.mkdirSync(FLAGS_DIR, { recursive: true });
}

// 创建默认的未知国旗图标
const unknownFlagSvg = `
<svg width="24" height="16" viewBox="0 0 24 16" fill="none" xmlns="http://www.w3.org/2000/svg">
  <rect width="24" height="16" fill="#E5E5E5"/>
  <text x="12" y="10" font-family="Arial" font-size="8" fill="#666666" text-anchor="middle">?</text>
</svg>
`;

fs.writeFileSync(path.join(FLAGS_DIR, 'unknown.svg'), unknownFlagSvg.trim());

// 要下载的国旗列表
const FLAGS = [
  'us', 'eu', 'gb', 'jp', 'cn', 'hk', 'tw', 'kr', 'sg', 'th',
  'id', 'my', 'ph', 'in', 'au', 'nz', 'ca', 'ch', 'se', 'dk',
  'no', 'ru', 'ae', 'sa', 'br', 'za', 'tr', 'mx', 'pl', 'vn'
];

// 从 country-flags-svg 项目下载国旗
const BASE_URL = 'https://raw.githubusercontent.com/lipis/flag-icons/master/flags/4x3';

function downloadFlag(countryCode) {
  const fileName = `${countryCode}.svg`;
  const filePath = path.join(FLAGS_DIR, fileName);
  const url = `${BASE_URL}/${countryCode}.svg`;

  https.get(url, (response) => {
    if (response.statusCode === 200) {
      const file = fs.createWriteStream(filePath);
      response.pipe(file);
      file.on('finish', () => {
        console.log(`Downloaded: ${fileName}`);
        file.close();
      });
    } else {
      console.error(`Failed to download ${fileName}: ${response.statusCode}`);
    }
  }).on('error', (err) => {
    console.error(`Error downloading ${fileName}:`, err.message);
  });
}

// 下载所有国旗
console.log('Starting flag downloads...');
FLAGS.forEach(downloadFlag);
console.log('Download tasks initiated. Please wait for completion...'); 