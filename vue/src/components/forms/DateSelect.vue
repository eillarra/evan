<template>
  <q-input
    v-model="text"
    dense
    :label="label || $t('field.date', 9)"
    :disable="disable"
    :readonly="readonly"
    placeholder="YYYY-MM-DD HH:mm"
  >
    <template v-slot:append v-if="!readonly">
      <template v-if="calendarType === 'date' || calendarType === 'datetime'">
        <q-icon :name="iconCalendarRange" size="xs" class="cursor-pointer">
          <q-popup-proxy cover transition-show="scale" transition-hide="scale">
            <q-date v-model="mutableDate" mask="YYYY-MM-DD" :options="dateOptions">
              <div class="row items-center justify-end">
                <q-btn v-close-popup :label="$t('form.close')" color="primary" flat />
              </div>
            </q-date>
          </q-popup-proxy>
        </q-icon>
      </template>
      <template v-if="calendarType === 'time' || calendarType === 'datetime'">
        <q-icon :name="iconTime" size="xs" class="cursor-pointer">
          <q-popup-proxy cover transition-show="scale" transition-hide="scale">
            <q-time v-model="mutableTime" format24h :options="timeOptions">
              <div class="row items-center justify-end">
                <q-btn v-close-popup :label="$t('form.close')" color="primary" flat />
              </div>
            </q-time>
          </q-popup-proxy>
        </q-icon>
      </template>
    </template>
  </q-input>
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
  minDate?: string | null | undefined;
  maxDate?: string | null | undefined;
}>();

const calendarType = computed<'datetime' | 'date' | 'time'>(() => {
  if (props.type) return props.type;
  return 'date';
});
const mutableDate = ref<string | null | undefined>(props.modelValue ? props.modelValue.split('T')[0] : null);
const mutableTime = ref<string | null | undefined>(props.modelValue ? props.modelValue.split('T')[1] : null);

// Date validation options
const dateOptions = computed(() => {
  if (!props.minDate && !props.maxDate) return undefined;

  return (date: string) => {
    if (props.minDate && date < props.minDate.split('T')[0]) return false;
    if (props.maxDate && date > props.maxDate.split('T')[0]) return false;
    return true;
  };
});

// Time validation options
const timeOptions = computed(() => {
  if (!props.options && !props.minDate && !props.maxDate) return undefined;

  return (hr: number, min: number | null, sec: number | null) => {
    // First apply custom options if provided
    if (props.options && !props.options(hr, min, sec)) return false;

    // Then apply datetime range validation
    if (mutableDate.value && (props.minDate || props.maxDate)) {
      const currentTime = `${hr.toString().padStart(2, '0')}:${(min || 0).toString().padStart(2, '0')}:${(sec || 0).toString().padStart(2, '0')}`;
      const currentDateTime = `${mutableDate.value}T${currentTime}`;

      if (props.minDate && currentDateTime < props.minDate) return false;
      if (props.maxDate && currentDateTime > props.maxDate) return false;
    }

    return true;
  };
});

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
