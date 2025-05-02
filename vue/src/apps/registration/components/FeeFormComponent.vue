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
  validFees: string[];
}>();

const fee = defineModel<string>('fee');
const extraData = defineModel<{ [key: string]: unknown }>('extraData', { type: Object, default: () => ({}) });
const formData = ref<(string | null)[]>([]);

const visibleCriteria = computed(() => {
  if (!props.feeConfig || !props.feeConfig.criteria) {
    return [];
  }
  const visible: SelectionCriteria[] = [];
  const currentFormData = formData.value; // Use the current state

  for (let i = 0; i < props.feeConfig.criteria.length; i++) {
    const criteria = props.feeConfig.criteria[i];
    if (!criteria.depends_on) {
      visible.push(criteria);
    } else {
      const [dependencyField, validValues] = criteria.depends_on;
      const idx = props.feeConfig.criteria.findIndex((c) => c.code === dependencyField);
      if (idx !== -1 && validValues.includes(currentFormData[idx] as string)) {
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
      return true;
    }
    return field.show_for.includes(selectedValue as string);
  });
};

const checkFormData = () => {
  // This function ensures formData array is consistent with dependencies and visibility rules.
  let changed = false;
  const currentFormData = formData.value; // Capture state at start of check

  // Determine visibility based on currentFormData *before* making changes
  const isVisibleMap = new Map<string, boolean>();
  const currentVisible: SelectionCriteria[] = []; // Keep track of criteria determined visible in this pass
  for (let i = 0; i < props.feeConfig.criteria.length; i++) {
    const criteria = props.feeConfig.criteria[i];
    let isVisible = false;
    if (!criteria.depends_on) {
      isVisible = true;
    } else {
      const [dependencyField, validValues] = criteria.depends_on;
      const depIdx = props.feeConfig.criteria.findIndex((c) => c.code === dependencyField);
      if (depIdx !== -1 && validValues.includes(currentFormData[depIdx] as string)) {
        isVisible = true;
      }
    }
    isVisibleMap.set(criteria.code, isVisible);
    if (isVisible) {
      currentVisible.push(criteria);
    }
  }

  // Now iterate and modify formData based on visibility and validity
  for (let i = 0; i < props.feeConfig.criteria.length; i++) {
    const criteria = props.feeConfig.criteria[i];
    const isCriterionVisible = isVisibleMap.get(criteria.code) ?? false;

    if (!isCriterionVisible) {
      // If this criterion is NOT visible, ensure its data is null
      if (formData.value[i] !== null) {
        // console.log(`Hiding criteria ${criteria.code}, setting formData[${i}] to null`);
        formData.value[i] = null;
        changed = true;
      }
    } else {
      // If it IS visible, check if its current value is valid for its options
      const optionValues = criteria.options.map((option) => option.value);
      if (formData.value[i] !== null && !optionValues.includes(formData.value[i] as string)) {
        // Value is invalid for the available options, reset it
        // console.log(`Criteria ${criteria.code} visible, but value ${formData.value[i]} invalid. Resetting.`);
        const defaultOption = criteria.options.find((option) => option.is_default);
        formData.value[i] = defaultOption ? defaultOption.value : null;
        changed = true;
      }
      // If value is null, but it's visible, do we select default?
      // Let's only reset if the *existing* value becomes invalid or criterion becomes hidden.
      // Selecting a default automatically might override user intent.
    }
  }
  // Return true if formData was modified
  return changed;
};

onMounted(() => {
  // Initialize formData based on initial fee
  const initialFeeParts = (fee.value ?? '').split('__');
  // Ensure formData has the correct length, padding with null if needed
  formData.value = Array.from({ length: props.feeConfig.criteria.length }, (_, i) => initialFeeParts[i] ?? null);

  // Run checkFormData to potentially correct initial state based on dependencies/defaults
  checkFormData(); // Clean formData first

  // Initialize extraData (ensure it's an object)
  if (!extraData.value || typeof extraData.value !== 'object') {
    extraData.value = {};
  } else {
    // Ensure reactivity if passed as prop initially
    extraData.value = { ...extraData.value };
  }

  // Clean initial extraData based on the *final* state after checkFormData
  const finalVisibleCriteriaOnMount = visibleCriteria.value; // Use computed property reflecting cleaned formData
  const finalVisibleCodesOnMount = new Set(finalVisibleCriteriaOnMount.map((c) => c.code));
  const initialExtraData = { ...extraData.value };
  let extraDataChanged = false;

  props.feeConfig.criteria.forEach((criteria, idx) => {
    if (criteria.extra_data_fields) {
      const isVisible = finalVisibleCodesOnMount.has(criteria.code);
      const selectedValue = formData.value[idx]; // Use cleaned value
      criteria.extra_data_fields.forEach((field) => {
        // Field should be shown if criteria is visible AND show_for condition met
        const shouldShowField = isVisible && (field.show_for ? field.show_for.includes(selectedValue as string) : true);
        if (!shouldShowField && initialExtraData.hasOwnProperty(field.code)) {
          delete initialExtraData[field.code];
          extraDataChanged = true;
        }
      });
    }
  });
  if (extraDataChanged) {
    extraData.value = initialExtraData; // Update the model if cleaning occurred
  }
});

watch(
  () => formData.value,
  () => {
    // Run cleaning logic *before* emitting updates.
    // checkFormData modifies formData.value directly if needed.
    checkFormData();

    // Emit the fee based on the potentially cleaned formData
    const newFee = formData.value.filter((value) => value !== null).join('__');
    // Avoid emitting if the value hasn't actually changed after cleaning
    // This check is important to prevent loops if checkFormData cleaned the data
    if (fee.value !== newFee) {
      emit('update:fee', newFee);
    }

    // Update extraData based on the *final* visible criteria and formData state
    // Use the computed property which reacts to the potentially cleaned formData
    const finalVisibleCriteria = visibleCriteria.value;
    const finalVisibleCodes = new Set(finalVisibleCriteria.map((c) => c.code));
    const newExtraData: { [key: string]: unknown } = { ...extraData.value };
    let extraDataChanged = false;

    props.feeConfig.criteria.forEach((criteria, idx) => {
      if (criteria.extra_data_fields) {
        const isVisible = finalVisibleCodes.has(criteria.code);
        const selectedValue = formData.value[idx]; // Use final cleaned value

        criteria.extra_data_fields.forEach((field) => {
          // Determine if field should be shown based on final state
          const shouldShowField =
            isVisible && (field.show_for ? field.show_for.includes(selectedValue as string) : true);

          if (!shouldShowField) {
            // If field should not be shown, remove its data if it exists
            if (newExtraData.hasOwnProperty(field.code)) {
              delete newExtraData[field.code];
              extraDataChanged = true;
            }
          }
          // We don't add fields here, just remove obsolete ones.
          // v-model on the input handles adding data when it becomes visible.
        });
      }
    });

    // Emit only if the extraData object has actually changed
    if (extraDataChanged) {
      // Use JSON check for robust object comparison, although simple flag works here
      if (JSON.stringify(extraData.value) !== JSON.stringify(newExtraData)) {
        emit('update:extraData', newExtraData);
      }
    }
  },
  { deep: true }, // Deep watch needed as formData is an array
);

watch(
  () => fee.value,
  (newFee) => {
    // Calculate the fee string based on the current internal formData state
    const currentFormDataFee = formData.value.filter((value) => value !== null).join('__');

    // Only proceed if the external change is different from the internal state's fee
    // This prevents infinite loops when the change originates from the formData watcher above
    if (newFee === currentFormDataFee) {
      return;
    }

    // Update internal formData based on the new external fee value
    const newFeeParts = (newFee ?? '').split('__');
    // Ensure formData array has the correct length, padding with null
    const newFormData = Array.from({ length: props.feeConfig.criteria.length }, (_, i) => newFeeParts[i] ?? null);

    // Update the formData ref. This will trigger the formData watcher.
    // The formData watcher will then call checkFormData and handle emitting updates.
    formData.value = newFormData;
  },
);
</script>
