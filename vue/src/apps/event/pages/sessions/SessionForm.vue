<template>
  <dialog-form :icon="iconSession" :title="$t('models.session')">
    <template #tabs>
      <q-tabs v-model="activeTab" dense narrow-indicator no-caps align="left">
        <q-tab name="general" :label="$t('tabs.general')" />
        <q-tab name="description" :label="$t('fields.description')" />
        <q-tab name="program" :label="$t('fields.program')" />
        <q-tab
          v-for="(subsession, index) in sortedSubsessions"
          :key="`tab-${subsession.id}`"
          :name="`subsession-${subsession.id}`"
          :label="`${session?.code || $t('models.subsession').toLocaleUpperCase()} ${toRomanNumeral(index + 1)}`"
        />
      </q-tabs>
    </template>
    <template #page>
      <div class="q-pb-lg q-px-sm">
        <q-tab-panels v-model="activeTab">
          <q-tab-panel name="general">
            <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
              <readonly-field
                v-if="session && session.secret_url"
                :value="`https://evan.ugent.be${session.secret_url}`"
                :label="$t('fields.secret_url')"
                class="col-12"
                with-copy
              />
              <q-input
                dense
                v-model.trim="formData.code"
                :label="$t('fields.code')"
                :readonly="!!props.obj && !!props.obj.code"
                class="col-12 col-md-3"
              />
              <evan-select
                v-model="formData.track"
                :label="$t('models.track')"
                :options="trackOptions"
                class="col-12 col-md-9"
              />
              <q-input dense v-model.trim="formData.title" :label="`${$t('fields.title')} *`" class="col-12" />
              <evan-select
                v-model="formData.topics"
                :label="$t('models.topic', 9)"
                :options="topicOptions"
                multiple
                class="col-12"
              />
              <date-select
                v-model="formData.start_at"
                type="datetime"
                :label="$t('fields.start')"
                class="col-12 col-md-3"
              />
              <date-select
                v-model="formData.end_at"
                type="datetime"
                :label="$t('fields.end')"
                class="col-12 col-md-3"
              />
              <evan-select
                v-model="formData.room"
                :label="$t('models.room')"
                :options="roomOptions"
                clearable
                class="col-12 col-md-6"
              />
              <q-checkbox
                v-model="formData.is_social_event"
                :label="$t('event.is_social_event')"
                class="col-12"
                disable
              />
              <q-input
                v-if="formData.is_social_event"
                v-model.number="formData.extra_attendees_fee"
                type="number"
                :label="$t('fields.extra_attendees_fee')"
                min="0"
                dense
                readonly
                class="col-12 col-md-3"
              />
              <evan-select
                v-if="formData.is_social_event"
                v-model="badgeIcon"
                :label="$t('fields.badge_icon')"
                :options="badgeIconOptions"
                class="col-12 col-md-9"
              />
            </div>
          </q-tab-panel>
          <q-tab-panel name="description">
            <marked-textarea v-model="formData.description" :label="$t('fields.description')" />
          </q-tab-panel>
          <q-tab-panel name="program">
            <div class="row q-col-gutter-y-sm">
              <div v-if="hasSubsessions" class="col-12">
                <warning-banner type="warning" class="q-mb-sm">
                  {{ $t('session.program_with_subsessions_note') }}
                </warning-banner>
              </div>
              <div class="col-12">
                <program-template-editor
                  v-model="sessionProgram"
                  :label="$t('fields.program')"
                  :papers="papers"
                  :keynotes="store.keynotes"
                  :rendered-program="renderedProgram"
                  :validation="programValidation || undefined"
                  :current-session="session"
                  @template-changed="onProgramChanged"
                  @unlink-paper="unlinkPaperFromSession"
                />
              </div>
            </div>
          </q-tab-panel>
          <q-tab-panel
            v-for="subsession in sortedSubsessions"
            :key="`panel-${subsession.id}`"
            :name="`subsession-${subsession.id}`"
          >
            <subsession-form
              :subsession="subsession"
              :event-id="store.evanEvent?.id || 0"
              :session="session"
              @remove="removeSubsessionItem"
            />
          </q-tab-panel>
        </q-tab-panels>
      </div>
    </template>
    <template #footer>
      <div class="flex q-gutter-sm q-pa-lg">
        <q-btn
          v-if="session"
          @click="addSubsession"
          :icon="iconAdd"
          color="ugent"
          outline
          :label="$t('form.add') + ' ' + $t('models.subsession').toLocaleLowerCase()"
        />
        <q-space />
        <update-btn @click="createUpdate" :disabled="!formData.title" :loading="loading" :is-create="!props.obj" />
      </div>
    </template>
  </dialog-form>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch } from 'vue';
import { storeToRefs } from 'pinia';
import { debounce } from 'quasar';
import { useI18n } from 'vue-i18n';

import { useStore } from '../../store';
import { useProgramTemplate } from '@/composables/useProgramTemplate';
import { useMinimumLoading } from '@/composables/useMinimumLoading';
import { BADGE_ICONS, badgeIconName } from '@/utils/badges';

import UpdateBtn from '@/components/buttons/UpdateBtn.vue';
import DateSelect from '@/components/forms/DateSelect.vue';
import DialogForm from '@/components/forms/DialogForm.vue';
import MarkedTextarea from '@/components/forms/MarkedTextarea.vue';
import ProgramTemplateEditor from '@/components/forms/ProgramTemplateEditor.vue';
import ReadonlyField from '@/components/forms/ReadonlyField.vue';
import WarningBanner from '@/components/ui/WarningBanner.vue';
import SubsessionForm from './SubsessionForm.vue';

import { iconAdd, iconSession } from '@/icons';

const props = defineProps<{
  obj?: Session;
}>();

const store = useStore();
const { loading, executeWithMinLoading } = useMinimumLoading();
const { topicOptions, trackOptions, papers, sessions } = storeToRefs(store);
const { t } = useI18n();

const activeTab = ref('general');

const formData = ref<SessionData>({
  code: props.obj?.code || null,
  title: props.obj?.title || '',
  description: props.obj?.description || '',
  program: props.obj?.program || '',
  start_at: props.obj?.start_at || null,
  end_at: props.obj?.end_at || null,
  track: props.obj?.track || null,
  topics: props.obj?.topics || [],
  room: props.obj?.room || null,
  is_social_event: props.obj?.is_social_event || false,
  is_private: props.obj?.is_private || false,
  extra_attendees_fee: props.obj?.extra_attendees_fee || 0,
  extra_data: sessionExtraData(),
});

function sessionExtraData(): SessionExtraData {
  return {
    committees: props.obj?.extra_data?.committees ?? [],
    important_dates: props.obj?.extra_data?.important_dates ?? [],
    group: props.obj?.extra_data?.group ?? null,
    selectable_in_form: props.obj?.extra_data?.selectable_in_form ?? false,
    badge_icon: props.obj?.extra_data?.badge_icon ?? null,
  };
}

const badgeIconOptions = computed(() => [
  { label: t('badges.no_icon'), value: null as string | null },
  ...BADGE_ICONS.map((icon) => ({ label: t(`badges.icon_${icon}`), value: icon, icon: badgeIconName(icon) })),
]);

const badgeIcon = computed({
  get: (): string | null => formData.value.extra_data?.badge_icon ?? null,
  set: (value: string | null) => {
    formData.value.extra_data = { ...sessionExtraData(), badge_icon: value };
  },
});

function mergedExtraData(): SessionExtraData {
  return { ...sessionExtraData(), ...props.obj?.extra_data, ...formData.value.extra_data };
}

const programValidation = ref<{
  is_valid: boolean;
  errors: string[];
  paper_references: number[];
  keynote_references: string[];
} | null>(null);

const renderedProgram = ref<string>('');
const programTemplate = useProgramTemplate();

// Get session directly from store when available, otherwise use prop
const session = computed(() => {
  if (!props.obj?.id) return props.obj;
  return sessions.value.find((s) => s.id === props.obj!.id) || props.obj;
});

const roomOptions = computed<QuasarSelectOption[]>(() => {
  if (!store.evanEvent?.venues || store.evanEvent.venues.length === 0) return [];

  const result = [];

  const sortedVenues = [...store.evanEvent.venues].sort((a, b) => {
    if (a.is_main && !b.is_main) return -1;
    if (!a.is_main && b.is_main) return 1;
    return a.name.localeCompare(b.name);
  });

  for (const venue of sortedVenues) {
    if (venue.rooms && venue.rooms.length > 0) {
      const sortedRooms = [...venue.rooms].sort((a, b) => a.position - b.position);

      result.push({
        label: venue.name,
        value: `--venue--${venue.id}--`,
        disable: true,
        header: true,
      });

      for (const room of sortedRooms) {
        result.push({
          label: `— ${room.name}`,
          value: room.id,
        });
      }
    }
  }

  return result;
});

const sessionProgram = computed({
  get: () => formData.value.program || '',
  set: (value: string) => {
    formData.value.program = value;
  },
});

const hasSubsessions = computed(() => {
  return session.value?.subsessions && session.value.subsessions.length > 0;
});

const sortedSubsessions = computed(() => {
  if (!session.value?.subsessions) return [];
  return session.value.subsessions.slice().sort((a, b) => {
    // Sort by start time if both have it, otherwise fallback to creation order (id)
    if (a.start_at && b.start_at) {
      return new Date(a.start_at).getTime() - new Date(b.start_at).getTime();
    }
    // If only one has start_at, prioritize the one with start time
    if (a.start_at && !b.start_at) return -1;
    if (!a.start_at && b.start_at) return 1;
    // If neither has start_at, sort by ID (creation order)
    return a.id - b.id;
  });
});

watch(
  () => formData.value.code,
  (newCode) => {
    if (newCode === '') {
      formData.value.code = null;
    }
  },
);

// Debounced validation
const debouncedValidation = debounce(async (template: string) => {
  if (template) {
    programValidation.value = await programTemplate.validateTemplate(template);
  }
}, 500);

// Debounced rendering
const debouncedRendering = debounce(async (template: string) => {
  if (template) {
    const rendered = await programTemplate.renderTemplate(template);
    renderedProgram.value = rendered;
  }
}, 1000);

function onProgramChanged(template: string) {
  debouncedValidation(template);
  debouncedRendering(template);
}

watch(
  () => formData.value.program,
  (newProgram) => {
    if (newProgram) {
      onProgramChanged(newProgram);
    } else {
      renderedProgram.value = '';
    }
  },
  { immediate: true },
);

function addSubsession() {
  if (!session.value) return;

  const nextOrder = session.value.subsessions
    ? Math.max(...session.value.subsessions.map((s: Subsession) => s.order), 0) + 1
    : 1;

  const newSubsession: SubsessionData = {
    title: '',
    order: nextOrder,
    program: '', // Initialize program for new subsessions
    start_at: session.value.start_at, // Default to parent session start time
    end_at: session.value.end_at, // Default to parent session end time
  };

  store.createSubsession(session.value.id, newSubsession).then((res) => {
    if (res?.data) {
      // Switch to the new subsession tab
      activeTab.value = `subsession-${res.data.id}`;
    }
  });
}

function removeSubsessionItem(subsession: Subsession) {
  // Check if we're currently on the tab being deleted
  const isCurrentTab = activeTab.value === `subsession-${subsession.id}`;

  store.removeSubsession(subsession);

  // If we were on the deleted tab, switch to a different tab
  if (isCurrentTab) {
    // Switch to general tab or first subsession tab
    const remainingSubsessions = sortedSubsessions.value.filter((s) => s.id !== subsession.id);
    if (remainingSubsessions.length > 0) {
      activeTab.value = `subsession-${remainingSubsessions[0].id}`;
    } else {
      activeTab.value = 'general';
    }
  }
}

async function createUpdate() {
  if (!formData.value.title) return;

  await executeWithMinLoading(async () => {
    if (props.obj) {
      await store.updateSession({ ...props.obj, ...formData.value, extra_data: mergedExtraData() });
    } else {
      await store.createSession({ ...formData.value, extra_data: mergedExtraData() });
    }
  });
}

function unlinkPaperFromSession(paper: Paper) {
  // TODO: Add API call to unlink paper from session
  // For now, just refresh the papers list
  store.fetchPapers();
}

function toRomanNumeral(num: number): string {
  const values = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1];
  const numerals = ['M', 'CM', 'D', 'CD', 'C', 'XC', 'L', 'XL', 'X', 'IX', 'V', 'IV', 'I'];

  let result = '';
  for (let i = 0; i < values.length; i++) {
    while (num >= values[i]) {
      result += numerals[i];
      num -= values[i];
    }
  }
  return result;
}

onMounted(() => {
  if (papers.value.length === 0) {
    store.fetchPapers();
  }
});
</script>
