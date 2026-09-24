import js from '@eslint/js';
import tsPlugin from '@typescript-eslint/eslint-plugin';
import tsParser from '@typescript-eslint/parser';
import prettier from 'eslint-config-prettier';
import pluginVue from 'eslint-plugin-vue';
import globals from 'globals';

export default [
  {
    ignores: ['vue/dist/**', 'node_modules/**', '.yarn/**', '.coverage_ts/**'],
  },

  js.configs.recommended,

  // https://eslint.vuejs.org/user-guide/#bundle-configurations
  // Priority A: Essential (Error Prevention)
  ...pluginVue.configs['flat/essential'],

  {
    files: ['**/*.ts', '**/*.d.ts'],
    languageOptions: {
      parser: tsParser,
      parserOptions: { ecmaVersion: 'latest', sourceType: 'module' },
    },
  },

  {
    files: ['**/*.vue'],
    languageOptions: {
      // `vue-eslint-parser` is set by the plugin:vue config; the TypeScript parser is
      // nested so it handles the `<script lang="ts">` block inside .vue files.
      parserOptions: {
        parser: tsParser,
        extraFileExtensions: ['.vue'],
        ecmaVersion: 'latest',
        sourceType: 'module',
      },
    },
  },

  {
    files: ['vue/src/**/*.{js,ts,vue}', '*.{js,mjs,ts}'],
    languageOptions: {
      globals: {
        ...globals.browser,
        ...globals.node,
      },
    },
    plugins: {
      '@typescript-eslint': tsPlugin,
    },
    rules: {
      ...tsPlugin.configs.recommended.rules,

      'prefer-promise-reject-errors': 'off',

      // Pre-existing `any` usages need real domain types (API payload and error shapes)
      // before this can be promoted to an error. Kept visible so the count only goes down.
      '@typescript-eslint/no-explicit-any': 'warn',

      quotes: ['warn', 'single', { avoidEscape: true }],

      // this rule, if on, would require explicit return type on the `render` function
      '@typescript-eslint/explicit-function-return-type': 'off',

      // TypeScript itself resolves identifiers, including ambient .d.ts globals,
      // so the core rules produce false positives here.
      // https://typescript-eslint.io/troubleshooting/faqs/eslint/#i-get-errors-from-no-undef
      'no-undef': 'off',
      'no-unused-vars': 'off',
      // `noUnusedLocals` / `noUnusedParameters` in tsconfig.json cover this, and unlike
      // ESLint they resolve kebab-case component usage in Vue templates.
      '@typescript-eslint/no-unused-vars': 'off',

      // allow debugger during development only
      'no-debugger': process.env.NODE_ENV === 'production' ? 'error' : 'off',
    },
  },

  // Must stay last so it can switch off stylistic rules handled by Prettier.
  prettier,
];