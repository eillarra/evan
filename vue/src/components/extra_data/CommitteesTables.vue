<template>
  <div class="flex q-mb-lg ugent__create-btn">
    <h3 class="text-ugent q-mb-none">
      {{ $t('models.committee', 9) }}
    </h3>
    <q-space />
    <q-btn
      unelevated
      color="blue-1"
      :label="$t('form.new')"
      :icon="iconAdd"
      class="text-ugent float-right"
      @click="createCommittee"
    />
  </div>
  <no-results v-if="!committees.length" />
  <div v-else class="row q-col-gutter-xl">
    <div v-for="(committee, idx) in committees" :key="idx" class="col-12 col-md-6">
      <div class="ugent__create-btn">
        <q-btn
          unelevated
          color="blue-1"
          :label="$t('form.new_member')"
          :icon="iconAdd"
          class="text-ugent float-right"
          @click="() => openDialog(idx)"
        />
        <h4 class="q-mt-none q-mb-md cursor-pointer q-gutter-x-sm">
          <span @click="toggleEditMode(idx)">{{ committee.name }}</span>
          <q-icon :name="iconEdit" @click="toggleEditMode(idx)" />
          <q-icon :name="iconArrowUp" @click="moveCommitteeUp(idx)" v-if="idx > 0" />
          <q-icon :name="iconArrowDown" @click="moveCommitteeDown(idx)" v-if="idx < committees.length - 1" />
          <q-icon :name="iconDelete" @click="removeCommitte(committee)" color="red" />
        </h4>
        <div v-if="editMode[idx]">
          <q-input dense v-model.trim="committee.name" label="Committee Name" />
          <q-select
            dense
            v-model="committee.sorting"
            :options="committeeSortingOptions"
            label="Sorting"
            emit-value
            map-options
            options-dense
          />
          <q-select
            dense
            v-model="committee.display"
            :options="committeeDisplayOptions"
            label="Display"
            emit-value
            map-options
            options-dense
          />
          <q-btn unelevated @click="saveCommittee(committee)" color="blue-1" class="text-ugent q-my-md">Save</q-btn>
          <q-btn unelevated @click="toggleEditMode(idx)" color="grey-5" class="text-ugent q-my-md">Cancel</q-btn>
        </div>
      </div>
      <data-table
        :columns="columns"
        :rows="rows(idx)"
        sort-by="notes"
        :form-component="PersonForm"
        :updateCallback="(oldPerson, person) => updatePerson(idx, oldPerson, person)"
        removable
        @remove:row="(row) => removePerson(idx, row)"
        hide-pagination
        hide-toolbar
      />
      <q-dialog v-model="dialog[idx]">
        <person-form @create:obj="(person) => createPerson(idx, person)" />
      </q-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, defineProps } from 'vue';
import { useI18n } from 'vue-i18n';
import { v4 as uuidv4 } from 'uuid'; // Import UUID library

import { confirm } from '@/utils/dialog';
import { notify } from '@/utils/notify';

import NoResults from '@/components/NoResults.vue';
import DataTable from '@/components/tables/DataTable.vue';
import PersonForm from './PersonForm.vue';

import { iconAdd, iconArrowUp, iconArrowDown, iconDelete, iconEdit } from '@/icons';

const emit = defineEmits(['update:modelValue']);

const props = defineProps<{
  modelValue: Session;
  updateCallback: (data: SessionExtraData) => Promise<void>;
  title?: string;
}>();

const { t } = useI18n();

const mutable = ref<Session>(props.modelValue);
const committeeDisplayOptions: QuasarSelectOption[] = [
  { label: 'Expanded', value: 'full' },
  { label: 'Simple list of names', value: 'list' },
];
const committeeSortingOptions: QuasarSelectOption[] = [
  { label: 'First name', value: 'first_name' },
  { label: 'Last name', value: 'last_name' },
];

const committees = computed(() =>
  Array.isArray(mutable.value.extra_data.committees) ? mutable.value.extra_data.committees : [],
);

const editMode = ref(committees.value.map(() => false));
const dialog = ref(committees.value.map(() => false));

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

const rows = (index: number) => {
  return Array.isArray(committees.value[index].members)
    ? committees.value[index].members.map((obj: Person) => {
        if (!obj.id) {
          obj.id = uuidv4(); // Assign a temporary ID if not already present
        }
        return {
          _self: obj,
          name: obj.affiliation
            ? `${obj.first_name} ${obj.last_name}, ${obj.affiliation}`
            : `${obj.first_name} ${obj.last_name}`,
        };
      })
    : [];
};

function createCommittee() {
  const newCommittee: Committee = {
    name: 'New committee',
    members: [],
    sorting: 'last_name',
    display: 'list',
  };
  mutable.value.extra_data.committees.push(newCommittee);
  editMode.value.push(false);
  dialog.value.push(false);
  syncPersons().then(() => {
    notify.success(t('messages.committee_created'));
  });
}

function updateCommittee(name: string, updatedCommittee: Committee) {
  const index = mutable.value.extra_data.committees.findIndex((c: Committee) => c.name === name);
  if (index !== -1) {
    mutable.value.extra_data.committees[index] = updatedCommittee;
    syncPersons().then(() => {
      notify.success(t('messages.committee_updated'));
    });
  }
}

function removeCommitte(committee: Committee) {
  confirm(t('messages.committee_confirm_delete'), () => {
    const index = mutable.value.extra_data.committees.indexOf(committee);
    if (index !== -1) {
      mutable.value.extra_data.committees.splice(index, 1);
      editMode.value.splice(index, 1);
      dialog.value.splice(index, 1);
      syncPersons().then(() => {
        notify.success(t('messages.committee_deleted'));
      });
    }
  });
}

function syncPersons() {
  mutable.value.extra_data.committees.forEach((committee: Committee) => {
    committee.members.sort((a: Person, b: Person) => {
      if (committee.sorting === 'first_name') {
        return a.first_name.localeCompare(b.first_name);
      }
      return a.last_name.localeCompare(b.last_name);
    });
  });

  return props.updateCallback(mutable.value.extra_data).then(() => {
    emit('update:modelValue', mutable.value);
  });
}

function createPerson(index: number, obj: Person) {
  obj.id = uuidv4(); // Assign a temporary ID
  const committee = mutable.value.extra_data.committees[index];
  committee.members.push(obj);
  syncPersons().then(() => {
    notify.success(t('messages.member_created'));
  });
  dialog.value[index] = false;
}

function updatePerson(index: number, oldPerson: Person, person: Person) {
  const committee = mutable.value.extra_data.committees[index];
  const memberIndex = committee.members.findIndex((d: Person) => d.id === oldPerson.id); // Use temporary ID
  if (memberIndex !== -1) {
    committee.members[memberIndex] = person;
    syncPersons().then(() => {
      notify.success(t('messages.member_updated'));
    });
  }
}

function removePerson(index: number, row: { _self: Person }) {
  confirm(t('messages.member_confirm_delete'), () => {
    const committee = mutable.value.extra_data.committees[index];
    committee.members = committee.members.filter((person: Person) => person.id !== row._self.id); // Use temporary ID
    syncPersons().then(() => {
      notify.success(t('messages.member_deleted'));
    });
  });
}

function toggleEditMode(index: number) {
  editMode.value[index] = !editMode.value[index];
}

function saveCommittee(committee: Committee) {
  updateCommittee(committee.name, committee);
  const index = mutable.value.extra_data.committees.indexOf(committee);
  if (index !== -1) {
    editMode.value[index] = false;
  }
}

function moveCommitteeUp(index: number) {
  if (index > 0) {
    const temp = mutable.value.extra_data.committees[index];
    mutable.value.extra_data.committees[index] = mutable.value.extra_data.committees[index - 1];
    mutable.value.extra_data.committees[index - 1] = temp;
    syncPersons();
  }
}

function moveCommitteeDown(index: number) {
  if (index < mutable.value.extra_data.committees.length - 1) {
    const temp = mutable.value.extra_data.committees[index];
    mutable.value.extra_data.committees[index] = mutable.value.extra_data.committees[index + 1];
    mutable.value.extra_data.committees[index + 1] = temp;
    syncPersons();
  }
}

function openDialog(index: number) {
  dialog.value[index] = true;
}
</script>
