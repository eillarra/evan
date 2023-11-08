<template>
  <div>
    <q-splitter v-model="split" :horizontal="$q.screen.lt.md" :limits="[40, 80]" class="q-py-lg">
      <template v-slot:before>
        <div :class="{ 'q-pr-md': !$q.screen.lt.md, 'q-pb-md': $q.screen.lt.md }">
          <q-input v-model="mutable" :label="label" autogrow bottom-slots class="q-pt-none">
            <template v-slot:hint>
              You can use Markdown to format your text; you can find more information about the
              <a href="https://commonmark.org/help/" target="_blank" rel="noopener">Markdown syntax here</a>.
            </template>
          </q-input>
        </div>
      </template>
      <template v-slot:after>
        <div :class="{ 'q-pl-md': !$q.screen.lt.md, 'q-pt-md': $q.screen.lt.md }">
          <marked-div :text="mutable" class="bg-grey-1 q-mt-sm q-pa-md" />
        </div>
      </template>
    </q-splitter>
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

const split = ref<number>(50);
const mutable = ref<string>(props.modelValue);

watch(mutable, (val) => {
  emit('update:modelValue', val);
});
</script>
