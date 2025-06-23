<template>
  <q-input
    v-model="mutable"
    :label="label"
    :dense="dense"
    :class="inputClass"
    :disable="disable"
    :readonly="readonly"
    :clearable="clearable"
    mask="xxxxxx"
    placeholder="1e64c8"
    prefix="#"
    lowercase
  >
    <template #append v-if="!readonly">
      <q-icon :name="iconPalette" :style="{ color: modelValue }" class="cursor-pointer" size="sm">
        <q-popup-proxy cover transition-show="scale" transition-hide="scale">
          <q-color v-model="colorPickerValue" format-model="hex" />
        </q-popup-proxy>
      </q-icon>
    </template>
  </q-input>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import { iconPalette } from '@/icons';

const props = defineProps<{
  modelValue: string;
  label?: string;
  dense?: boolean;
  inputClass?: string;
  disable?: boolean;
  readonly?: boolean;
  clearable?: boolean;
}>();

const emit = defineEmits<{
  'update:modelValue': [value: string];
}>();

const mutable = computed({
  get: () => {
    const value = props.modelValue;
    return value.startsWith('#') ? value.slice(1) : value;
  },
  set: (value: string) => {
    // Handle cleared value
    if (!value || value === '') {
      emit('update:modelValue', '');
      return;
    }
    const colorValue = value.startsWith('#') ? value : `#${value}`;
    emit('update:modelValue', colorValue);
  },
});

const colorPickerValue = computed({
  get: () => props.modelValue,
  set: (value: string) => {
    emit('update:modelValue', value);
  },
});
</script>
