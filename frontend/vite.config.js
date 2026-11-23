import { defineConfig, loadEnv } from 'vite';
import react from '@vitejs/plugin-react';

// Proxy local: conecta con Django sin modificar el backend original.
export default defineConfig(({ mode }) => {
    const entorno = loadEnv(mode, process.cwd(), 'VITE_');
    return {
        plugins: [react()],
        server: { proxy: { '/api': { target: entorno.VITE_BACKEND_URL || 'http://127.0.0.1:8000', changeOrigin: true } } }
    };
});
