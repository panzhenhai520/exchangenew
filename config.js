// 机顶盒汇率展示配置文件
const CONFIG = {
    serverUrl: 'http://192.168.13.56:8080',  // 汇率系统地址
    branchCode: 'A005',                    // 网点代码
    theme: 'dark',                         // 主题 (light/dark)
    // 检查间隔（毫秒）- 每小时检查一次
    checkInterval: 60 * 60 * 1000,
    // 重试间隔（毫秒）- 失败后5分钟重试
    retryInterval: 5 * 60 * 1000
};

// 如果在浏览器环境中，将配置暴露到全局
if (typeof window !== 'undefined') {
    window.CONFIG = CONFIG;
}

// 如果在Node.js环境中，导出配置
if (typeof module !== 'undefined' && module.exports) {
    module.exports = CONFIG;
} 