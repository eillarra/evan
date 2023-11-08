<template>
  <q-select
    v-model="mutable"
    clearable
    dense
    rounded
    outlined
    :options="options"
    :label="label"
    options-dense
    emit-value
    map-options
    class="col-6 col-md-2"
    :bg-color="mutable !== null ? 'blue-1' : 'white'"
  >
    <template #selected-item="scope">
      <span class="ellipsis">{{ scope.opt.label }}</span>
    </template>
  </q-select>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const emit = defineEmits(['update:modelValue']);

const props = defineProps<{
  label: string;
  modelValue: string;
  options: { label: string; value: string | number | boolean | null }[];
}>();

const mutable = ref<string>(props.modelValue);

watch(mutable, (val) => {
  emit('update:modelValue', val);
});
</script>
