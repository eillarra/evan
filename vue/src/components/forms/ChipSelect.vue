<style lang="scss">
.chip-select {
  .q-chip {
    &--selected {
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.25);
    }

    &:hover {
      box-shadow: 0 1px 4px rgba(0, 0, 0, 0.2);
    }
  }

  &--disabled .q-chip {
    cursor: not-allowed;
    opacity: 0.5;
  }
}
</style>

<template>
  <div class="chip-select row q-gutter-xs" :class="{ 'chip-select--disabled': disable }">
    <q-chip
      v-if="addAll"
      :color="isAllSelected ? 'primary' : 'dark'"
      :text-color="isAllSelected ? 'white' : 'dark'"
      :outline="!isAllSelected"
      :class="isAllSelected ? 'q-chip--selected' : ''"
      clickable
      :disable="disable"
      size="11px"
      @click="selectAll"
    >
      {{ allLabel }}
    </q-chip>
    <q-chip
      v-for="opt in options"
      :key="String(opt.value)"
      :color="isSelected(opt) ? 'primary' : 'dark'"
      :text-color="isSelected(opt) ? 'white' : 'dark'"
      :outline="!isSelected(opt)"
      :class="isSelected(opt) ? 'q-chip--selected' : ''"
      clickable
      :disable="disable"
      size="11px"
      @click="toggle(opt)"
    >
      {{ opt.label }}
    </q-chip>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';

const props = withDefaults(
  defineProps<{
    modelValue: unknown[] | unknown;
    options: QuasarSelectOption[];
    addAll?: boolean;
    allLabel?: string;
    multiple?: boolean;
    disable?: boolean;
  }>(),
  {
    addAll: false,
    multiple: true,
    disable: false,
  },
);

const emit = defineEmits<{
  'update:modelValue': [value: unknown[] | unknown];
}>();

const isMulti = computed(() => props.multiple);

const isAllSelected = computed(() => {
  if (!props.addAll) return false;
  if (isMulti.value) return Array.isArray(props.modelValue) && props.modelValue.length === 0;
  return props.modelValue === null || props.modelValue === undefined;
});

function isSelected(opt: QuasarSelectOption): boolean {
  if (isMulti.value) {
    return Array.isArray(props.modelValue) && props.modelValue.includes(opt.value);
  }
  return props.modelValue === opt.value;
}

function selectAll() {
  if (isMulti.value) {
    emit('update:modelValue', []);
  } else {
    emit('update:modelValue', null);
  }
}

function toggle(opt: QuasarSelectOption) {
  if (isMulti.value) {
    const current = Array.isArray(props.modelValue) ? [...props.modelValue] : [];
    const idx = current.indexOf(opt.value);
    if (idx >= 0) {
      current.splice(idx, 1);
    } else {
      current.push(opt.value);
    }
    emit('update:modelValue', current);
  } else {
    emit('update:modelValue', opt.value);
  }
}
</script>
