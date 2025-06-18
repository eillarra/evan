<template>
  <dialog-form :icon="props.obj ? iconCoupon : iconAdd" :title="$t('models.coupon')" size="sm">
    <template #page>
      <div class="q-py-md q-px-lg">
        <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
          <readonly-field v-if="obj" :value="obj.code" :label="$t('fields.code')" class="col-12" with-copy />
          <q-input
            v-model="formData.value"
            :label="`${$t('fields.value')} *`"
            type="number"
            dense
            class="col-12 col-sm-3"
          />
          <q-select
            v-model="formData.coverage"
            :label="$t('fields.coverage')"
            :options="coverageOptions"
            emit-value
            map-options
            dense
            options-dense
            class="col-12 col-sm-9"
          />
          <q-input v-model.trim="formData.notes" :label="`${$t('fields.note', 9)} *`" dense class="col-12" />
          <template v-if="linkedRegistration">
            <readonly-field :value="linkedRegistration.user.name" :label="$t('fields.used_by')" class="col-12" />
            <readonly-field :value="linkedRegistration.total_fee" :label="$t('fields.fee')" class="col-12 col-sm-3" />
            <readonly-field
              :value="linkedRegistration.uuid"
              :label="$t('models.registration')"
              class="col-12 col-sm-9"
              with-copy
            />
          </template>
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
import { computed, ref } from 'vue';
import { storeToRefs } from 'pinia';

import { useStore } from '../../store';

import DialogForm from '@/components/forms/DialogForm.vue';
import ReadonlyField from '@/components/forms/ReadonlyField.vue';

import { iconAdd, iconCoupon } from '@/icons';

const props = defineProps<{
  obj?: Coupon;
}>();

const store = useStore();

const { registrations } = storeToRefs(store);

const formData = ref<CouponData>({
  value: props.obj?.value || 0,
  notes: props.obj?.notes || '',
  coverage: props.obj?.coverage || 'base_fee',
});

const coverageOptions = [
  { label: 'Base fee only', value: 'base_fee' },
  { label: 'All fees', value: 'all_fees' },
];

const linkedRegistration = computed<Registration | null>(() => {
  if (!props.obj) return null;
  return registrations.value.find((r) => r.coupon?.id === props.obj?.id) || null;
});

function createUpdate() {
  if (!formData.value.value || !formData.value.notes) return;

  if (props.obj) store.updateCoupon({ ...props.obj, ...formData.value });
  else store.createCoupon(formData.value);
}
</script>
