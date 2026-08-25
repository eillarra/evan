<template>
  <data-table
    :columns="columns"
    :rows="rows"
    :query-columns="queryColumns"
    :form-component="EmailPlanForm"
    :create-form-component="EmailPlanForm"
    sort-by="-updated_at"
    removable
    @remove:row="removePlan"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

import { useStore } from '@/apps/event/store';

import DataTable from '@/components/tables/DataTable.vue';
import EmailPlanForm from '@/components/emailplans/EmailPlanForm.vue';

const props = defineProps<{
  plans: EmailPlan[];
}>();

const store = useStore();
const { t } = useI18n();

const queryColumns = ['name', 'subject', 'status'];

const columns = [
  {
    name: 'name',
    field: 'name',
    required: true,
    label: t('email_plan.name'),
    align: 'left',
    sortable: true,
    sort: (a: string, b: string) => a.localeCompare(b),
    headerClasses: 'sticky-left',
    classes: 'sticky-left',
  },
  {
    name: 'subject',
    field: 'subject',
    label: t('email_plan.subject'),
    align: 'left',
    sortable: true,
    sort: (a: string, b: string) => a.localeCompare(b),
  },
  {
    name: 'recipients_count',
    field: 'recipients_count',
    label: t('email_plan.recipients_count'),
    align: 'right',
    sortable: true,
  },
  {
    name: 'send_at',
    field: 'send_at',
    label: t('email_plan.send_at'),
    align: 'left',
    sortable: true,
  },
  {
    name: 'sent_at',
    field: 'sent_at',
    label: t('email_plan.sent_at'),
    align: 'left',
    sortable: true,
  },
  {
    name: 'status',
    field: 'status',
    label: t('email_plan.status'),
    align: 'left',
    sortable: true,
  },
];

const rows = computed(() =>
  props.plans.map((plan: EmailPlan) => ({
    _self: plan,
    name: plan.name,
    subject: plan.subject,
    recipients_count: plan.recipients_count,
    send_at: plan.send_at || '—',
    sent_at: plan.sent_at || '—',
    status: statusLabel(plan),
  })),
);

function statusLabel(plan: EmailPlan): string {
  if (plan.sent_at) return t('email_plan.status_sent');
  if (!plan.send_at) return t('email_plan.status_draft');
  return t('email_plan.status_scheduled');
}

function removePlan(row: { _self: EmailPlan }) {
  store.removeEmailPlan(row._self);
}
</script>
