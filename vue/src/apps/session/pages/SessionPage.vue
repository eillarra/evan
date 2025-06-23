<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.session') }}
    </h3>
  </div>
  <div v-if="evanEvent && session">
    <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
      <readonly-field
        :value="`${evanEvent.website}program/${session.slug}/`"
        :label="$t('fields.public_url')"
        class="col-12"
        with-copy
      />
      <readonly-field :value="session.code || '-'" :label="$t('fields.code')" class="col-12 col-md-4" />
      <readonly-field :value="session.start_at || '-'" :label="$t('fields.start')" class="col-12 col-md-4" />
      <readonly-field :value="session.end_at || '-'" :label="$t('fields.end')" class="col-12 col-md-4" />
      <readonly-field :value="trackName" :label="$t('models.track')" class="col-12 col-md-4" />
      <evan-select
        v-model="session.topics"
        :label="$t('models.topic', 9)"
        :options="topicOptions"
        multiple
        class="col-12 col-md-8"
      />
      <q-input
        v-model="session.title"
        :label="$t('fields.title')"
        dense
        class="col-12"
        :rules="[(val: string) => !!val || $t('validation.required')]"
      />
      <marked-textarea v-model="session.description" :label="$t('fields.description')" class="col-12" />
    </div>
    <div v-if="session" class="flex q-gutter-sm q-mt-md">
      <update-btn @click="update" :disabled="!session.title" :loading="loading" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia';

import { useStore } from '../store';
import { useMinimumLoading } from '@/composables/useMinimumLoading';

import UpdateBtn from '@/components/buttons/UpdateBtn.vue';
import MarkedTextarea from '@/components/forms/MarkedTextarea.vue';
import ReadonlyField from '@/components/forms/ReadonlyField.vue';

const store = useStore();
const { loading, executeWithMinLoading } = useMinimumLoading();

const { evanEvent, session, topicOptions, trackName } = storeToRefs(store);

async function update() {
  await executeWithMinLoading(async () => {
    await store.updateSession();
  });
}
</script>
