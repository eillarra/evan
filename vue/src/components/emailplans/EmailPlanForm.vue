<template>
  <dialog-form :icon="currentObj ? iconEmail : iconAdd" :title="$t('models.email_plan')">
    <template #page>
      <div class="q-pb-lg q-px-lg">
        <q-banner v-if="isSent" class="bg-orange-2 text-orange-9 q-mb-md rounded-borders" rounded dense>
          {{ $t('email_plan.sent_readonly_banner') }}
        </q-banner>

        <q-input
          v-model.trim="formData.name"
          :label="`${$t('email_plan.name')} *`"
          :disable="isSent"
          dense
          class="q-mb-sm"
        />

        <q-input
          v-model.trim="formData.subject"
          :label="`${$t('email_plan.subject')} *`"
          :disable="isSent"
          dense
          class="q-mb-sm"
        />

        <div class="row q-col-gutter-x-md q-mb-lg">
          <q-input
            v-model.trim="formData.from_email"
            :label="$t('email_plan.from_email')"
            :hint="$t('email_plan.from_email_hint')"
            :disable="isSent"
            :rules="[validateUgentEmail]"
            dense
            class="col-12 col-md-6"
          />
          <div class="col-12 col-md-6">
            <date-select
              v-model="formData.send_at"
              type="datetime"
              :label="$t('email_plan.send_at')"
              :disable="isSent"
              dense
            >
            </date-select>
            <div v-if="!formData.send_at" class="text-caption text-grey-7 q-mt-xs">
              <q-badge color="grey-6" :label="$t('email_plan.status_draft')" class="q-mr-xs" />
              {{ $t('email_plan.send_at_hint') }}
            </div>
          </div>
        </div>

        <q-expansion-item
          v-model="filtersExpanded"
          dense
          dense-toggle
          :label="recipientCountLabel"
          header-class="q-pa-none"
        >
          <div class="q-pa-sm">
            <div class="text-caption text-grey-7 q-mb-xs">{{ $t('email_plan.filters.fee_types') }}</div>
            <chip-select
              v-model="formData.filters.fee_types"
              :options="feeOptions"
              add-all
              :all-label="$t('email_plan.filters.all')"
              :disable="isSent"
              multiple
              class="q-mb-sm"
            />

            <div class="text-caption text-grey-7 q-mb-xs q-mt-sm">{{ $t('email_plan.filters.payment_status') }}</div>
            <chip-select
              v-model="formData.filters.payment_status"
              :options="paymentStatusChips"
              :disable="isSent"
              :multiple="false"
              class="q-mb-sm"
            />

            <template v-if="socialEventOptions.length > 0">
              <div class="text-caption text-grey-7 q-mb-xs q-mt-sm">{{ $t('email_plan.filters.social_events') }}</div>
              <chip-select
                v-model="socialEventFilter"
                :options="socialEventOptions"
                add-all
                :all-label="$t('email_plan.filters.all')"
                :disable="isSent"
                :multiple="false"
              />
            </template>
          </div>
        </q-expansion-item>

        <q-separator class="q-mb-lg" />

        <marked-textarea v-model="formData.body" :label="$t('email_plan.body')" />
        <div class="row q-gutter-xs q-mt-lg">
          <q-chip
            v-for="tag in templateTags"
            :key="tag"
            clickable
            dense
            square
            color="grey-2"
            text-color="dark"
            @click="insertTag(tag)"
          >
            {{ tag }}
          </q-chip>
        </div>
      </div>
    </template>

    <template #footer>
      <div class="flex items-center q-gutter-sm q-pa-lg">
        <template v-if="currentObj">
          <q-btn
            outline
            square
            :icon="iconEye"
            :label="$t('email_plan.preview')"
            :loading="previewLoading"
            color="ugent"
            @click="onPreview"
          />
          <q-btn
            v-if="!isSent"
            outline
            square
            :icon="iconSend"
            :label="$t('email_plan.demo')"
            :loading="demoLoading"
            color="ugent"
            @click="onDemo"
          />
          <q-btn
            v-if="isSent"
            outline
            square
            :icon="iconLogs"
            :label="$t('email_plan.logs')"
            color="ugent"
            @click="onLogs"
          />
          <q-btn
            outline
            square
            :icon="iconDuplicate"
            :label="$t('email_plan.duplicate')"
            :loading="duplicateLoading"
            color="ugent"
            @click="onDuplicate"
          />
        </template>
        <q-space />
        <update-btn
          v-if="!isSent"
          @click="createUpdate"
          :disabled="!formData.name || !formData.subject"
          :loading="loading"
          :label="currentObj ? $t('form.update') : $t('form.create')"
        />
      </div>
    </template>
  </dialog-form>

  <!-- Logs dialog -->
  <q-dialog v-model="logsDialogVisible">
    <q-card style="width: 900px; max-width: 95vw">
      <q-card-section class="row items-center q-pb-sm">
        <div class="text-h6">{{ $t('email_plan.logs') }}</div>
        <q-space />
        <q-btn flat round dense v-close-popup :icon="iconClose" />
      </q-card-section>
      <q-separator />
      <q-card-section class="scroll" style="max-height: 70vh">
        <email-plan-logs v-if="currentObj" :plan-id="currentObj.id" />
      </q-card-section>
    </q-card>
  </q-dialog>

  <q-dialog v-model="previewDialogVisible">
    <q-card style="width: 700px; max-width: 90vw">
      <q-card-section class="row items-center q-pb-sm">
        <div class="text-h6">{{ preview?.subject }}</div>
        <q-space />
        <q-btn flat round dense v-close-popup :icon="iconClose" />
      </q-card-section>
      <q-separator />
      <q-card-section class="scroll" style="max-height: 60vh">
        <marked-div v-if="preview" :text="preview.body" />
      </q-card-section>
    </q-card>
  </q-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { copyToClipboard } from 'quasar';
import { debounce } from 'lodash-es';

import { useStore } from '@/apps/event/store';
import { useMinimumLoading } from '@/composables/useMinimumLoading';
import { confirm } from '@/utils/dialog';
import { notify } from '@/utils/notify';

import UpdateBtn from '@/components/buttons/UpdateBtn.vue';
import MarkedDiv from '@/components/MarkedDiv.vue';
import DialogForm from '@/components/forms/DialogForm.vue';
import MarkedTextarea from '@/components/forms/MarkedTextarea.vue';
import DateSelect from '@/components/forms/DateSelect.vue';
import ChipSelect from '@/components/forms/ChipSelect.vue';
import EmailPlanLogs from '@/components/emailplans/EmailPlanLogs.vue';

import { iconAdd, iconClose, iconDuplicate, iconEmail, iconEye, iconLogs, iconSend } from '@/icons';

const { t } = useI18n();

defineEmits(['create:obj', 'update:obj']);

const props = defineProps<{
  obj?: EmailPlan;
  parent?: unknown;
}>();

const store = useStore();
const { loading, executeWithMinLoading } = useMinimumLoading();

// Holds the plan being edited: either the passed prop or a just-created plan.
// After create, this is set to the API response so the footer actions appear immediately.
const currentObj = ref<EmailPlan | null>(props.obj ?? null);

const isSent = computed(() => !!currentObj.value?.sent_at);

const fees = computed(() => store.evanEvent?.fees ?? []);

const feeOptions = computed(() => {
  const usedFeeTypes = new Set(store.registrations.map((r) => r.fee_type));
  return fees.value.filter((fee) => usedFeeTypes.has(fee.type)).map((fee) => ({ label: fee.type, value: fee.type }));
});

const socialEventOptions = computed(() =>
  store.sessions.filter((s) => s.is_social_event).map((s) => ({ label: s.title, value: s.id })),
);

// Single-value bridge for the social-events chip-select (non-multiple).
// ChipSelect expects a single value; backend sessions.ids expects an array.
const socialEventFilter = computed({
  get: () => formData.value.filters.sessions.ids[0] ?? null,
  set: (val: unknown) => {
    formData.value.filters.sessions.ids = val ? [val] : [];
  },
});

const paymentStatusChips: QuasarSelectOption[] = [
  { label: t('email_plan.filters.payment_all'), value: null },
  { label: t('email_plan.filters.payment_paid'), value: 'paid' },
  { label: t('email_plan.filters.payment_unpaid'), value: 'unpaid' },
];

// Accordion for the filters section, collapsed by default.
const filtersExpanded = ref(false);

// Recipient count state (debounced fetch on filter change).
const recipientCount = ref<number | null>(null);
const countLoading = ref(false);

// Recipient count label for the accordion header.
const recipientCountLabel = computed(() => {
  if (countLoading.value) return t('email_plan.recipients_count_loading');
  if (recipientCount.value === 0) return t('email_plan.recipients_match_none');
  return t('email_plan.recipients_match', { count: recipientCount.value });
});

const templateTags = [
  '{{ user.first_name }}',
  '{{ user.last_name }}',
  '{{ user.email }}',
  '{{ event.name }}',
  '{{ session.title }}',
];

const emptyFilters = (): EmailPlanFilters => ({
  fee_types: [],
  sessions: { ids: [], match: 'any' },
  session_days: [],
  payment_status: null,
});

const formData = ref({
  name: props.obj?.name || '',
  subject: props.obj?.subject || '',
  body: props.obj?.body || '',
  from_email: props.obj?.from_email || `${store.evanEvent?.name || 'UGent'} <evan@ugent.be>`,
  bcc_email: props.obj?.bcc_email || '',
  reply_to_email: props.obj?.reply_to_email || '',
  filters: props.obj?.filters ? { ...props.obj.filters } : emptyFilters(),
  send_at: props.obj?.send_at || null,
});

async function createUpdate() {
  if (!formData.value.name || !formData.value.subject) return;

  // send_at, when set, must be at least 5 minutes in the future.
  if (formData.value.send_at && !validateSendAt(formData.value.send_at)) {
    notify.error(t('email_plan.send_at_too_soon'));
    return;
  }

  await executeWithMinLoading(async () => {
    if (currentObj.value) {
      const res = await store.updateEmailPlan({ ...currentObj.value, ...formData.value });
      currentObj.value = res.data;
    } else {
      const res = await store.createEmailPlan(formData.value);
      currentObj.value = res.data;
    }
  });
}

function validateSendAt(sendAt: string): boolean {
  const min = new Date(Date.now() + 5 * 60 * 1000);
  return new Date(sendAt) >= min;
}

function validateUgentEmail(value: string): true | string {
  if (!value) return true;
  // Accept both "x@ugent.be" and "Display Name <x@ugent.be>".
  const match = value.match(/<([^>]+)>/);
  const email = match ? match[1].trim() : value.trim();
  return email.endsWith('@ugent.be') || t('email_plan.from_email_invalid');
}

function insertTag(tag: string) {
  copyToClipboard(tag)
    .then(() => {
      notify.info(t('messages.copied_to_clipboard'));
    })
    .catch(() => {
      // Fallback for non-secure contexts (http without localhost).
      const textarea = document.createElement('textarea');
      textarea.value = tag;
      textarea.style.position = 'fixed';
      textarea.style.opacity = '0';
      document.body.appendChild(textarea);
      textarea.select();
      try {
        document.execCommand('copy');
        notify.info(t('messages.copied_to_clipboard'));
      } catch {
        notify.error('Clipboard not available');
      }
      document.body.removeChild(textarea);
    });
}

async function refreshCount() {
  if (isSent.value) return;
  countLoading.value = true;
  try {
    recipientCount.value = await store.fetchRecipientCount(formData.value.filters);
  } catch {
    recipientCount.value = null;
  } finally {
    countLoading.value = false;
  }
}

const debouncedRefreshCount = debounce(refreshCount, 400);

watch(
  () => ({ ...formData.value.filters }),
  () => {
    if (isSent.value) return;
    debouncedRefreshCount();
  },
  { deep: true, immediate: true },
);

const preview = ref<{ subject: string; body: string } | null>(null);
const previewLoading = ref(false);
const previewDialogVisible = ref(false);

async function onPreview() {
  if (!currentObj.value) return;
  previewLoading.value = true;
  try {
    preview.value = await store.previewEmailPlan(currentObj.value);
    previewDialogVisible.value = true;
  } catch {
    preview.value = null;
  } finally {
    previewLoading.value = false;
  }
}

const demoLoading = ref(false);

async function onDemo() {
  if (!currentObj.value) return;
  demoLoading.value = true;
  try {
    await store.demoEmailPlan(currentObj.value);
  } finally {
    demoLoading.value = false;
  }
}

const duplicateLoading = ref(false);

function onDuplicate() {
  if (!currentObj.value) return;
  confirm(t('messages.email_plan_confirm_duplicate'), async () => {
    duplicateLoading.value = true;
    try {
      await store.duplicateEmailPlan(currentObj.value);
    } finally {
      duplicateLoading.value = false;
    }
  });
}

const logsDialogVisible = ref(false);

function onLogs() {
  logsDialogVisible.value = true;
}
</script>
