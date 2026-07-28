// Copy to frontend/vite.config.ts
// The `@` alias lets every component import as `@/components/...` / `@/pages/...`,
// matching the design-system pages. The proxy forwards /api to the FastAPI backend.
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import path from 'path';
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            '@': path.resolve(__dirname, './src'),
        },
    },
    server: {
        port: 5174,
        strictPort: true,
        proxy: {
            '/api': {
                target: 'http://localhost:8010',
                changeOrigin: true,
                ws: true,
            },
        },
    },
});
