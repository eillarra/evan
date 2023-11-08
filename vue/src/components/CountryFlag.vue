<template>
  <i :class="getCountryClass(code)"></i>
</template>

<script setup lang="ts">
defineProps<{
  code: string | null;
}>();

function getCountryClass(code: string | null) {
  const flag = !code || code == '' ? 'zz' : code.toLowerCase();
  return `flag-sprite flag-${flag[0]} flag-_${flag[1]}`;
}
</script>
