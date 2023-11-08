<template>
  <dialog-form :icon="iconLabel" :title="$t('models.topic')" size="xs">
    <template #page>
      <div class="q-py-md q-px-lg">
        <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
          <q-input v-model="formData.name" :label="`${$t('fields.name')} *`" class="col-12" />
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

import { useStore } from '../../store.js';

import DialogForm from '@/components/forms/DialogForm.vue';

import { iconLabel } from '@/icons';

const props = defineProps<{
  obj?: Topic;
}>();

const store = useStore();

const formData = ref({
  name: props.obj?.name || '',
});

function createUpdate() {
  if (!formData.value.name) return;

  if (props.obj) store.updateTopic({ ...props.obj, ...formData.value });
  else store.createTopic(formData.value);
}
</script>
