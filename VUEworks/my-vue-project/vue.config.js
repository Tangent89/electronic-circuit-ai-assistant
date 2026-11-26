const { defineConfig } = require('@vue/cli-service')
module.exports = defineConfig({
  // 必须使用绝对根路径 '/'：前端是 history 模式路由，若用 './' 相对路径，
  // 在 /analog-circuit-experiments/1 这类子页面刷新时，资源会被解析成
  // /analog-circuit-experiments/js/app.js 而 404。配合 app.py 的 404 回落使用。
  publicPath: '/',
  devServer: {   //生产环境中，不会启用 devServer 相关的 proxy 设置
    compress: false, //禁止gzip压缩，否则流会被缓冲
    proxy: {
      '/chat': {
        target: 'http://localhost:5000',
        changeOrigin: true,
        ws: false,                    // 关闭 websocket
        onProxyReq (proxyReq /*, req, res*/) {
          // ① 去掉浏览器带来的 Accept-Encoding，让代理别压缩
          proxyReq.removeHeader('accept-encoding')
        },
        onProxyRes(proxyRes /*, req, res */) {
          //  移除任何压缩头，确保浏览器即收即读
          delete proxyRes.headers['content-encoding'];
          delete proxyRes.headers['content-length']; // 避免长度不匹配警告
        },
        }, 
      '/ai-explain': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
      '/feedback': {
        target: 'http://localhost:5000',
        changeOrigin: true
      },
    },
  },
})
