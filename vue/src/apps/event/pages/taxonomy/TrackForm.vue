<template>
  <dialog-form :icon="iconLabel" :title="$t('models.track')" size="xs">
    <template #page>
      <div class="q-py-md q-px-lg">
        <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
          <q-input v-model="formData.name" :label="`${$t('fields.name')} *`" dense class="col-12 col-md-9" />
          <q-input
            v-model.number="formData.position"
            :label="$t('fields.position')"
            type="number"
            dense
            class="col-12 col-md"
          />
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

import { useStore } from '../../store';

import DialogForm from '@/components/forms/DialogForm.vue';

import { iconLabel } from '@/icons';

const props = defineProps<{
  obj?: Track;
}>();

const store = useStore();

const formData = ref({
  name: props.obj?.name || '',
  position: props.obj?.position || 0,
});

function createUpdate() {
  if (!formData.value.name) return;

  if (props.obj) store.updateTrack({ ...props.obj, ...formData.value });
  else store.createTrack(formData.value);
}
</script>
