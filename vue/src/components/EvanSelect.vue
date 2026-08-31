<template>
  <q-select
    v-model="mutable"
    :label="label"
    :options="options"
    :dense="!notDense"
    :options-dense="!notDense"
    emit-value
    map-options
    :multiple="multiple"
  >
    <template #selected-item="scope">
      <span class="row items-center no-wrap ellipsis">
        <q-icon v-if="scope.opt.icon" :name="scope.opt.icon" class="q-mr-xs" size="20px" />
        {{ scope.opt.label }}
      </span>
    </template>
    <template #option="scope">
      <q-item v-bind="scope.itemProps">
        <q-item-section v-if="scope.opt.icon" avatar style="min-width: 36px">
          <q-icon :name="scope.opt.icon" size="24px" />
        </q-item-section>
        <q-item-section>{{ scope.opt.label }}</q-item-section>
      </q-item>
    </template>
    <template v-if="$slots.append" #append>
      <slot name="append" />
    </template>
  </q-select>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue';

const emit = defineEmits(['update:modelValue']);

const props = defineProps<{
  label: string;
  modelValue: string | number | boolean | null | (string | number)[];
  options: { label: string; value: string | number | boolean | null; icon?: string }[];
  multiple?: boolean;
  notDense?: boolean;
}>();

const mutable = ref<string | number | boolean | null | (string | number)[]>(props.modelValue);

watch(mutable, (val) => {
  emit('update:modelValue', val);
});
</script>
