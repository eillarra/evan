<style scoped></style>

<template>
  <dialog-form :icon="iconSponsor" :title="$t('models.sponsor')" size="sm">
    <template #page>
      <div class="q-py-md q-px-lg">
        <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
          <q-input v-model.trim="formData.name" :label="`${$t('fields.name')} *`" dense class="col-12" />
          <q-input
            v-model.trim="formData.website"
            :label="`${$t('fields.website')} *`"
            type="url"
            dense
            class="col-12 col-sm-9"
          />
          <q-select
            v-model="formData.level"
            :label="$t('fields.type')"
            :options="sponsorTypeOptions"
            :disable="!sponsorTypeOptions.length"
            :hint="!sponsorTypeOptions.length ? 'Configure sponsor tiers in Django admin first.' : undefined"
            emit-value
            map-options
            dense
            options-dense
            class="col-12 col-sm-3"
          />
          <template v-if="currentSponsor">
            <q-item-label class="col-12 text-caption text-grey-7">Logo</q-item-label>
            <div class="col-12">
              <file-field
                public
                :api-endpoint="currentSponsor.rel_files"
                :tags="['logo']"
                :label="'Logo'"
                accept="image/*"
              />
            </div>
          </template>
          <div v-else class="col-12 text-caption text-grey-6">Save the sponsor first to upload a logo.</div>
        </div>
      </div>
    </template>
    <template #footer>
      <div class="flex q-gutter-sm q-pa-lg">
        <q-space />
        <update-btn
          @click="createUpdate"
          :disabled="!formData.name || !formData.website"
          :loading="loading"
          :is-create="!props.obj"
        />
      </div>
    </template>
  </dialog-form>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { storeToRefs } from 'pinia';

import { useStore } from '../../store';
import { useMinimumLoading } from '@/composables/useMinimumLoading';

import UpdateBtn from '@/components/buttons/UpdateBtn.vue';
import DialogForm from '@/components/forms/DialogForm.vue';
import FileField from '@/components/rel/FileField.vue';

import { iconSponsor } from '@/icons';

const props = defineProps<{
  obj?: Sponsor;
}>();

const store = useStore();
const { loading, executeWithMinLoading } = useMinimumLoading();
const { sponsorTypeOptions } = storeToRefs(store);

const currentSponsor = ref<Sponsor | undefined>(props.obj);

const formData = ref<SponsorData>({
  name: props.obj?.name || '',
  website: props.obj?.website || '',
  level: props.obj?.level ?? 0,
});

async function createUpdate() {
  executeWithMinLoading(async () => {
    if (props.obj) {
      await store.updateSponsor({ ...props.obj, ...formData.value });
    } else {
      const res = await store.createSponsor(formData.value);
      currentSponsor.value = res?.data;
    }
  });
}
</script>
