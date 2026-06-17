import { defineConfig } from "vite";
import vue from "@vitejs/plugin-vue";
import { MpaPlugin } from "@struggler/vite-plugin-mpa";
import path from "node:path";
import { fileURLToPath } from "node:url";

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const r = (...p) => path.resolve(__dirname, ...p);
const backendTarget = "http://127.0.0.1:8000";

export default defineConfig({
  plugins: [
    vue(),
    MpaPlugin({
      inject: {
        title: "智慧AI探索平台",
      },
    }),
  ],

  resolve: {
    alias: {
      "@": r("src"),
      "#": r("app"),
    },
  },

  server: {
    host: process.env.HOST || "0.0.0.0",
    port: 5173,
    open: "/",
    allowedHosts: true,
    proxy: {
      "/api":         backendTarget,
      "/docs":        backendTarget,
      "/openapi.json": backendTarget,
      "/doc":         backendTarget,
    },
  },

  build: {
    // FastAPI 静态挂载点：boot/static.py -> app/public
    outDir:     r("../backend/app/public"),
    assetsDir:  "_app",
    emptyOutDir: true,
    rollupOptions: {
      input: {
        index: r("app/admin/index.html"),
        login: r("app/login/index.html"),
      },
    },
  },
});
