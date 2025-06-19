<template>
  <dialog-form :icon="iconKeynote" :title="$t('models.keynote')">
    <template #tabs>
      <q-tabs v-model="activeTab" dense narrow-indicator no-caps align="left">
        <q-tab name="general" :label="$t('tabs.general')" />
        <q-tab name="abstract" :label="$t('fields.abstract')" />
        <q-tab name="bio" :label="$t('fields.bio')" />
        <q-tab name="extra_data" :label="$t('tabs.extra_data')" />
      </q-tabs>
    </template>
    <template #page>
      <div class="q-pb-lg q-px-sm">
        <q-tab-panels v-model="activeTab">
          <q-tab-panel name="general">
            <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
              <q-input
                dense
                v-model="formData.code"
                :label="`${$t('fields.code')} *`"
                :readonly="!!props.obj"
                class="col-12 col-md-3"
              />
              <readonly-field
                v-if="props.obj"
                :label="$t('program_shortcut')"
                :value="`[keynote:${props.obj.code}]`"
                class="col-12 col-md"
              />
              <q-input dense v-model="formData.title" :label="`${$t('fields.title')} *`" class="col-12" />
              <q-input dense v-model="formData.speaker" :label="`${$t('fields.speaker')} *`" class="col-12" />
              <evan-select
                v-model="formData.topics"
                :label="$t('models.topic', 9)"
                :options="topicOptions"
                multiple
                class="col-12"
              />
              <evan-select
                v-model="formData.session"
                :label="$t('models.session')"
                :options="sessionOptions"
                clearable
                :disable="isReferencedInProgram"
                class="col-12 col-md-3"
              />
              <div v-if="isReferencedInProgram" class="col-12 col-md-9">
                <warning-banner class="full-heigth full-width">{{
                  $t('keynote.session_locked_warning')
                }}</warning-banner>
              </div>
            </div>
          </q-tab-panel>
          <q-tab-panel name="abstract">
            <marked-textarea v-model="formData.abstract" :label="$t('fields.abstract')" class="col-12" />
          </q-tab-panel>
          <q-tab-panel name="bio">
            <marked-textarea v-model="formData.bio" :label="$t('fields.bio')" class="col-12" />
          </q-tab-panel>
          <q-tab-panel name="extra_data">
            <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
              <q-input
                dense
                v-model="extraData.speaker_affiliation"
                :label="$t('fields.speaker_affiliation')"
                class="col-12"
              />
              <q-input
                dense
                v-model="extraData.speaker_email"
                :label="$t('fields.speaker_email')"
                type="email"
                class="col-12"
              />
              <q-input
                dense
                v-model="extraData.presentation_url"
                :label="$t('fields.presentation_url')"
                type="url"
                class="col-12"
              />
            </div>
          </q-tab-panel>
        </q-tab-panels>
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
          :disable="!formData.code || !formData.title || !formData.speaker"
        />
      </div>
    </template>
  </dialog-form>
</template>

<script setup lang="ts">
import { ref, onMounted, computed } from 'vue';
import { storeToRefs } from 'pinia';

import { useStore } from '../../store';

import DialogForm from '@/components/forms/DialogForm.vue';
import MarkedTextarea from '@/components/forms/MarkedTextarea.vue';
import ReadonlyField from '@/components/forms/ReadonlyField.vue';
import WarningBanner from '@/components/ui/WarningBanner.vue';

import { iconKeynote } from '@/icons';

interface KeynoteExtraData {
  speaker_affiliation: string | null;
  speaker_email: string | null;
  presentation_url: string | null;
}

const props = defineProps<{
  obj?: Keynote;
}>();

const store = useStore();

const { topicOptions, sessionOptions } = storeToRefs(store);

const obj = ref<Keynote | undefined>(props.obj);
const activeTab = ref('general');

const formData = ref<KeynoteData>({
  code: props.obj?.code || '',
  title: props.obj?.title || '',
  speaker: props.obj?.speaker || '',
  bio: props.obj?.bio || '',
  abstract: props.obj?.abstract || '',
  session: props.obj?.session || null,
  topics: props.obj?.topics || [],
});

const extraData = ref<KeynoteExtraData>({
  speaker_affiliation: props.obj?.extra_data?.speaker_affiliation || null,
  speaker_email: props.obj?.extra_data?.speaker_email || null,
  presentation_url: props.obj?.extra_data?.presentation_url || null,
});

onMounted(() => {
  if (sessionOptions.value.length === 0) {
    store.fetchSessions();
  }
});

const isReferencedInProgram = computed(() => {
  if (!props.obj) return false;

  const keynotePattern = new RegExp(`\\[keynote:${props.obj.code}\\]`, 'g');

  return store.sessions.some((session) => {
    if (session.program && keynotePattern.test(session.program)) {
      return true;
    }

    if (session.subsessions) {
      return session.subsessions.some((subsession) => {
        return subsession.program && keynotePattern.test(subsession.program);
      });
    }

    return false;
  });
});

function createUpdate() {
  if (!formData.value.code || !formData.value.title || !formData.value.speaker) return;

  const cleanedExtraData = {
    speaker_affiliation: extraData.value.speaker_affiliation || undefined,
    speaker_email: extraData.value.speaker_email || undefined,
    presentation_url: extraData.value.presentation_url || undefined,
  };

  const data = {
    ...formData.value,
    extra_data: cleanedExtraData,
  };

  if (props.obj) {
    store.updateKeynote({ ...props.obj, ...data });
  } else {
    store.createKeynote(data).then((res) => {
      if (res && res.data) {
        obj.value = res.data as Keynote;
      }
    });
  }
}
</script>
