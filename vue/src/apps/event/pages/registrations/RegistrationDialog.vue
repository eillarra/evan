<template>
  <full-dialog icon="calendar_month" :title="internshipName">
    <template #menu>
      <q-list :dense="$q.screen.gt.sm" class="q-mt-xs">
        <q-item-label header>{{ $t('internship') }}</q-item-label>
        <q-item clickable @click="tab = 'info'" :active="tab == 'info'" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon name="info_outline" size="xs"></q-icon>
          </q-item-section>
          <q-item-section>Info</q-item-section>
        </q-item>
        <q-item clickable @click="tab = 'mentors'" :active="tab == 'mentors'" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon name="people_outline" size="xs"></q-icon>
          </q-item-section>
          <q-item-section>{{ $t('mentor', 9) }}</q-item-section>
        </q-item>
      </q-list>
    </template>
    <template #page>
      <q-tab-panels v-model="tab" class="q-pb-lg">
        <q-tab-panel name="info">
          <div class="row q-col-gutter-xl">
            <div class="col-12 col-md-8">
              <div class="q-gutter-sm">
                <readonly-field :label="$t('project')" :value="projectName" />
                <readonly-field :label="$t('student')" :value="obj.Student?.User?.name || '-'" />
                <div class="row q-col-gutter-lg q-pt-sm q-pl-sm">
                  <date-select
                    v-model="obj.start_date"
                    :label="$t('fields.start_date')"
                    clearable
                    class="col-12 col-md"
                  />
                  <date-select v-model="obj.end_date" :label="$t('fields.end_date')" clearable class="col-12 col-md" />
                </div>
              </div>
            </div>
          </div>
        </q-tab-panel>
      </q-tab-panels>
    </template>
    <template #footer>
      <div v-if="tab == 'info'" class="flex q-gutter-sm q-pa-lg">
        <q-space />
        <q-btn @click="save" unelevated color="ugent" :label="$t('form.internship.save')" />
      </div>
    </template>
  </full-dialog>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { storeToRefs } from 'pinia';
import { useI18n } from 'vue-i18n';

import { api } from '@/axios';
import { notify } from '@/utils/notify';

import { useStore } from '../../store';

import FullDialog from '@/components/FullDialog.vue';

defineEmits(['delete:obj']);

const props = defineProps<{
  obj: Registration;
}>();

const { t } = useI18n();
const store = useStore();
const { education, project, emails } = storeToRefs(store);

const obj = ref<Internship>(props.obj);
const tab = ref<string>('info');
const projectName = computed<string>(() => (project.value ? project.value.name : ''));
const internshipName = computed<string>(
  () => `${obj.value.Student?.User?.name} - ${obj.value.Place?.name || ''} (${obj.value.Discipline?.name})`,
);
const hasStarted = computed<boolean>(() => {
  if (!obj.value.start_date) return false;
  return new Date(obj.value.start_date) <= new Date();
});
const hasRemarks = computed<boolean>(() => Number(obj.value.tag_objects?.['remarks.count']) || 0 > 0);

const filteredPeriods = computed(() => {
  if (!project.value) return [];
  if (!obj.value.Student?.Track) return (project.value as Project).periods;

  return (project.value as Project).periods.filter((period) => {
    return (
      obj.value.Student?.block == period.ProgramInternship?.block &&
      obj.value.Student?.Track?.program_internships.includes(period.program_internship)
    );
  });
});

const remarkEndpoints = computed<null | Record<string, ApiEndpoint>>(() => {
  if (!props.obj) return null;
  return {
    default: props.obj.rel_remarks,
  };
});

function save() {
  api
    .put(obj.value.self, {
      ...obj.value,
      student: obj.value.Student?.id,
      track: obj.value.Track?.id,
    })
    .then((res) => {
      obj.value.updated_at = res.data.updated_at;
      obj.value.updated_by = res.data.updated_by;
      store.updateObj('projectInternship', obj.value);
      notify.success(t('form.internship.saved'));
    });
}

function updateObj(obj: Internship) {
  store.updateObj('projectInternship', obj);
}

onMounted(() => store.fetchEmails());
</script>
