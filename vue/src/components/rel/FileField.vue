<template>
  <q-file
    ref="qFileRef"
    :model-value="fileModel"
    :readonly="readOnly"
    :accept="accept"
    :loading="uploading"
    @update:model-value="handleFileSelect"
    class="use-default-q-btn"
  >
    <template #append>
      <q-btn v-if="currentFile" dense round flat :icon="iconEye" color="ugent" size="sm" @click="openLink" />
      <q-btn v-else dense round flat :icon="iconAttachment" size="xs" @click.stop="(qFileRef as any)?.pickFiles()" />
      <q-btn
        v-if="currentFile && !readOnly"
        dense
        round
        flat
        :icon="iconDelete"
        color="red"
        size="sm"
        @click="deleteFile"
      />
    </template>
  </q-file>
</template>

<script setup lang="ts">
import { computed, ref, watch, onMounted, useTemplateRef } from 'vue';
import { useI18n } from 'vue-i18n';

import { api } from '@/axios';
import { confirm } from '@/utils/dialog';
import { notify } from '@/utils/notify';

import { iconAttachment, iconEye, iconDelete } from '@/icons';

const { t } = useI18n();

const props = defineProps<{
  apiEndpoint: ApiEndpoint;
  tags: string[];
  accept?: string;
  public?: boolean;
  readOnly?: boolean;
}>();

const emit = defineEmits<{
  fileChanged: [file: RelatedFile | null];
}>();

const qFileRef = useTemplateRef('qFileRef');
const uploading = ref(false);
const files = ref<RelatedFile[]>([]);

// File model for q-file component - show current file name or null for file picker
const fileModel = computed(() => {
  if (currentFile.value) {
    // Create a fake File-like object with the current file name for display
    return { name: currentFile.value.description || fileName.value } as File;
  }
  return null;
});

// Find the current file with any of the specified tags
const currentFile = computed<RelatedFile | null>(() => {
  return files.value.find((file) => props.tags.some((tag: string) => file.tags.includes(tag))) || null;
});

// Extract filename from URL for display
const fileName = computed(() => {
  if (!currentFile.value?.file) return '';
  const url = currentFile.value.file;
  return url.split('/').pop() || url;
});

async function fetchFiles() {
  if (!props.apiEndpoint) return;

  try {
    const response = await api.get<RelatedFile[]>(props.apiEndpoint);
    files.value = response.data;
  } catch (error) {
    console.error('Failed to fetch files:', error);
  }
}

async function handleFileSelect(selectedFile: File | null) {
  if (!selectedFile || !props.apiEndpoint) return;

  uploading.value = true;

  try {
    // If there's already a file with this tag, delete it first
    if (currentFile.value) {
      await api.delete(currentFile.value.self);
      files.value = files.value.filter((f) => f.id !== currentFile.value!.id);
    }

    // Prepare form data
    const formData = new FormData();
    formData.append('file', selectedFile);
    formData.append(
      'json',
      JSON.stringify({
        type: props.public ? 'public' : 'private',
        description: selectedFile.name,
        tags: props.tags,
      }),
    );

    // Upload new file
    const response = await api.post<RelatedFile>(props.apiEndpoint, formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });

    files.value.push(response.data);
    emit('fileChanged', response.data);
    notify.success(t('messages.file_uploaded'));
  } catch (error) {
    console.error('Failed to upload file:', error);
    notify.error(t('messages.file_upload_failed'));
  } finally {
    uploading.value = false;
  }
}

function deleteFile() {
  if (!currentFile.value || props.readOnly) return;

  confirm(t('messages.file_confirm_delete'), () => {
    api.delete(currentFile.value!.self).then(() => {
      files.value = files.value.filter((f) => f.id !== currentFile.value!.id);
      emit('fileChanged', null);
      notify.success(t('messages.file_deleted'));
    });
  });
}

function openLink() {
  if (currentFile.value?.file) {
    window.open(currentFile.value.file, '_blank');
  }
}

// Initialize
onMounted(fetchFiles);
watch(() => props.apiEndpoint, fetchFiles);

// Emit initial value
watch(
  currentFile,
  (newFile) => {
    emit('fileChanged', newFile);
  },
  { immediate: true },
);
</script>
