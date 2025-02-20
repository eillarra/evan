import { shallowRef } from 'vue';
import { useI18n } from 'vue-i18n';
import { defineStore } from 'pinia';

import { api } from '@/axios.ts';
import { notify } from '@/utils/notify';

export const useStore = defineStore('evanSession', () => {
  const evanEvent = shallowRef<EvanEvent | null>(null);
  const registration = shallowRef<Registration | null>(null);

  const { t } = useI18n();

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
    createRegistration,
    updateRegistration,
    evanEvent,
    registration,
  };
});
