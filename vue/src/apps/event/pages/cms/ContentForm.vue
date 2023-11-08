<template>
  <dialog-form :icon="iconContent" :title="$t('models.content')">
    <template #page>
      <div class="q-py-md q-px-lg">
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
    </template>
    <template #footer>
      <div class="flex q-gutter-sm q-pa-lg">
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
import { useI18n } from 'vue-i18n';

import { api } from '@/axios';
import { notify } from '@/utils/notify';

import { useStore } from '../../store.js';

import DialogForm from '@/components/forms/DialogForm.vue';
import MarkedTextarea from '@/components/forms/MarkedTextarea.vue';
import ReadonlyField from '@/components/forms/ReadonlyField.vue';

import { iconContent } from '@/icons';

const emit = defineEmits(['create:obj']);

const props = defineProps<{
  obj: Content;
}>();

const { t } = useI18n();
const store = useStore();

const formData = ref({
  content: props.obj.value,
});

function update() {
  if (!formData.value.content) return;

  const data = {
    key: props.obj.key,
    value: formData.value.content,
  };

  api.put(props.obj.self, data).then((res) => {
    //store.updateObj('content', res.data);
    notify.success(t('form.contact.create.success'));
    emit('create:obj');
  });
}
</script>
