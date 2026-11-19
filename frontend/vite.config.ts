/// <reference types="node" />
import { defineConfig } from "vite";
import react from "@vitejs/plugin-react";

// In development the React app runs on Vite and the API on FastAPI.
// Requests to /api are passed through to the API, so the browser sees one origin.
const apiPort = process.env.PREDICTV_API_PORT ?? "8000";

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      "/api": { target: `http://127.0.0.1:${apiPort}`, changeOrigin: false },
      "/health": { target: `http://127.0.0.1:${apiPort}`, changeOrigin: false },
    },
  },
  build: { chunkSizeWarningLimit: 800 },
});
