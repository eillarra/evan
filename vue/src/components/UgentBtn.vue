<style lang="scss">
.ugent__btn {
  font-family: 'UGent Panno Medium', 'Arial', sans-serif;
  font-size: 17px;
  line-height: 15px;
  padding: 12px 15px;

  &.bg-blue {
    background-color: #1e64c8 !important;
  }

  &.bg-yellow {
    background-color: #fdd200 !important;
  }
}
</style>

<template>
  <q-btn
    unelevated
    square
    no-caps
    :icon="icon"
    :label="label"
    text-color="dark"
    class="ugent__btn"
    :class="`bg-${color}`"
  />
</template>

<script setup lang="ts">
defineProps<{
  label: string;
  color?: string;
  icon?: string;
}>();
</script>
