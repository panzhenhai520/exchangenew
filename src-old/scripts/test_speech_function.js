// 测试语音功能脚本
console.log('🔊 开始测试语音功能...');

// 1. 检查浏览器是否支持语音合成
function testSpeechSynthesisSupport() {
  console.log('🔊 1. 检查语音合成支持...');
  
  if ('speechSynthesis' in window) {
    console.log('✅ 浏览器支持语音合成 API');
    
    const speechSynthesis = window.speechSynthesis;
    console.log('🔊 语音合成对象:', speechSynthesis);
    
    // 检查关键方法
    if (typeof speechSynthesis.speak === 'function') {
      console.log('✅ speak 方法可用');
    } else {
      console.error('❌ speak 方法不可用');
    }
    
    if (typeof speechSynthesis.cancel === 'function') {
      console.log('✅ cancel 方法可用');
    } else {
      console.error('❌ cancel 方法不可用');
    }
    
    if (typeof speechSynthesis.getVoices === 'function') {
      console.log('✅ getVoices 方法可用');
    } else {
      console.error('❌ getVoices 方法不可用');
    }
    
    return true;
  } else {
    console.error('❌ 浏览器不支持语音合成 API');
    return false;
  }
}

// 2. 检查可用的语音
function testAvailableVoices() {
  console.log('🔊 2. 检查可用语音...');
  
  const speechSynthesis = window.speechSynthesis;
  const voices = speechSynthesis.getVoices();
  
  console.log('🔊 可用语音数量:', voices.length);
  
  if (voices.length === 0) {
    console.warn('⚠️ 没有找到可用的语音，可能需要等待语音加载');
    
    // 尝试等待语音加载
    return new Promise((resolve) => {
      speechSynthesis.onvoiceschanged = () => {
        const loadedVoices = speechSynthesis.getVoices();
        console.log('🔊 语音加载完成，可用语音数量:', loadedVoices.length);
        
        // 显示支持的语音语言
        const supportedLanguages = [...new Set(loadedVoices.map(voice => voice.lang.split('-')[0]))];
        console.log('🔊 支持的语音语言:', supportedLanguages);
        
        // 显示中文语音
        const chineseVoices = loadedVoices.filter(voice => voice.lang.startsWith('zh'));
        console.log('🔊 中文语音:', chineseVoices.map(v => ({ name: v.name, lang: v.lang })));
        
        // 显示英文语音
        const englishVoices = loadedVoices.filter(voice => voice.lang.startsWith('en'));
        console.log('🔊 英文语音:', englishVoices.map(v => ({ name: v.name, lang: v.lang })));
        
        resolve(loadedVoices);
      };
      
      // 触发语音加载
      speechSynthesis.getVoices();
    });
  } else {
    // 显示支持的语音语言
    const supportedLanguages = [...new Set(voices.map(voice => voice.lang.split('-')[0]))];
    console.log('🔊 支持的语音语言:', supportedLanguages);
    
    // 显示中文语音
    const chineseVoices = voices.filter(voice => voice.lang.startsWith('zh'));
    console.log('🔊 中文语音:', chineseVoices.map(v => ({ name: v.name, lang: v.lang })));
    
    // 显示英文语音
    const englishVoices = voices.filter(voice => voice.lang.startsWith('en'));
    console.log('🔊 英文语音:', englishVoices.map(v => ({ name: v.name, lang: v.lang })));
    
    return Promise.resolve(voices);
  }
}

// 3. 测试语音播报
function testSpeechUtterance(text = '测试语音播报功能') {
  console.log('🔊 3. 测试语音播报...');
  
  try {
    const speechSynthesis = window.speechSynthesis;
    
    // 取消当前播放
    speechSynthesis.cancel();
    
    // 创建语音对象
    const utterance = new SpeechSynthesisUtterance();
    
    // 设置语音参数
    utterance.text = text;
    utterance.lang = 'zh-CN';
    utterance.rate = 0.8;
    utterance.pitch = 1;
    
    console.log('🔊 语音设置:', {
      text: utterance.text,
      lang: utterance.lang,
      rate: utterance.rate,
      pitch: utterance.pitch
    });
    
    // 添加事件监听
    utterance.onstart = () => {
      console.log('✅ 语音播报开始');
    };
    
    utterance.onend = () => {
      console.log('✅ 语音播报结束');
    };
    
    utterance.onerror = (event) => {
      console.error('❌ 语音播报错误:', event.error);
      console.error('🔊 错误详情:', {
        error: event.error,
        message: event.message,
        elapsedTime: event.elapsedTime,
        charIndex: event.charIndex,
        name: event.name
      });
    };
    
    utterance.onpause = () => {
      console.log('🔊 语音播报暂停');
    };
    
    utterance.onresume = () => {
      console.log('🔊 语音播报恢复');
    };
    
    // 执行语音播报
    speechSynthesis.speak(utterance);
    
    console.log('✅ 语音播报已启动');
    
  } catch (error) {
    console.error('❌ 语音播报测试失败:', error);
    console.error('🔊 错误堆栈:', error.stack);
  }
}

// 4. 测试不同语言的语音播报
function testMultiLanguageSpeech() {
  console.log('🔊 4. 测试多语言语音播报...');
  
  const testCases = [
    { text: '测试中文语音播报', lang: 'zh-CN', rate: 0.8 },
    { text: 'Test English Speech', lang: 'en-US', rate: 0.9 },
    { text: 'ทดสอบการพูดภาษาไทย', lang: 'th-TH', rate: 0.7 }
  ];
  
  testCases.forEach((testCase, index) => {
    setTimeout(() => {
      console.log(`🔊 测试 ${testCase.lang} 语音...`);
      
      try {
        const speechSynthesis = window.speechSynthesis;
        speechSynthesis.cancel();
        
        const utterance = new SpeechSynthesisUtterance();
        utterance.text = testCase.text;
        utterance.lang = testCase.lang;
        utterance.rate = testCase.rate;
        utterance.pitch = 1;
        
        utterance.onstart = () => {
          console.log(`✅ ${testCase.lang} 语音播报开始`);
        };
        
        utterance.onend = () => {
          console.log(`✅ ${testCase.lang} 语音播报结束`);
        };
        
        utterance.onerror = (event) => {
          console.error(`❌ ${testCase.lang} 语音播报错误:`, event.error);
        };
        
        speechSynthesis.speak(utterance);
        
      } catch (error) {
        console.error(`❌ ${testCase.lang} 语音播报测试失败:`, error);
      }
    }, index * 3000); // 每个测试间隔3秒
  });
}

// 5. 检查语音状态
function checkSpeechStatus() {
  console.log('🔊 5. 检查语音状态...');
  
  const speechSynthesis = window.speechSynthesis;
  
  console.log('🔊 语音合成状态:', {
    speaking: speechSynthesis.speaking,
    pending: speechSynthesis.pending,
    paused: speechSynthesis.paused
  });
  
  // 检查是否有正在播放的语音
  if (speechSynthesis.speaking) {
    console.log('🔊 当前有语音正在播放');
  } else {
    console.log('🔊 当前没有语音播放');
  }
  
  // 检查是否有待播放的语音
  if (speechSynthesis.pending) {
    console.log('🔊 当前有待播放的语音');
  } else {
    console.log('🔊 当前没有待播放的语音');
  }
}

// 主测试函数
async function runSpeechTests() {
  console.log('🔊 ===== 语音功能测试开始 =====');
  
  // 1. 检查语音合成支持
  const isSupported = testSpeechSynthesisSupport();
  if (!isSupported) {
    console.error('❌ 语音合成不支持，测试终止');
    return;
  }
  
  // 2. 检查可用语音
  await testAvailableVoices();
  
  // 3. 检查语音状态
  checkSpeechStatus();
  
  // 4. 测试基本语音播报
  testSpeechUtterance('语音功能测试，如果您听到这句话，说明语音播报功能正常');
  
  // 5. 等待一段时间后测试多语言
  setTimeout(() => {
    testMultiLanguageSpeech();
  }, 2000);
  
  console.log('🔊 ===== 语音功能测试完成 =====');
}

// 运行测试
runSpeechTests(); 