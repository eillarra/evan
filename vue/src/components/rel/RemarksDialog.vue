<template>
  <div>
    <q-icon @click="dialogVisible = true" :name="icon" :color="iconColor || 'dark'" class="cursor-pointer" />
    <q-dialog v-model="dialogVisible">
      <dialog-form :title="title || $t('remark', 9)" :icon="icon">
        <template #page>
          <div class="q-py-sm q-px-lg">
            <remarks-view :api-endpoint="apiEndpoint" :visibility-options="visibilityOptions" hide-title />
          </div>
        </template>
      </dialog-form>
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import DialogForm from '@/components/forms/DialogForm.vue';
import RemarksView from './RemarksView.vue';

defineProps<{
  apiEndpoint: ApiEndpoint;
  icon: string;
  iconColor?: string;
  title?: string;
  visibilityOptions?: string[];
}>();

const dialogVisible = ref<boolean>(false);
</script>
