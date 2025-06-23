<template>
  <div class="row full-height">
    <div class="col-12 col-lg-6" :class="{ 'q-pr-sm': $q.screen.gt.md }">
      <div class="column full-height">
        <q-input v-model="mutable" :label="label" dense autogrow bottom-slots :input-style="lineStyle">
          <template v-slot:hint>
            You can use Markdown to format your text; you can find more information about the
            <a href="https://commonmark.org/help/" target="_blank" rel="noopener">Markdown syntax here</a>.
          </template>
        </q-input>
      </div>
    </div>
    <div class="col-12 col-lg-6" :class="{ 'q-pl-sm': $q.screen.gt.md }">
      <div class="bg-grey-1 q-mt-sm q-py-sm q-px-md full-height">
        <marked-div :text="mutable" :style="lineStyle" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

import MarkedDiv from '@/components/MarkedDiv.vue';

const emit = defineEmits(['update:modelValue']);

const props = defineProps<{
  label: string;
  modelValue: string;
}>();

const mutable = ref<string>(props.modelValue);
const lineStyle = ref<string>('line-height: 1.3');

watch(mutable, (val) => {
  emit('update:modelValue', val);
});
</script>
