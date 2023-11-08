<template>
  <dialog-form :icon="iconContact" :title="$t('models.person')" size="sm">
    <template #page>
      <div class="q-py-md q-px-lg">
        <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
          <q-input v-model="formData.name" dense :label="`${$t('fields.name')} *`" class="col-12" />
          <q-input v-model="formData.affiliation" dense :label="$t('fields.affiliation')" class="col-12" />
          <q-input v-model="formData.email" dense type="email" :label="$t('fields.email')" class="col-12" />
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
          :disable="!formData.name"
        />
      </div>
    </template>
  </dialog-form>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import DialogForm from '@/components/forms/DialogForm.vue';

import { iconContact } from '@/icons';

const emit = defineEmits(['create:obj', 'update:obj']);

const props = defineProps<{
  obj?: Person;
}>();

const formData = ref({
  name: props.obj?.name || '',
  affiliation: props.obj?.affiliation || null,
  country_code: props.obj?.country_code || null,
  email: props.obj?.email || null,
});

function createUpdate() {
  if (!formData.value.name) return;
  if (props.obj) emit('update:obj', props.obj, formData.value);
  else emit('create:obj', formData.value);
}
</script>
