<template>
  <q-field
    v-model="mutable"
    dense
    :label="label || $t('field.date', 9)"
    :stack-label="mutable !== null"
    class="cursor-pointer"
    :disable="disable"
    :readonly="readonly"
  >
    <template #control>
      <span>{{ text }}</span>
    </template>
    <template #append v-if="!readonly">
      <q-icon
        ref="calendarBtn"
        :name="calendarType == 'time' ? iconTime : iconCalendarRange"
        size="xs"
        class="q-mx-xs"
      />
    </template>
    <template #default v-if="!readonly">
      <q-menu anchor="top end" self="bottom right">
        <template v-if="calendarType == 'datetime'">
          <q-date v-model="mutableDate" mask="YYYY-MM-DD" minimal />
          <q-time v-model="mutableTime" minimal :format24h="true" :options="options" />
        </template>
        <q-time v-else-if="calendarType == 'time'" v-model="mutableTime" minimal :format24h="true" :options="options" />
        <q-date v-else v-model="mutableDate" mask="YYYY-MM-DD" minimal />
      </q-menu>
    </template>
  </q-field>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import { iconCalendarRange, iconTime } from '@/icons';

const emit = defineEmits(['update:modelValue']);

const props = defineProps<{
  label?: string;
  type?: 'datetime' | 'date' | 'time' | undefined;
  modelValue: string | null | undefined;
  options?: (hr: number, min: number | null, sec: number | null) => boolean | null | undefined;
  disable?: boolean;
  readonly?: boolean;
}>();

const calendarBtn = ref<HTMLElement | null>(null);
const calendarType = computed<'datetime' | 'date' | 'time'>(() => {
  if (props.type) return props.type;
  return 'date';
});
const mutableDate = ref<string | null | undefined>(props.modelValue ? props.modelValue.split('T')[0] : null);
const mutableTime = ref<string | null | undefined>(props.modelValue ? props.modelValue.split('T')[1] : null);

const text = computed<string>(() => {
  if (!mutableDate.value && !mutableTime.value) return '';
  if (calendarType.value == 'time') return mutableTime.value ? mutableTime.value.substring(0, 5) : '';
  if (calendarType.value == 'date') return mutableDate.value || '';
  return `${mutableDate.value} ${mutableTime.value ? mutableTime.value.substring(0, 5) : ''}`;
});

watch([mutableDate, mutableTime], ([newDate, newTime]) => {
  if (calendarType.value == 'datetime') {
    emit('update:modelValue', newDate && newTime ? `${newDate}T${newTime}` : newDate || newTime);
  } else if (calendarType.value == 'date') {
    emit('update:modelValue', newDate);
  } else {
    emit('update:modelValue', newTime);
  }
});

watch(
  () => props.modelValue,
  (val) => {
    if (val) {
      mutableDate.value = val.split('T')[0];
      mutableTime.value = val.split('T')[1];
    } else {
      mutableDate.value = null;
      mutableTime.value = null;
    }
  },
);
</script>
