<template>
  <q-icon @click.prevent="copyText(text)" :name="iconCopy" :size="iconSize || '16px'" class="cursor-pointer q-ml-xs" />
</template>

<script setup lang="ts">
import { useI18n } from 'vue-i18n';
import { copyToClipboard } from 'quasar';

import { notify } from '@/utils/notify';

import { iconCopy } from '@/icons';

const { t } = useI18n();

defineProps<{
  text: string;
  iconSize?: string;
}>();

function copyText(text: string) {
  copyToClipboard(text).then(() => {
    notify.info(t('messages.copied_to_clipboard'));
  });
}
</script>
