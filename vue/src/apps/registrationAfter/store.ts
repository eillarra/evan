import { ref, shallowRef } from 'vue';
import { defineStore } from 'pinia';

import { api } from '@/axios.ts';

export const useStore = defineStore('evanSession', () => {
  const loading = ref<boolean>(true);
  const evanEvent = shallowRef<EvanEvent | null>(null);
  const registration = shallowRef<Registration | null>(null);

  async function setData(inertiaEvanEvent: EvanEvent) {
    evanEvent.value = inertiaEvanEvent;
    await init();
  }

  async function init() {
    await getRegistrations();
  }

  // Registration ------

  async function getRegistrations() {
    api.get<Registration[]>('/user/registrations/').then((response) => {
      registration.value =
        response.data.find((registration) => registration.event.code === evanEvent.value?.code) || null;
      loading.value = false;
    });
  }

  // ------

  return {
    init,
    setData,
    loading,
    evanEvent,
    registration,
  };
});
