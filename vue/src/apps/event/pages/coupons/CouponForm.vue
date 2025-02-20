<template>
  <dialog-form :icon="props.obj ? iconCoupon : iconAdd" :title="$t('models.coupon')" size="xs">
    <template #page>
      <div class="q-py-md q-px-lg">
        <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
          <readonly-field v-if="obj" :value="obj.code" :label="$t('fields.code')" class="col-12" with-copy />
          <q-input v-model="formData.value" :label="`${$t('fields.value')} *`" type="number" dense class="col-12" />
          <q-input v-model.trim="formData.notes" :label="`${$t('fields.note', 9)} *`" dense class="col-12" />
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
          :disable="!formData.value || !formData.notes"
        />
      </div>
    </template>
  </dialog-form>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import { useStore } from '../../store.js';

import DialogForm from '@/components/forms/DialogForm.vue';
import ReadonlyField from '@/components/forms/ReadonlyField.vue';

import { iconAdd, iconCoupon } from '@/icons';

const props = defineProps<{
  obj?: Coupon;
}>();

const store = useStore();

const formData = ref<CouponData>({
  value: props.obj?.value || 0,
  notes: props.obj?.notes || '',
});

function createUpdate() {
  if (!formData.value.value || !formData.value.notes) return;

  if (props.obj) store.updateCoupon({ ...props.obj, ...formData.value });
  else store.createCoupon(formData.value);
}
</script>
