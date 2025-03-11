<template>
  <dialog-form :icon="iconContent" :title="$t('models.content')">
    <template #tabs>
      <q-tabs v-model="tab" no-caps>
        <q-tab name="content" :label="$t('models.content')" />
        <q-tab name="files" :label="$t('models.file', 9)" />
      </q-tabs>
    </template>
    <template #page>
      <q-tab-panels v-model="tab">
        <q-tab-panel name="content">
          <div class="q-pa-sm">
            <div class="row q-col-gutter-y-sm">
              <readonly-field :value="obj.key" :label="$t('fields.code')" class="col-12" />
              <marked-textarea
                v-if="obj.config.markdown"
                v-model="formData.content"
                :label="$t('models.content')"
                class="col-12"
              />
              <q-input v-else v-model="formData.content" :label="$t('models.content')" autogrow class="col-12" />
            </div>
          </div>
        </q-tab-panel>
        <q-tab-panel name="files">
          <files-view :api-endpoint="obj.rel_files" />
        </q-tab-panel>
      </q-tab-panels>
    </template>
    <template #footer>
      <div v-if="tab == 'content'" class="flex q-gutter-sm q-pa-lg">
        <q-space />
        <q-btn
          v-close-popup
          unelevated
          @click="update"
          color="ugent"
          :label="$t('form.update')"
          :disable="!formData.content"
        />
      </div>
    </template>
  </dialog-form>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import { useStore } from '../../store';

import DialogForm from '@/components/forms/DialogForm.vue';
import MarkedTextarea from '@/components/forms/MarkedTextarea.vue';
import ReadonlyField from '@/components/forms/ReadonlyField.vue';
import FilesView from '@/components/rel/FilesView.vue';

import { iconContent } from '@/icons';

const props = defineProps<{
  obj: Content;
}>();

const store = useStore();

const formData = ref({
  content: props.obj.value,
});

const tab = ref('content');

function update() {
  if (!formData.value.content) return;

  const data: Partial<Content> = {
    value: formData.value.content,
  };

  store.updateContent(props.obj, data);
}
</script>
