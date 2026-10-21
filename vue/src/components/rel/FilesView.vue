<template>
  <div>
    <div v-if="loading" class="flex flex-center q-mt-xl">
      <q-spinner color="grey-3" size="4em" />
    </div>
    <no-results v-else-if="!filteredFiles.length" />
    <template v-else>
      <q-markup-table dense flat class="use-default-q-btn full-width q-mb-lg text-body1">
        <tbody>
          <tr v-for="file in filteredFiles" :key="file.id">
            <td>{{ visibilityLabel(file.visibility) }}</td>
            <td>
              <a v-if="secret" href="#" @click.prevent="downloadFile(file)">{{ getDisplayName(file.file) }}</a>
              <a v-else :href="file.file" target="_blank">{{ getDisplayName(file.file) }}</a>
            </td>
            <td>{{ file.description || '-' }}</td>
            <td>{{ file.tags.join(', ') }}</td>
            <td>
              <q-btn
                v-if="!readOnly"
                flat
                round
                :icon="iconDelete"
                color="negative"
                size="sm"
                @click="deleteRelatedFile(file)"
              />
            </td>
          </tr>
        </tbody>
      </q-markup-table>
    </template>
    <div class="row q-col-gutter-sm">
      <q-space />
      <div v-if="!readOnly" class="col-6 col-md text-right ugent__create-btn">
        <q-btn
          unelevated
          color="blue-1"
          :label="$t('form.new')"
          :icon="iconAdd"
          class="text-ugent"
          @click="dialogVisible = true"
        />
      </div>
    </div>
    <q-dialog v-model="dialogVisible">
      <dialog-form size="sm" :icon="iconAdd" :title="$t('models.file')">
        <template #page>
          <div class="q-pa-lg">
            {{ customCreateDescription }}
            <div class="row q-col-gutter-sm">
              <q-file v-model="file" :label="$t('models.file')" :accept="selectedAccept" dense clearable class="col-12">
                <template #prepend>
                  <q-icon :name="iconAttachment" />
                </template>
                <template #append>
                  <q-badge :label="selectedAccept" color="grey" />
                </template>
              </q-file>
              <q-select
                v-model="formData.visibility"
                :label="$t('fields.visibility')"
                :options="visibilityOptions"
                emit-value
                map-options
                class="col-12"
                dense
                options-dense
                :disable="visibilityOptions.length === 1"
              />
              <q-input v-model="formData.description" :label="$t('fields.description')" dense class="col-12" />
            </div>
          </div>
        </template>
        <template #footer>
          <div class="flex q-gutter-sm q-pa-lg">
            <q-space />
            <q-btn
              unelevated
              @click="addRelatedFile"
              color="ugent"
              :label="$t('form.create')"
              :disable="!file || !formData.description"
            />
          </div>
        </template>
      </dialog-form>
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';

import { api, axios } from '@/axios';
import { confirm } from '@/utils/dialog';
import { notify } from '@/utils/notify';

import NoResults from '@/components/NoResults.vue';
import DialogForm from '@/components/forms/DialogForm.vue';

import { iconAdd, iconAttachment, iconDelete } from '@/icons';

const { t } = useI18n();

const props = defineProps<{
  apiEndpoint: ApiEndpoint;
  accept?: string;
  customCreateDescription?: string;
  filterTypes?: string[];
  visibilityOptions?: string[];
  readOnly?: boolean;
  createOnly?: boolean;
  /**
   * The secret of the owning object, when the viewer holds one (a session's
   * secret link). Every call carries it, and the files are downloaded through
   * the media path, because a plain link cannot carry a header.
   */
  secret?: string;
}>();

const loading = ref<boolean>(true);
const dialogVisible = ref<boolean>(false);
const files = ref<RelatedFile[]>([]);
const file = ref<File | null>(null);
const allVisibilityOptions: QuasarSelectOption[] = [
  {
    label: t('fields.visibility_public'),
    value: 'public',
  },
  {
    label: t('fields.visibility_attendees'),
    value: 'attendees',
  },
  {
    label: t('fields.visibility_organizers'),
    value: 'organizers',
  },
];
const visibilityOptions = computed<QuasarSelectOption[]>(() => {
  if (!props.visibilityOptions?.length) return allVisibilityOptions;
  return allVisibilityOptions.filter((option) => props.visibilityOptions?.includes(option.value as string));
});
const formData = ref({
  visibility: 'attendees' as 'public' | 'attendees' | 'organizers',
  description: null,
  tags: [],
});

const filteredFiles = computed<RelatedFile[]>(() => {
  if (!props.filterTypes) return files.value;
  return files.value.filter((file) => props.filterTypes?.some((type) => file.tags.includes(`type:${type}`)));
});

const selectedAccept = computed(() => props.accept || '*');

const requestHeaders = computed((): Record<string, string> => {
  if (!props.secret) return {};
  return { 'X-Evan-Secret': props.secret };
});

function getDisplayName(fileUrl: string): string {
  if (!fileUrl) return '';
  return fileUrl.split('/').pop() || fileUrl;
}

function visibilityLabel(visibility: RelatedFile['visibility']): string {
  const option = allVisibilityOptions.find((item) => item.value === visibility);
  return option?.label ?? visibility;
}

async function fetchRelatedFiles() {
  if (!props.apiEndpoint) return;
  await api
    .get<RelatedFile[]>(props.apiEndpoint, { headers: requestHeaders.value })
    .then((res) => {
      files.value = res.data.sort((a, b) => a.description.localeCompare(b.description));
      loading.value = false;
    })
    .catch(() => {
      loading.value = false;
    });
}

async function addRelatedFile() {
  if (!props.apiEndpoint || !formData.value.description || !file.value) return;

  const multipartFormData = new FormData();
  multipartFormData.append('file', file.value);
  multipartFormData.append('json', JSON.stringify(formData.value));

  api
    .post<RelatedFile>(props.apiEndpoint, multipartFormData, {
      headers: {
        'Content-Type': 'multipart/form-data',
        ...requestHeaders.value,
      },
    })
    .then((res) => {
      notify.success(t('messages.file_created'));
      files.value.push(res.data);
      reset();
    });
}

async function deleteRelatedFile(file: RelatedFile) {
  confirm(t('messages.file_confirm_delete'), () => {
    api.delete(file.self, { headers: requestHeaders.value }).then(() => {
      notify.success(t('messages.file_deleted'));
      files.value.splice(files.value.indexOf(file), 1);
    });
  });
}

// A plain link cannot carry the secret header, so the file is fetched through
// the media path and saved client-side.
async function downloadFile(file: RelatedFile) {
  try {
    const response = await axios.get(file.file, {
      headers: requestHeaders.value,
      responseType: 'blob',
    });
    const url = URL.createObjectURL(response.data as Blob);
    const link = document.createElement('a');
    link.href = url;
    link.download = getDisplayName(file.file);
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  } catch {
    notify.error(t('messages.file_download_failed'));
  }
}

fetchRelatedFiles();

watch(() => props.apiEndpoint, fetchRelatedFiles);

function reset() {
  file.value = null;
  formData.value.description = null;
  formData.value.tags = [];
  dialogVisible.value = false;
}
</script>
