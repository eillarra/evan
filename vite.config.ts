const fs = require('fs');
const { resolve } = require('path');

import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import { quasar, transformAssetUrls } from '@quasar/vite-plugin';

// read apps folder and create a list of entries
const apps = fs.readdirSync(resolve(__dirname, './vue/src/apps'));
const appsToBuild = {};
apps.forEach((app) => {
  appsToBuild[app] = resolve(__dirname, `./vue/src/apps/${app}/main.ts`);
});

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [
    vue({
      template: { transformAssetUrls }
    }),
    quasar()
  ],
  root: resolve('./vue/src'),
  base: '/static/vite/',
  server: {
    host: 'localhost',
    port: 5173,
    open: false,
    watch: {
      usePolling: true,
      disableGlobbing: false,
    },
  },
  resolve: {
    extensions: ['.vue', '.ts', '.js', '.json'],
    alias: {
      '@': resolve(__dirname, './vue/src'),
    },
  },
  build: {
    outDir: resolve('./vue/dist'),
    assetsDir: '',
    manifest: 'manifest.json',
    emptyOutDir: true,
    target: 'es2020',
    rollupOptions: {
      input: appsToBuild,
      output: {
        chunkFileNames: undefined,
        manualChunks: {
          helpers: ['axios', '@sentry/vue'],
          quasar: ['quasar'],
          vue: ['vue', 'vue-router', 'pinia'],
        },
      },
    },
  },
  define: {
    __VUE_I18N_FULL_INSTALL__: true,
    __VUE_I18N_LEGACY_API__: false,
    __INTLIFY_PROD_DEVTOOLS__: false,
  },
});
