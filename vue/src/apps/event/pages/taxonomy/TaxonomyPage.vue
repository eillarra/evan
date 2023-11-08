<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.tracks_topics') }}
    </h3>
  </div>
  <div v-if="evanEvent" class="row q-col-gutter-xl">
    <div class="col-12 col-md-6 ugent__create-btn">
      <div class="ugent__create-btn">
        <q-btn
          unelevated
          color="blue-1"
          :label="$t('form.new')"
          :icon="iconAdd"
          class="text-ugent float-right"
          @click="() => openForm(TrackForm)"
        />
        <h4 class="q-mt-none q-mb-md">{{ $t('models.track', 9) }}</h4>
      </div>
      <tracks-table :tracks="evanEvent.tracks" />
    </div>
    <div class="col-12 col-md-6">
      <div class="ugent__create-btn">
        <q-btn
          unelevated
          color="blue-1"
          :label="$t('form.new')"
          :icon="iconAdd"
          class="text-ugent float-right"
          @click="() => openForm(TopicForm)"
        />
        <h4 class="q-mt-none q-mb-md">{{ $t('models.topic', 9) }}</h4>
      </div>
      <topics-table :topics="evanEvent.topics" />
    </div>
  </div>
  <q-dialog v-if="formComponent" v-model="createDialogVisible">
    <component :is="formComponent" @create:obj="() => (createDialogVisible = false)" />
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, ComponentOptions } from 'vue';
import { storeToRefs } from 'pinia';

import { useStore } from '../../store';

import TopicForm from './TopicForm.vue';
import TopicsTable from './TopicsTable.vue';
import TrackForm from './TrackForm.vue';
import TracksTable from './TracksTable.vue';

import { iconAdd } from '@/icons';

const { evanEvent } = storeToRefs(useStore());

const createDialogVisible = ref(false);
const formComponent = ref<ComponentOptions | undefined>(undefined);

function openForm(component: ComponentOptions) {
  formComponent.value = component;
  createDialogVisible.value = true;
}
</script>
