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
        <update-btn
          @click="createUpdate"
          :disabled="!formData.name"
          :loading="loading"
          :label="props.obj ? $t('form.update') : $t('form.create')"
        />
      </div>
    </template>
  </dialog-form>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import { useStore } from '../../store';
import { useMinimumLoading } from '@/composables/useMinimumLoading';

import UpdateBtn from '@/components/buttons/UpdateBtn.vue';
import DialogForm from '@/components/forms/DialogForm.vue';

import { iconLabel } from '@/icons';

const props = defineProps<{
  obj?: Track;
}>();

const store = useStore();
const { loading, executeWithMinLoading } = useMinimumLoading();

const formData = ref({
  name: props.obj?.name || '',
  position: props.obj?.position || 0,
});

async function createUpdate() {
  if (!formData.value.name) return;

  await executeWithMinLoading(async () => {
    if (props.obj) {
      await store.updateTrack({ ...props.obj, ...formData.value });
    } else {
      await store.createTrack(formData.value);
    }
  });
}
</script>
