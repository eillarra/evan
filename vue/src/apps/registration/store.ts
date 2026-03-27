import { ref, shallowRef } from 'vue';
import { useI18n } from 'vue-i18n';
import { defineStore } from 'pinia';

import { api } from '@/axios.ts';
import { notify } from '@/utils/notify';

export const useStore = defineStore('evanSession', () => {
  const loading = ref<boolean>(true);
  const evanEvent = shallowRef<EvanEvent | null>(null);
  const registration = shallowRef<Registration | null>(null);
  const albums = shallowRef<Album[]>([]);

  const { t } = useI18n();

  async function setData(inertiaEvanEvent: EvanEvent) {
    evanEvent.value = inertiaEvanEvent;
    await init();
  }

  async function setPreviewData(inertiaEvanEvent: EvanEvent) {
    evanEvent.value = inertiaEvanEvent;
    loading.value = false;
  }

  async function init() {
    await getRegistrations();
  }

  // Registration ------

  async function getRegistrations() {
    api.get<Registration[]>('/user/registrations/').then((response) => {
      registration.value = response.data.find((r) => r.event.code === evanEvent.value?.code) || null;
      loading.value = false;

      const reg = registration.value;
      if (reg?.is_accepted && !reg.no_show && evanEvent.value?.code) {
        fetchAlbums(evanEvent.value.code);
      }
    });
  }

  // Albums ------

  async function fetchAlbums(code: string) {
    api.get<Album[]>(`/events/${code}/albums/?include_photos=true`).then((response) => {
      albums.value = response.data;
    });
  }

  async function createRegistration(data: RegistrationData) {
    if (!evanEvent.value) return;
    await api
      .post<Registration>(`/events/${evanEvent.value?.code}/register/`, data)
      .then((response) => {
        registration.value = response.data;
      })
      .then(() => {
        notify.success(t('messages.registration_created'));
      });
  }

  async function updateRegistration(data: RegistrationData) {
    if (!registration.value) return;
    await api
      .put<Registration>(registration.value.self, data)
      .then((response) => {
        registration.value = response.data;
      })
      .then(() => {
        notify.success(t('messages.registration_updated'));
      });
  }

  // ------

  return {
    init,
    setData,
    setPreviewData,
    createRegistration,
    updateRegistration,
    loading,
    evanEvent,
    registration,
    albums,
  };
});
