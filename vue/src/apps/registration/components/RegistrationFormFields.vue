<template>
  <div class="row q-col-gutter-y-sm q-col-gutter-x-md q-mt-md">
    <template v-for="field in visibleFields" :key="field.code">
      <q-checkbox
        v-if="field.field_type === 'checkbox'"
        v-model="extraData[field.code] as boolean"
        :label="field.required ? field.label + ' *' : field.label"
        keep-color
        class="col-12"
      />
      <q-input
        v-else
        v-model="extraData[field.code] as string | number | null | undefined"
        :label="field.required ? field.label + ' *' : field.label"
        :type="field.field_type === 'number' ? 'number' : 'text'"
        :required="field.required"
        dense
        class="col-12"
      />
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, watch } from 'vue';

const props = defineProps<{
  fields: ExtraDataField[];
  feeType?: string;
}>();

const extraData = defineModel<{ [key: string]: unknown }>('extraData', { type: Object, default: () => ({}) });

const visibleFields = computed<ExtraDataField[]>(() => {
  if (!props.fields?.length) {
    return [];
  }

  return props.fields.filter((field) => {
    if (!field.show_for || field.show_for.length === 0) {
      return true;
    }
    if (!props.feeType) {
      return false;
    }

    return field.show_for.includes(props.feeType);
  });
});

watch(
  () => [visibleFields.value.map((field) => field.code).join(','), props.feeType],
  () => {
    const visibleCodes = new Set(visibleFields.value.map((field) => field.code));
    const nextExtraData = { ...extraData.value };
    let changed = false;

    props.fields.forEach((field) => {
      if (!visibleCodes.has(field.code) && Object.prototype.hasOwnProperty.call(nextExtraData, field.code)) {
        delete nextExtraData[field.code];
        changed = true;
      }
    });

    if (changed) {
      extraData.value = nextExtraData;
    }
  },
  { immediate: true },
);
</script>
