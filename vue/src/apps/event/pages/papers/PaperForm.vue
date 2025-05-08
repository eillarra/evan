<template>
  <dialog-form :icon="iconPaper" :title="$t('models.paper')">
    <template #page>
      <div class="q-py-md q-px-lg">
        <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
          <readonly-field
            v-if="obj && obj.secret_url"
            :value="`https://evan.ugent.be${obj.secret_url}`"
            :label="$t('fields.secret_url')"
            class="col-12"
            with-copy
          />
          <q-input dense v-model="formData.title" :label="`${$t('fields.title')} *`" class="col-12" />
          <evan-select
            v-model="formData.track"
            :label="$t('models.track')"
            :options="trackOptions"
            class="col-12 col-md-3"
          />
          <evan-select
            v-model="formData.topics"
            :label="$t('models.topic', 9)"
            :options="topicOptions"
            multiple
            class="col-12 col-md-9"
          />
          <marked-textarea v-model="formData.abstract" :label="$t('fields.abstract')" class="col-12" />
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
          :disable="!formData.title"
        />
      </div>
    </template>
  </dialog-form>
</template>

<script setup lang="ts">
import { ref } from 'vue';
import { storeToRefs } from 'pinia';

import { useStore } from '../../store';

import DialogForm from '@/components/forms/DialogForm.vue';
import MarkedTextarea from '@/components/forms/MarkedTextarea.vue';
import ReadonlyField from '@/components/forms/ReadonlyField.vue';

import { iconPaper } from '@/icons';

const props = defineProps<{
  obj?: Paper;
}>();

const store = useStore();

const { topicOptions, trackOptions } = storeToRefs(store);

const obj = ref<Paper | undefined>(props.obj);
const formData = ref<PaperData>({
  title: props.obj?.title || '',
  abstract: props.obj?.abstract || '',
  track: props.obj?.track || null,
  topics: props.obj?.topics || [],
});

function createUpdate() {
  if (!formData.value.title) return;

  if (props.obj) store.updatePaper({ ...props.obj, ...formData.value });
  else {
    store.createPaper(formData.value).then((res) => {
      if (res && res.data) {
        obj.value = res.data as Paper;
      }
    });
  }
}
</script>
