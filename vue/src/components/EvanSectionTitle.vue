<template>
  <h6 class="text-weight-bold q-mb-md" :class="{ 'q-mt-xl': !first, 'q-mt-none': first }">
    <slot></slot>
  </h6>
</template>

<script setup lang="ts">
defineProps<{
  first?: boolean;
}>();
</script>
