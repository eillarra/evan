import { ref, computed } from 'vue';
import { api } from '@/axios';
import { notify } from '@/utils/notify';

export function useAlbums(eventCode?: string) {
  const albums = ref<Album[]>([]);
  const loading = ref(false);
  const error = ref<string | null>(null);

  const albumsCount = computed(() => albums.value.length);

  async function fetchAlbums(code?: string) {
    const targetEventCode = code || eventCode;
    if (!targetEventCode) {
      error.value = 'Event code is required';
      return;
    }

    loading.value = true;
    error.value = null;

    try {
      const response = await api.get(`/events/${targetEventCode}/albums/?include_photos=true`);
      albums.value = response.data;
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch albums';
      error.value = errorMessage;
      notify.error(errorMessage);
    } finally {
      loading.value = false;
    }
  }

  async function fetchAlbum(albumId: number): Promise<Album | null> {
    loading.value = true;
    error.value = null;

    try {
      const response = await api.get(`/albums/${albumId}/`);
      return response.data;
    } catch (err: unknown) {
      const errorMessage = err instanceof Error ? err.message : 'Failed to fetch album';
      error.value = errorMessage;
      notify.error(errorMessage);
      return null;
    } finally {
      loading.value = false;
    }
  }

  return {
    albums,
    albumsCount,
    loading,
    error,
    fetchAlbums,
    fetchAlbum,
  };
}
