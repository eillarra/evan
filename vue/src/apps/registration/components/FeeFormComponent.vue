<template>
  <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
    <template v-for="(criteria, idx) in visibleCriteria" :key="idx">
      <q-select
        v-model="formData[idx]"
        :label="criteria.question + ' *'"
        :options="criteria.options"
        emit-value
        map-options
        dense
        options-dense
        class="col-12"
      />
      <template v-if="showExtraDataFields(criteria)">
        <q-input
          v-for="field in criteria.extra_data_fields"
          :key="field.code"
          v-model="extraData[field.code] as string | number | null | undefined"
          :label="field.required ? field.label + ' *' : field.label"
          :required="field.required"
          dense
          class="col-12"
        />
      </template>
    </template>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref, watch } from 'vue';

const emit = defineEmits(['update:fee', 'update:extraData']);

const props = defineProps<{
  feeConfig: FeeSelectionConfig;
}>();

const fee = defineModel<string>('fee');
const extraData = defineModel<{ [key: string]: unknown }>('extraData', { type: Object, default: () => ({}) });
const formData = ref<(string | null)[]>([]);
const selectedFee = ref<string>('');

const visibleCriteria = computed(() => {
  if (!props.feeConfig || !props.feeConfig.criteria) {
    return [];
  }

  const visible: SelectionCriteria[] = [];

  for (let i = 0; i < props.feeConfig.criteria.length; i++) {
    const criteria = props.feeConfig.criteria[i];

    if (!criteria.depends_on) {
      visible.push(criteria);
    } else {
      const [dependencyField, validValues] = criteria.depends_on;
      const idx = props.feeConfig.criteria.findIndex((c) => c.code === dependencyField);

      if (validValues.includes(formData.value[idx] as string)) {
        visible.push(criteria);
      }
    }
  }
  return visible;
});

const showExtraDataFields = (criteria: SelectionCriteria) => {
  if (!criteria.extra_data_fields) {
    return false;
  }

  const idx = props.feeConfig.criteria.findIndex((c: SelectionCriteria) => c.code === criteria.code);
  const selectedValue = formData.value[idx];

  return criteria.extra_data_fields.some((field) => {
    if (!field.show_for || field.show_for.length === 0) {
      return true; // Show if show_for is not defined
    }
    return field.show_for.includes(selectedValue as string);
  });
};

const resetFormData = () => {
  for (let i = 0; i < props.feeConfig.criteria.length; i++) {
    const criteria = props.feeConfig.criteria[i];
    if (criteria.depends_on) {
      const [dependencyField, validValues] = criteria.depends_on;
      const idx = props.feeConfig.criteria.findIndex((c) => c.code === dependencyField);

      if (!validValues.includes(formData.value[idx] as string)) {
        formData.value[i] = null;
      }
    }
  }
};

onMounted(() => {
  formData.value = (fee.value ?? '').split('__');
  resetFormData();

  if (extraData.value) {
    extraData.value = { ...extraData.value };
  }
});

watch(
  () => formData.value,
  () => {
    emit('update:fee', formData.value.filter((value) => value !== null).join('__'));
    resetFormData();

    // Update extraData based on visible criteria
    const newExtraData: { [key: string]: unknown } = { ...extraData.value };
    visibleCriteria.value.forEach((criteria) => {
      if (criteria.extra_data_fields) {
        criteria.extra_data_fields.forEach((field) => {
          const idx = props.feeConfig.criteria.findIndex((c: SelectionCriteria) => c.code === criteria.code);
          const selectedValue = formData.value[idx];
          const shouldShow = field.show_for ? field.show_for.includes(selectedValue as string) : true;

          if (!shouldShow) {
            delete newExtraData[field.code];
          }
        });
      }
    });
    emit('update:extraData', newExtraData);
  },
  { deep: true },
);

watch(
  () => fee.value,
  (val) => {
    selectedFee.value = val ?? '';
    formData.value = (val ?? '').split('__');
    resetFormData();
  },
);
</script>
