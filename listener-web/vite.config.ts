import { defineConfig } from 'vite';
import { fileURLToPath, URL } from 'node:url';
import { svelte } from '@sveltejs/vite-plugin-svelte';
import tailwindcss from '@tailwindcss/vite';

export default defineConfig({
  base: '/',
  plugins: [svelte(), tailwindcss()],
  resolve: { alias: { $lib: fileURLToPath(new URL('./src/lib', import.meta.url)) } },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
    assetsDir: 'assets'
  }
});
