// 开发环境将同源 /api 请求代理到本地 FastAPI，生产环境由 Nginx 接管。
import {defineConfig} from 'vite'
import vue from '@vitejs/plugin-vue'

export default defineConfig({
    plugins: [vue()],
    server: {
        proxy: {
            "/api": {
                target: "http://localhost:8000",
                changeOrigin: true,
                configure: (proxy) => {
                    proxy.on("proxyReq", (proxyReq) => {
                        proxyReq.setHeader("Cache-Control", "no-cache");
                        proxyReq.setHeader("Connection", "keep-alive");
                    });
                },
            },
        },
    },
});
