import fs from 'fs';
import { resolve } from 'path';

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
      template: { transformAssetUrls },
    }),
    quasar(),
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
        manualChunks: (id: string) => {
          if (id.includes('node_modules/axios') || id.includes('node_modules/@sentry')) return 'helpers';
          if (id.includes('node_modules/quasar') || id.includes('node_modules/@quasar')) return 'quasar';
          if (id.includes('node_modules/vue') || id.includes('node_modules/pinia')) return 'vue';
        },
      },
    },
  },
  define: {
    __VUE_I18N_FULL_INSTALL__: true,
    __VUE_I18N_LEGACY_API__: false,
    __INTLIFY_PROD_DEVTOOLS__: false,
  },
  test: {
    globals: true,
    environment: 'happy-dom',
    include: ['**/__tests__/**/*.{test,spec}.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'html', 'lcov'],
      reportsDirectory: resolve(__dirname, '.coverage_ts'),
    },
  },
});
