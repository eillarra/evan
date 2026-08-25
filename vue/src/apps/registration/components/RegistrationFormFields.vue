<template>
  <div class="q-col-gutter-y-lg q-mt-md">
    <template v-for="field in visibleFields" :key="field.code">
      <div class="col-12">
        <div v-if="field.description" class="q-mb-xs">{{ field.description }}</div>

        <q-checkbox
          v-if="field.field_type === 'checkbox'"
          v-model="extraData[field.code] as boolean"
          :label="field.required ? field.label + ' *' : field.label"
          keep-color
        />

        <q-input
          v-else-if="field.field_type === 'time'"
          v-model="extraData[field.code] as string | null | undefined"
          :label="field.required ? field.label + ' *' : field.label"
          type="time"
          :required="field.required"
          dense
        />

        <div v-else-if="field.field_type === 'radio'" class="q-mb-sm">
          {{ field.required ? field.label + ' *' : field.label }}
          <q-list dense class="q-mt-md">
            <q-item v-for="option in field.options || []" :key="String(option.value)" tag="label">
              <q-item-section avatar>
                <q-radio
                  :model-value="extraData[field.code] as string | number | null | undefined"
                  :val="option.value"
                  keep-color
                  @update:model-value="extraData[field.code] = option.value"
                />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ option.label }}</q-item-label>
                <q-item-label v-if="option.description" caption>{{ option.description }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </div>

        <div v-else-if="field.field_type === 'multiselect'" class="q-mb-sm">
          {{ field.required ? field.label + ' *' : field.label }}
          <q-list dense>
            <q-item v-for="option in field.options || []" :key="String(option.value)" tag="label">
              <q-item-section avatar>
                <q-checkbox
                  :model-value="
                    (extraData[field.code] as (string | number)[] | undefined)?.includes(option.value) || false
                  "
                  keep-color
                  @update:model-value="toggleMultiselectOption(field, option.value)"
                />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ option.label }}</q-item-label>
                <q-item-label v-if="option.description" caption>{{ option.description }}</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </div>

        <q-select
          v-else-if="field.field_type === 'select'"
          v-model="extraData[field.code] as string | number | null | undefined"
          :label="field.required ? field.label + ' *' : field.label"
          :options="selectOptions(field)"
          emit-value
          map-options
          :required="field.required"
          dense
        />

        <q-input
          v-else
          v-model="extraData[field.code] as string | number | null | undefined"
          :label="field.required ? field.label + ' *' : field.label"
          :type="field.field_type === 'number' ? 'number' : 'text'"
          :required="field.required"
          dense
        />
      </div>
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

type SelectItem = { label: string; value: string | number };

function selectOptions(field: ExtraDataField): SelectItem[] {
  return (field.options || []).map((option) => ({ label: option.label, value: option.value }));
}

function toggleMultiselectOption(field: ExtraDataField, value: string | number): void {
  const current = (extraData.value[field.code] as (string | number)[] | undefined) || [];
  if (current.includes(value)) {
    extraData.value[field.code] = current.filter((item) => item !== value);
  } else {
    extraData.value[field.code] = [...current, value];
  }
}

function showWhenConditionMet(field: ExtraDataField): boolean {
  if (!field.show_when) {
    return true;
  }
  const [dependsOnCode, expectedValue] = field.show_when;
  return extraData.value[dependsOnCode] === expectedValue;
}

const visibleFields = computed<ExtraDataField[]>(() => {
  if (!props.fields?.length) {
    return [];
  }

  return props.fields.filter((field) => {
    if (field.show_for && field.show_for.length > 0) {
      if (!props.feeType || !field.show_for.includes(props.feeType)) {
        return false;
      }
    }
    return showWhenConditionMet(field);
  });
});

watch(
  () => [
    visibleFields.value.map((field) => field.code).join(','),
    props.feeType,
    JSON.stringify(
      props.fields.filter((field) => field.show_when).map((field) => extraData.value[field.show_when![0]]),
    ),
  ],
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
