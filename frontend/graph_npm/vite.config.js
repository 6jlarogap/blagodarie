import { defineConfig } from 'vite'
import FullReload from 'vite-plugin-full-reload'

export default defineConfig(({ command }) => ({
    plugins: [
        FullReload(['public/js/*', 'public/css/*', 'public/images/*', 'public/res/*'])
    ],
    build: {
        chunkSizeWarningLimit: 1600,
    },
    publicDir: command === "serve" ? "public" : false,
    server: { port: 5001 },
}));
