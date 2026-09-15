import react from "@vitejs/plugin-react";
import { defineConfig } from "vite";

// Proxy /api to the FastAPI backend during local development so the
// frontend can call relative paths without hardcoding a host/port.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": {
        target: "http://localhost:8000",
        changeOrigin: true,
      },
    },
  },
});
