import { defineConfig } from "vite";
import react from "@vitejs/plugin-react-swc";
import path from "path";
import { fileURLToPath } from "url";
import { dirname } from "path";

const __filename = fileURLToPath(import.meta.url);
const __dirname = dirname(__filename);

export default defineConfig({
  plugins: [react()],

  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
    dedupe: ["react", "react-dom"],
  },

  server: {
    host: "0.0.0.0",
    port: 4173,

    // IMPORTANT: ensures React Router deep links work (e.g. /scanner)
    fs: {
      strict: false,
    },

    hmr: {
      host: "localhost",
      overlay: false,
    },
  },

  preview: {
    port: 8080,
    strictPort: true,
  },

  optimizeDeps: {
    include: ["react", "react-dom"],
    force: true,
  },
});