import react from "@vitejs/plugin-react";
import { defineConfig, loadEnv } from "vite";

// 开发代理目标来自环境变量（默认本机 8000 端口），源码页面只使用相对路径 /api
export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, process.cwd(), "");
  const target = env.VITE_API_PROXY_TARGET || "http://127.0.0.1:8000";
  return {
    plugins: [react()],
    server: {
      port: Number(env.VITE_PORT) || 5173,
      proxy: { "/api": { target, changeOrigin: false } },
    },
  };
});
