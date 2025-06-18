<template>
  <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
    <div class="col-12 col-md-3">
      <date-select
        v-model="mutableSubsession.start_at"
        type="datetime"
        :label="$t('fields.start')"
        :min-date="sessionStartDate"
        :max-date="sessionEndDate"
      />
      <div v-if="startTimeError" class="text-negative text-caption q-mt-xs">
        {{ startTimeError }}
      </div>
    </div>
    <div class="col-12 col-md-3">
      <date-select
        v-model="mutableSubsession.end_at"
        type="datetime"
        :label="$t('fields.end')"
        :min-date="sessionStartDate"
        :max-date="sessionEndDate"
      />
      <div v-if="endTimeError" class="text-negative text-caption q-mt-xs">
        {{ endTimeError }}
      </div>
    </div>
    <div class="col-12 col-md text-right use-default-q-btn">
      <q-btn
        outline
        square
        @click="saveChanges"
        color="primary"
        :label="$t('form.save')"
        :loading="saving"
        :disable="hasValidationErrors"
        class="q-mr-sm"
      />
      <q-btn outline square @click="remove" color="negative" :label="$t('form.delete')" />
    </div>
    <div class="col-12 col-md-12">
      <q-input dense v-model="mutableSubsession.title" :label="$t('subsession.title')" />
    </div>
    <div class="col-12">
      <program-template-editor
        :model-value="mutableSubsession.program || ''"
        @update:model-value="(value) => (mutableSubsession.program = value)"
        :label="$t('fields.program')"
        :papers="papers"
        :validation="undefined"
        :event-id="eventId"
        :item-id="subsession.id"
        :current-session="session"
        :current-subsession="mutableSubsession"
        item-type="subsession"
        @unlink-paper="unlinkPaperFromSubsession"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, computed } from 'vue';
import { storeToRefs } from 'pinia';
import { useI18n } from 'vue-i18n';

import { useStore } from '../../store';

import DateSelect from '@/components/forms/DateSelect.vue';
import ProgramTemplateEditor from '@/components/forms/ProgramTemplateEditor.vue';

const props = defineProps<{
  subsession: Subsession;
  eventId: number;
  session?: Session;
}>();

const emit = defineEmits<{
  remove: [subsession: Subsession];
}>();

const store = useStore();
const { papers } = storeToRefs(store);
const { t } = useI18n();

const saving = ref(false);

// Create a mutable copy for editing to avoid mutating props directly
const mutableSubsession = ref<Subsession>({ ...props.subsession });

// Compute session datetime bounds for validation
const sessionStartDate = computed(() => props.session?.start_at || undefined);
const sessionEndDate = computed(() => props.session?.end_at || undefined);

// Validation helpers
const isValidSubsessionTime = (time: string | null | undefined): boolean => {
  if (!time || !props.session) return true;

  const sessionStart = props.session.start_at;
  const sessionEnd = props.session.end_at;

  if (sessionStart && time < sessionStart) return false;
  if (sessionEnd && time > sessionEnd) return false;

  return true;
};

const startTimeError = computed(() => {
  if (!mutableSubsession.value.start_at || !props.session?.start_at || !props.session?.end_at) return '';
  if (!isValidSubsessionTime(mutableSubsession.value.start_at)) {
    return t('subsession.validation.start_time_range', {
      start: new Date(props.session.start_at).toLocaleString(),
      end: new Date(props.session.end_at).toLocaleString(),
    });
  }
  return '';
});

const endTimeError = computed(() => {
  if (!mutableSubsession.value.end_at || !props.session?.start_at || !props.session?.end_at) return '';
  if (!isValidSubsessionTime(mutableSubsession.value.end_at)) {
    return t('subsession.validation.end_time_range', {
      start: new Date(props.session.start_at).toLocaleString(),
      end: new Date(props.session.end_at).toLocaleString(),
    });
  }
  return '';
});

const hasValidationErrors = computed(() => {
  return startTimeError.value !== '' || endTimeError.value !== '';
});

// Watch for changes to the prop and update mutable copy
watch(
  () => props.subsession,
  (newSubsession) => {
    mutableSubsession.value = { ...newSubsession };
  },
  { immediate: true, deep: true },
);

async function saveChanges() {
  if (saving.value || hasValidationErrors.value) return;

  saving.value = true;
  try {
    await store.updateSubsession(mutableSubsession.value);
  } finally {
    saving.value = false;
  }
}

function remove() {
  emit('remove', props.subsession);
}

function unlinkPaperFromSubsession(paper: Paper) {
  // TODO: Add API call to unlink paper from subsession
  console.log('Unlinking paper from subsession:', paper.title);
  // For now, just refresh the papers list
  store.fetchPapers();
}
</script>
