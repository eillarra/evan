<template>
  <dialog-form :icon="iconPaper" :title="$t('models.paper')">
    <template #tabs>
      <q-tabs v-model="activeTab" dense narrow-indicator no-caps align="left">
        <q-tab name="general" :label="$t('tabs.general')" />
        <q-tab name="abstract" :label="$t('fields.abstract')" />
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
                v-model="extraData.internal_id"
                :label="$t('fields.internal_id')"
                :readonly="!!(props.obj && props.obj.extra_data?.internal_id)"
                class="col-12 col-md-3"
              />
              <readonly-field
                v-if="props.obj"
                :label="$t('program_shortcut')"
                :value="
                  props.obj.extra_data?.internal_id
                    ? `[paper:${props.obj.id}] or [paperi:${props.obj.extra_data?.internal_id}]`
                    : `[paper:${props.obj.id}]`
                "
                class="col-12 col-md"
              />
              <q-input dense v-model="formData.title" :label="`${$t('fields.title')} *`" class="col-12" />
              <q-input dense v-model="extraData.authors_str" :label="$t('fields.author', 9)" class="col-12" />
              <q-input dense v-model="formData.doi" :label="$t('fields.doi')" class="col-12" />
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
                <warning-banner class="full-heigth full-width">{{ $t('paper.session_locked_warning') }}</warning-banner>
              </div>
            </div>
          </q-tab-panel>
          <q-tab-panel name="abstract">
            <marked-textarea v-model="formData.abstract" :label="$t('fields.abstract')" class="col-12" />
          </q-tab-panel>
          <q-tab-panel name="extra_data">
            <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
              <div class="col-12">
                <div class="text-subtitle2 q-mb-sm">{{ $t('fields.author', 9) }}</div>
                <div v-for="(author, index) in extraData.authors" :key="index" class="row q-col-gutter-sm q-mb-sm">
                  <q-input dense v-model="author.name" :label="$t('fields.name')" class="col-4" />
                  <q-input dense v-model="author.affiliation" :label="$t('fields.affiliation')" class="col" />
                  <q-btn
                    flat
                    dense
                    round
                    :icon="iconDelete"
                    color="negative"
                    @click="removeAuthor(index)"
                    class="col-2"
                  />
                </div>
                <q-btn flat dense :icon="iconAdd" :label="$t('form.add')" @click="addAuthor" color="primary" />
              </div>
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
          :disable="!formData.title"
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

import { iconAdd, iconDelete, iconPaper } from '@/icons';

interface PaperAuthor {
  name: string;
  affiliation: string | null;
}

interface PaperExtraData {
  authors_str: string | null;
  authors: PaperAuthor[];
  internal_id: number | string | null;
}

const props = defineProps<{
  obj?: Paper;
}>();

const store = useStore();

const { topicOptions, sessionOptions } = storeToRefs(store);

const obj = ref<Paper | undefined>(props.obj);
const activeTab = ref('general');

const isReferencedInProgram = computed(() => {
  if (!props.obj) return false;

  const paperPattern = new RegExp(`\\[paper:${props.obj.id}\\]`, 'g');
  const paperInternalPattern = props.obj.extra_data?.internal_id
    ? new RegExp(`\\[paperi:${props.obj.extra_data.internal_id}\\]`, 'g')
    : null;

  const checkProgram = (program: string) => {
    const hasDirectReference = paperPattern.test(program);
    const hasInternalReference = paperInternalPattern && paperInternalPattern.test(program);
    return hasDirectReference || hasInternalReference;
  };

  return store.sessions.some((session) => {
    if (session.program && checkProgram(session.program)) {
      return true;
    }

    if (session.subsessions) {
      return session.subsessions.some((subsession) => {
        return subsession.program && checkProgram(subsession.program);
      });
    }

    return false;
  });
});

const formData = ref<PaperData>({
  title: props.obj?.title || '',
  abstract: props.obj?.abstract || '',
  doi: props.obj?.doi || '',
  session: props.obj?.session || null,
  topics: props.obj?.topics || [],
});

const extraData = ref<PaperExtraData>({
  authors_str: props.obj?.extra_data?.authors_str || null,
  authors: props.obj?.extra_data?.authors || [],
  internal_id: props.obj?.extra_data?.internal_id || null,
});

onMounted(() => {
  if (sessionOptions.value.length === 0) {
    store.fetchSessions();
  }
});

function addAuthor() {
  extraData.value.authors.push({
    name: '',
    affiliation: null,
  });
}

function removeAuthor(index: number) {
  extraData.value.authors.splice(index, 1);
}

function createUpdate() {
  if (!formData.value.title) return;

  const cleanedExtraData = {
    authors_str: extraData.value.authors_str || '',
    authors: extraData.value.authors.map((author) => ({
      name: author.name,
      affiliation: author.affiliation || '',
    })),
    internal_id: extraData.value.internal_id || undefined,
  };

  const data = {
    ...formData.value,
    extra_data: cleanedExtraData,
  };

  if (props.obj) {
    store.updatePaper({ ...props.obj, ...data });
  } else {
    store.createPaper(data).then((res) => {
      if (res && res.data) {
        obj.value = res.data as Paper;
      }
    });
  }
}
</script>
