import { computed, ref, shallowRef } from 'vue';
import { useI18n } from 'vue-i18n';
import { defineStore } from 'pinia';

import { api } from '@/axios.ts';
import { notify } from '@/utils/notify';

export const useStore = defineStore('evanSession', () => {
  const evanEvent = shallowRef<EvanEvent | null>(null);
  const session = ref<Session | null>(null);
  const secret = ref<string | null>(null);

  const { t } = useI18n();

  async function setData(inertiaEvanEvent: EvanEvent, inertiaEvanSession: Session, inertiaSecret: string) {
    evanEvent.value = inertiaEvanEvent;
    session.value = inertiaEvanSession;
    secret.value = inertiaSecret;
    await init();
  }

  async function init() {}

  async function updateSession() {
    if (!session.value || !session.value.title) return;

    return api
      .put(session.value.self, session.value, {
        headers: {
          'X-Evan-Secret': secret.value,
        },
      })
      .then(() => {
        notify.success(t('messages.session_updated'));
      });
  }

  // Options ------

  const topicOptions = computed<QuasarSelectOption[]>(() => {
    if (!evanEvent.value) return [];

    return evanEvent.value.topics.map((topic) => ({
      value: topic.id,
      label: topic.name,
    }));
  });

  const trackName = computed<string>(() => {
    if (!evanEvent.value?.tracks || !session.value?.track) return '-';
    const track = evanEvent.value.tracks.find((t) => t.id === session.value?.track);
    return track ? track.name : '-';
  });

  // ------

  return {
    init,
    setData,
    updateSession,
    evanEvent,
    session,
    topicOptions,
    trackName,
  };
});
