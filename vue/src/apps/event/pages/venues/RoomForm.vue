<template>
  <dialog-form :icon="iconRoom" :title="$t('models.room')" size="xs">
    <template #page>
      <div class="q-py-md q-px-lg">
        <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
          <q-input v-model="formData.name" :label="`${$t('fields.name')} *`" dense class="col-12 col-md-6" />
          <q-input
            v-model.number="formData.max_capacity"
            :label="$t('fields.capacity')"
            type="number"
            dense
            class="col-12 col-md-3"
          />
          <q-input
            v-model.number="formData.position"
            :label="$t('fields.position')"
            type="number"
            dense
            class="col-12 col-md-3"
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

import { iconRoom } from '@/icons';

const props = defineProps<{
  obj?: Room;
  parent?: Venue;
}>();

const emit = defineEmits<{
  (e: 'create:obj'): void;
  (e: 'update:obj'): void;
}>();

const store = useStore();
const { loading, executeWithMinLoading } = useMinimumLoading();

const formData = ref<RoomData>({
  name: props.obj?.name || '',
  max_capacity: props.obj?.max_capacity || 0,
  position: props.obj?.position || 0,
  venue: props.obj?.venue || props.parent?.id || 0,
});

async function createUpdate() {
  if (!formData.value.name || !formData.value.venue) return;

  await executeWithMinLoading(async () => {
    if (props.obj) {
      await store.updateRoom({ ...props.obj, ...formData.value });
      emit('update:obj');
    } else {
      await store.createRoom(formData.value);
      emit('create:obj');
    }
  });
}
</script>
