<template>
  <q-dialog :model-value="modelValue" @update:model-value="$emit('update:modelValue', $event)" persistent>
    <q-card style="min-width: 600px">
      <q-card-section>
        <div class="text-h6">{{ title }}</div>
      </q-card-section>
      <q-card-section class="q-pt-none">
        <q-input
          :model-value="searchQuery"
          @update:model-value="(value) => $emit('update:searchQuery', String(value || ''))"
          :placeholder="searchPlaceholder"
          outlined
          dense
          clearable
        >
          <template v-slot:prepend>
            <q-icon :name="iconSearch" />
          </template>
        </q-input>
        <div class="q-mt-md" style="max-height: 400px; overflow-y: auto">
          <q-list>
            <slot name="items" />
          </q-list>
        </div>
      </q-card-section>

      <q-card-actions align="right">
        <q-btn flat :label="cancelLabel" @click="$emit('update:modelValue', false)" />
      </q-card-actions>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { iconSearch } from '@/icons';

interface Props {
  modelValue: boolean;
  title: string;
  searchPlaceholder: string;
  searchQuery: string;
  cancelLabel?: string;
}

withDefaults(defineProps<Props>(), {
  cancelLabel: 'Cancel',
});

defineEmits<{
  'update:modelValue': [value: boolean];
  'update:searchQuery': [value: string];
}>();
</script>
