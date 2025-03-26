<template>
  <data-table
    :columns="columns"
    :rows="rows"
    :query-columns="queryColumns"
    sort-by="-sent_at"
    :form-component="EmailDialog"
    open-dialog
    :in-dialog="inDialog"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import { formatDate } from '@/utils/dates';

import DataTable from '@/components/tables/DataTable.vue';
import EmailDialog from './EmailDialog.vue';

const { t } = useI18n();

const props = defineProps<{
  emails: Email[];
  tags?: string[];
  inDialog?: boolean;
}>();

const queryColumns = ['sent_to', 'subject', 'type'];

const columns = [
  {
    name: 'sent_at',
    field: 'sent_at',
    required: true,
    label: t('fields.sent_at'),
    align: 'left',
    sortable: true,
    autoWidth: true,
  },
  {
    name: 'subject',
    field: 'subject',
    required: true,
    label: t('fields.subject'),
    align: 'left',
  },
  {
    name: 'email',
    field: 'email',
    label: t('fields.sent_to'),
    align: 'left',
  },
  {
    name: 'type_badge',
    field: 'type',
    label: t('fields.type'),
    align: 'left',
    autoWidth: true,
  },
];

const rows = computed(() => {
  return props.emails
    .filter((email: Email) => {
      return (props.tags || []).every((tag: string) => {
        return email.tags?.includes(tag);
      });
    })
    .map((email: Email) => {
      return {
        _self: email,
        sent_at: formatDate(email.sent_at),
        email: email.to.join(', '),
        subject: email.subject,
        // if a tag starting with `type:xxx` is present, use `xxx` as the type
        type: (email.tags || []).find((tag: string) => tag.startsWith('type:'))?.split(':')[1] ?? null,
      };
    });
});
</script>
