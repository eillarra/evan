<template>
  <div>
    <div class="ugent__create-btn">
      <q-btn
        unelevated
        color="blue-1"
        :label="$t('form.new')"
        :icon="iconAdd"
        class="text-ugent float-right"
        @click="() => (dialog = true)"
      />
      <h4 v-if="title" class="q-mt-none q-mb-md">{{ title }}</h4>
    </div>
    <data-table
      :columns="columns"
      :rows="rows"
      sort-by="notes"
      :form-component="PersonForm"
      :updateCallback="updatePerson"
      removable
      @remove:row="removePerson"
      hide-pagination
      hide-toolbar
    />
    <q-dialog v-model="dialog">
      <person-form @create:obj="syncPersons" />
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, defineProps } from 'vue';
import { useI18n } from 'vue-i18n';

import { api } from '@/axios.ts';
import { confirm } from '@/utils/dialog';
import { notify } from '@/utils/notify';

import DataTable from '@/components/tables/DataTable.vue';
import PersonForm from './PersonForm.vue';

import { iconAdd } from '@/icons';

const emit = defineEmits(['update:modelValue']);

const props = defineProps<{
  modelValue: Session;
  field: 'chairs' | 'program_committee';
  title?: string;
}>();

const { t } = useI18n();

const dialog = ref(false);
const mutable = ref<Session>(props.modelValue);

const columns = [
  {
    name: 'name',
    field: 'name',
    required: true,
    label: t('fields.name'),
    align: 'left',
    sortable: true,
    sort: (a: string, b: string) => a.localeCompare(b),
    headerClasses: 'sticky-left',
    classes: 'sticky-left',
  },
];

const rows = computed(() => {
  if (!mutable.value.extra_data || !mutable.value.extra_data[props.field]) {
    return [];
  }
  return mutable.value.extra_data[props.field].map((obj: Person) => ({
    _self: obj,
    name: obj.affiliation ? `${obj.name}, ${obj.affiliation}` : obj.name,
  }));
});

function updatePersons() {
  mutable.value.extra_data[props.field].sort((a: Person, b: Person) => {
    return a.name.localeCompare(b.name);
  });
  return api.patch(mutable.value.self, { extra_data: mutable.value.extra_data }).then(() => {
    emit('update:modelValue', mutable.value);
  });
}

function updatePerson(oldPerson: Person, person: Person) {
  const index = mutable.value.extra_data[props.field].findIndex((d: Person) => d.name === oldPerson.name);
  if (index !== -1) {
    mutable.value.extra_data[props.field][index] = person as Person;
    updatePersons().then(() => {
      notify.success(t('messages.contact_updated'));
    });
  }
}

function removePerson(row: { _self: Person }) {
  confirm(t('messages.contact_confirm_delete'), () => {
    mutable.value.extra_data[props.field] = mutable.value.extra_data[props.field].filter(
      (person: Person) => person !== row._self,
    );
    updatePersons().then(() => {
      notify.success(t('messages.contact_deleted'));
    });
  });
}

function syncPersons(obj: Person) {
  mutable.value.extra_data[props.field].push(obj);
  updatePersons();
  dialog.value = false;
}
</script>
