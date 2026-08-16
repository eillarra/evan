<style type="scss">
.marked {
  h1,
  h2,
  h3 {
    margin: 1em 0;

    &:first-child {
      margin-top: 0;
    }
  }

  h1 {
    font-size: 1.5em;
  }

  h2 {
    font-size: 1.25em;
  }

  h3 {
    font-size: 1.1em;
  }
}
</style>

<template>
  <div v-if="text" v-html="html" class="marked" />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { render } from '@/utils/markdown';

const props = defineProps<{
  text: string;
}>();

const html = computed<string>(() => render(props.text));
</script>
