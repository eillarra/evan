<style scoped>
.photo-thumbnail {
  cursor: pointer;
  transition: transform 0.2s ease;
}

.photo-thumbnail:hover {
  transform: scale(1.05);
}

.photo-grid {
  display: grid;
  grid-template-columns: repeat(7, 1fr);
  gap: 8px;
}

.photo-item {
  aspect-ratio: 1;
}

.arrow-left {
  transform: rotate(180deg);
}

.dialog-photo {
  max-width: 90vw;
  max-height: 90vh;
  object-fit: contain;
}
</style>

<template>
  <!-- Loading state -->
  <div v-if="props.loading" class="text-center q-pa-lg">
    <div class="q-mt-md text-grey-7">{{ $t('loading') }}</div>
  </div>

  <!-- No results (only show when not loading and no albums) -->
  <no-results v-else-if="albums.length === 0" />

  <!-- Albums content -->
  <div v-else>
    <!-- Album Tabs -->
    <div class="q-mb-lg">
      <q-tabs v-model="selectedAlbum" dense narrow-indicator no-caps align="left" style="margin-left: -16px">
        <q-tab v-for="album in albums" :key="album.id" :name="album.id">
          <span>
            {{ album.title }}
            <q-badge
              v-if="album.photos && album.photos.length > 0"
              color="grey-3"
              text-color="grey-8"
              rounded
              style="vertical-align: middle; margin-left: 4px"
            >
              {{ album.photos.length }}
            </q-badge>
          </span>
        </q-tab>
      </q-tabs>
    </div>

    <!-- Download Section -->
    <div v-if="currentAlbum && currentAlbum.collection_zip" class="q-mb-md">
      <q-btn
        @click="downloadAlbum"
        :icon="iconDownload"
        color="primary"
        outline
        no-caps
        class="q-mr-sm"
        :loading="downloadLoading"
        :disabled="downloadLoading"
      >
        Download all photos ({{ currentAlbum.title }})
      </q-btn>
      <span class="text-caption text-grey-6">
        ZIP file with all {{ currentAlbum.photos?.length || 0 }} original photos
      </span>
    </div>

    <!-- Photos Grid -->
    <div v-if="currentAlbum && currentAlbum.photos" :key="currentAlbum.id" class="photo-grid">
      <div v-for="(photo, index) in currentAlbum.photos" :key="`${currentAlbum.id}-${index}`" class="photo-item">
        <q-img :src="photo.thumbnail?.file" :ratio="1" class="cursor-pointer" fit="cover" @click="openPhoto(index)" />
      </div>
    </div>

    <!-- Photo Viewer Dialog -->
    <q-dialog v-model="showPhotoDialog" maximized>
      <q-card class="bg-black">
        <q-card-section class="row items-center q-pb-none text-white">
          <div class="text-h6">{{ currentAlbum?.title }}</div>
          <q-space />
          <div class="text-subtitle2 q-mr-md">
            {{ currentPhotoIndex + 1 || 0 }} / {{ currentAlbum?.photos?.length || 0 }}
          </div>
          <q-btn :icon="iconClose" flat round dense color="white" v-close-popup />
        </q-card-section>

        <q-card-section v-if="currentPhoto" class="flex flex-center" style="height: calc(100vh - 100px)">
          <!-- Navigation buttons -->
          <q-btn
            v-if="currentPhotoIndex > 0"
            @click="previousPhoto"
            :icon="iconArrowForward"
            flat
            round
            size="lg"
            color="white"
            class="absolute-left q-ml-md arrow-left"
          />

          <!-- Current photo -->
          <q-img :src="currentPhoto.original.file" class="" style="max-height: 90vh; max-width: 90vw" fit="contain" />

          <q-btn
            v-if="currentPhotoIndex < (currentAlbum?.photos?.length || 0) - 1"
            @click="nextPhoto"
            :icon="iconArrowForward"
            flat
            round
            size="lg"
            color="white"
            class="absolute-right q-mr-md"
          />
        </q-card-section>
      </q-card>
    </q-dialog>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';

import NoResults from '@/components/NoResults.vue';

import { iconArrowForward, iconClose, iconDownload } from '@/icons';

interface Props {
  eventCode: string;
  albums: Album[];
  loading?: boolean;
}

const props = defineProps<Props>();

const selectedAlbum = ref<number | null>(null);
const showPhotoDialog = ref(false);
const currentPhotoIndex = ref<number>(0);
const downloadLoading = ref(false);

// Computed properties
const currentAlbum = computed(() => props.albums.find((album) => album.id === selectedAlbum.value) || null);

const currentPhoto = computed((): PhotoPair | null => {
  if (!currentAlbum.value || !currentAlbum.value.photos || currentPhotoIndex.value === null) return null;
  return currentAlbum.value.photos[currentPhotoIndex.value] || null;
});

// Methods
function openPhoto(index: number) {
  currentPhotoIndex.value = index;
  showPhotoDialog.value = true;
}

function nextPhoto() {
  if (
    currentAlbum.value &&
    currentAlbum.value.photos &&
    currentPhotoIndex.value < currentAlbum.value.photos.length - 1
  ) {
    currentPhotoIndex.value++;
  }
}

function previousPhoto() {
  if (currentPhotoIndex.value > 0) {
    currentPhotoIndex.value--;
  }
}

function downloadAlbum() {
  if (!currentAlbum.value?.collection_zip?.file) return;

  downloadLoading.value = true;

  try {
    // Create a temporary link to trigger download
    const link = document.createElement('a');
    link.href = currentAlbum.value.collection_zip.file;
    link.download = `${currentAlbum.value.title}.zip`;
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);

    // Use a timeout to reset the loading state since we can't detect when download actually starts
    setTimeout(() => {
      downloadLoading.value = false;
    }, 4000); // Reset after 4 seconds
  } catch (error) {
    console.error('Error downloading album:', error);
    downloadLoading.value = false;
  }
}

// Keyboard navigation
function handleKeydown(event: KeyboardEvent) {
  if (!showPhotoDialog.value) return;

  if (event.key === 'ArrowLeft') {
    previousPhoto();
  } else if (event.key === 'ArrowRight') {
    nextPhoto();
  } else if (event.key === 'Escape') {
    showPhotoDialog.value = false;
  }
}

// Add keyboard event listeners when dialog is open
watch(showPhotoDialog, (isOpen) => {
  if (isOpen) {
    document.addEventListener('keydown', handleKeydown);
  } else {
    document.removeEventListener('keydown', handleKeydown);
  }
});

// Auto-select first album if available
watch(
  () => props.albums,
  (newAlbums) => {
    if (newAlbums.length > 0 && !selectedAlbum.value) {
      selectedAlbum.value = newAlbums[0].id;
    }
  },
  { immediate: true },
);
</script>
