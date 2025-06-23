---
applyTo: "**/*.vue"
description: Vue 3, Quasar, and Pinia coding standards for the project.
---

Core architecture
-----------------

- Framework: Vue 3.
- API: Composition API with `<script setup lang="ts">` is mandatory.
- State management: Pinia is the only state management library.

Component structure
-------------------

- File order: `<style scoped>`, then `<template>`, then `<script setup>`.
- Styles: the `<style>` tag **must always** be `scoped`.
- Naming:
  - Component files: `PascalCase.vue`
  - Composable functions: `useSomething.ts`

Quasar Framework
----------------

- Components: always prefer Quasar components (`<q-btn>`, `<q-input>`, etc.) over native HTML elements.
- Styling: use Quasar's layout and spacing utility classes (`q-pa-md`, `row`, `col`, `text-h1`) instead of writing custom CSS for layout and typography.
