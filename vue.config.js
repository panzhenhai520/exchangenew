const path = require('path')

module.exports = {
  publicPath: '/', // 修改：使用绝对路径，确保从根目录加载资源
  outputDir: path.resolve(__dirname, 'src/static/dist_frontend'), // ✅ 添加：设置输出目录
  assetsDir: '', // 可选：资源统一输出到 outputDir 下
  productionSourceMap: false,
  configureWebpack: {
    performance: {
      hints: false
    },
    plugins: [
      new (require('webpack')).DefinePlugin({
        __VUE_PROD_HYDRATION_MISMATCH_DETAILS__: 'false'
      })
    ]
  },
  devServer: {
    host: '0.0.0.0',  // 允许外部访问
    port: 8080,
    allowedHosts: 'all',  // 允许所有主机访问
    // 强制显示网络地址的配置
    onListening: function(devServer) {
      if (!devServer) {
        throw new Error('webpack-dev-server is not defined');
      }
      const port = devServer.server.address().port;
      console.log(`\n  App running at:`);
      console.log(`  - Local:   http://localhost:${port}/`);
      console.log(`  - Network: http://192.168.13.56:${port}/`);
    },
    historyApiFallback: {
      // 配置SPA路由fallback，解决刷新页面404问题
      index: '/index.html',
      rewrites: [
        // API请求不进行fallback
        { from: /^\/api\/.*$/, to: function(context) {
          return context.parsedUrl.pathname;
        }},
        // 静态资源不进行fallback
        { from: /\.(js|css|png|jpg|jpeg|gif|svg|ico|woff|woff2|ttf|eot|pdf)$/, to: function(context) {
          return context.parsedUrl.pathname;
        }},
        // 静态文件路径不进行fallback
        { from: /^\/static\/.*$/, to: function(context) {
          return context.parsedUrl.pathname;
        }},
        // help文件路径不进行fallback
        { from: /^\/help\/.*$/, to: function(context) {
          return context.parsedUrl.pathname;
        }},
        // 所有system路由都重定向到index.html
        { from: /^\/system\/.*$/, to: '/index.html' },
        // 其他前端路由
        { from: /^\/(dashboard|exchange|rates|balances|transactions|profile|login).*$/, to: '/index.html' }
      ],
      // 只对已知的前端路由进行fallback
      verbose: false,
      // 禁用自动重定向
      disableDotRule: true
    },
    proxy: {
      '/api': {
        target: process.env.VUE_APP_API_BASE_URL || (process.env.NODE_ENV === 'development' ? 'http://192.168.13.56:5001' : 'http://192.168.13.56:5001'),
        changeOrigin: true,
        logLevel: 'warn',
        secure: false,
        timeout: 60000,
        onError: function(err, req, res) {
          console.error('代理错误:', err.message);
          console.log('代理目标:', process.env.VUE_APP_API_BASE_URL || (process.env.NODE_ENV === 'development' ? 'http://192.168.13.56:5001' : 'http://192.168.13.56:5001'));
          // 返回JSON格式的错误响应而不是HTML
          res.writeHead(502, {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
          });
          res.end(JSON.stringify({
            success: false,
            message: '服务器连接失败，请检查后端服务是否正常运行',
            error: 'PROXY_ERROR',
            target: process.env.VUE_APP_API_BASE_URL || (process.env.NODE_ENV === 'development' ? 'http://192.168.13.56:5001' : 'http://192.168.13.56:5001')
          }));
        },
        onProxyReq: function(proxyReq, req, res) {
          // 设置请求超时
          proxyReq.setTimeout(30000, function() {
            proxyReq.abort();
          });
        }
      },
      '/static': {
        target: process.env.VUE_APP_API_BASE_URL || (process.env.NODE_ENV === 'development' ? 'http://192.168.13.56:5001' : 'http://192.168.13.56:5001'),
        changeOrigin: true,
        logLevel: 'warn',
        secure: false,
        timeout: 60000,
        onError: function(err, req, res) {
          console.error('静态资源代理错误:', err.message);
          res.writeHead(404, {
            'Content-Type': 'text/plain'
          });
          res.end('Static resource not found');
        }
      },
      '/flags': {
        target: process.env.VUE_APP_API_BASE_URL || (process.env.NODE_ENV === 'development' ? 'http://192.168.13.56:5001' : 'http://192.168.13.56:5001'),
        changeOrigin: true,
        logLevel: 'warn',
        secure: false,
        timeout: 60000,
        onError: function(err, req, res) {
          console.error('图标文件代理错误:', err.message);
          res.writeHead(404, {
            'Content-Type': 'text/plain'
          });
          res.end('Flag file not found');
        }
      },
      '/help': {
        target: process.env.VUE_APP_API_BASE_URL || (process.env.NODE_ENV === 'development' ? 'http://192.168.13.56:5001' : 'http://192.168.13.56:5001'),
        changeOrigin: true,
        logLevel: 'warn',
        secure: false,
        timeout: 60000,
        onError: function(err, req, res) {
          console.error('帮助文件代理错误:', err.message);
          res.writeHead(404, {
            'Content-Type': 'text/plain'
          });
          res.end('Help file not found');
        }
      }
    }
  }
}
