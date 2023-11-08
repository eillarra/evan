<template>
  <dialog-form :icon="props.obj ? iconImportantDates : iconAdd" :title="$t('models.important_date')" size="sm">
    <template #page>
      <div class="q-py-md q-px-lg">
        <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
          <q-input v-model="formData.label" :label="`${$t('fields.label')} *`" dense class="col-12" />
          <date-select
            v-model="formData.start_date"
            :label="`${$t('fields.start_date')} *`"
            dense
            class="col-12 col-md-6"
          />
          <date-select v-model="formData.end_date" :label="$t('fields.end_date')" dense class="col-12 col-md-6" />
          <q-checkbox v-model="formData.aoe" :label="$t('fields.aoe')" dense class="col-12 q-mt-md" />
        </div>
      </div>
    </template>
    <template #footer>
      <div class="flex q-gutter-sm q-pa-lg">
        <q-space />
        <q-btn
          v-close-popup
          unelevated
          @click="createUpdate"
          color="ugent"
          :label="props.obj ? $t('form.update') : $t('form.create')"
          :disable="!formData.label || !formData.start_date"
        />
      </div>
    </template>
  </dialog-form>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import DateSelect from '@/components/forms/DateSelect.vue';
import DialogForm from '@/components/forms/DialogForm.vue';

import { iconAdd, iconImportantDates } from '@/icons';

const emit = defineEmits(['create:obj', 'update:obj']);

const props = defineProps<{
  obj?: ImportantDate;
}>();

const formData = ref<ImportantDate>({
  label: props.obj?.label || '',
  format: props.obj?.format || 'date',
  start_date: props.obj?.start_date || '',
  end_date: props.obj?.end_date || null,
  aoe: props.obj?.aoe ?? true,
});

function createUpdate() {
  if (!formData.value.label || !formData.value.format || !formData.value.start_date) return;
  if (props.obj) emit('update:obj', props.obj, formData.value);
  else emit('create:obj', formData.value);
}
</script>
