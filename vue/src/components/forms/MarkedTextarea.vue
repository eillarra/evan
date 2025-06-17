<template>
  <div class="row q-col-gutter-md full-height">
    <div class="col-12 col-lg-6">
      <div class="column full-height">
        <q-input v-model="mutable" :label="label" dense autogrow bottom-slots>
          <template v-slot:hint>
            You can use Markdown to format your text; you can find more information about the
            <a href="https://commonmark.org/help/" target="_blank" rel="noopener">Markdown syntax here</a>.
          </template>
        </q-input>
      </div>
    </div>
    <div class="col-12 col-lg-6">
      <div class="bg-grey-1 q-pa-md full-height">
        <marked-div :text="mutable" />
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

watch(mutable, (val) => {
  emit('update:modelValue', val);
});
</script>
