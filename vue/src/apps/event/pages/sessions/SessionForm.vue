<template>
  <dialog-form :icon="iconSession" :title="$t('models.session')">
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
          <q-input dense v-model="formData.code" :label="`${$t('fields.code')} *`" class="col-12 col-md-3" />
          <q-input dense v-model="formData.title" :label="`${$t('fields.title')} *`" class="col-12 col-md-9" />
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
          <date-select
            v-model="formData.start_at"
            type="datetime"
            :label="$t('fields.start')"
            class="col-12 col-md-3"
          />
          <date-select v-model="formData.end_at" type="datetime" :label="$t('fields.end')" class="col-12 col-md-3" />
          <marked-textarea v-model="formData.description" :label="$t('fields.description')" class="col-12" />
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

import DateSelect from '@/components/forms/DateSelect.vue';
import DialogForm from '@/components/forms/DialogForm.vue';
import MarkedTextarea from '@/components/forms/MarkedTextarea.vue';
import ReadonlyField from '@/components/forms/ReadonlyField.vue';

import { iconSession } from '@/icons';

const props = defineProps<{
  obj?: Session;
}>();

const store = useStore();

const { topicOptions, trackOptions } = storeToRefs(store);

const obj = ref<Session | undefined>(props.obj);
const formData = ref<SessionData>({
  code: props.obj?.code || '',
  title: props.obj?.title || '',
  description: props.obj?.description || '',
  start_at: props.obj?.start_at || null,
  end_at: props.obj?.end_at || null,
  track: props.obj?.track || null,
  topics: props.obj?.topics || [],
});

function createUpdate() {
  if (!formData.value.code || !formData.value.title) return;

  if (props.obj) store.updateSession({ ...props.obj, ...formData.value });
  else {
    store.createSession(formData.value).then((res) => {
      if (res && res.data) {
        obj.value = res.data as Session;
      }
    });
  }
}
</script>
