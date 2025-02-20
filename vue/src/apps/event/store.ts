import { computed, ref } from 'vue';
import { useI18n } from 'vue-i18n';
import { defineStore } from 'pinia';

import { api } from '@/axios.ts';
import { confirm } from '@/utils/dialog';
import { notify } from '@/utils/notify';

export const useStore = defineStore('evanEvent', () => {
  const evanEvent = ref<ManagedEvanEvent | null>(null);
  const contents = ref<Content[]>([]);
  const coupons = ref<Coupon[]>([]);
  const registrations = ref<Registration[]>([]);
  const sessions = ref<Session[]>([]);

  const { t } = useI18n();

  async function setData(inertiaEvanEvent: ManagedEvanEvent) {
    evanEvent.value = inertiaEvanEvent;
    await init();
  }

  async function init() {
    await fetchRegistrations();
  }

  async function fetchContents() {
    contents.value = [];

    if (!evanEvent.value) {
      return;
    }

    await api.get(evanEvent.value.self + 'contents/').then((res) => {
      contents.value = res.data;
    });
  }

  // Event ------

  async function patchEvent(data: Partial<ManagedEvanEvent>): Promise<void> {
    if (!evanEvent.value) return;

    return api.patch(evanEvent.value.self, data);
  }

  // Coupons ------

  async function createCoupon(data: CouponData) {
    if (!evanEvent.value) return;

    return api.post(evanEvent.value.self + 'coupons/', data).then((res) => {
      coupons.value.push(res.data);
      notify.success(t('messages.coupon_created'));
      return res;
    });
  }

  async function fetchCoupons() {
    if (!evanEvent.value) return;

    coupons.value = [];

    return await api.get(evanEvent.value.self + 'coupons/').then((res) => {
      coupons.value = res.data;
    });
  }

  async function updateCoupon(coupon: Coupon) {
    return await api.put(coupon.self, coupon).then((res) => {
      const index = coupons.value.findIndex((c) => c.id === coupon.id);
      coupons.value[index] = res.data;
      notify.success(t('messages.coupon_updated'));
      return res;
    });
  }

  function removeCoupon(coupon: Coupon) {
    const msg = couponIdsUsed.value.has(coupon.id)
      ? t('messages.coupon_confirm_delete_used')
      : t('messages.coupon_confirm_delete');

    confirm(msg, () => {
      api.delete(coupon.self).then(() => {
        coupons.value = coupons.value.filter((c) => c.id !== coupon.id);
        notify.success(t('messages.coupon_deleted'));
      });
    });
  }

  const couponIdsUsed = computed<Set<number>>(() => {
    const couponIds = new Set<number>();

    registrations.value.forEach((registration) => {
      if (registration.coupon) {
        couponIds.add(registration.coupon.id);
      }
    });

    return couponIds;
  });

  // Registrations ------

  async function fetchRegistrations() {
    registrations.value = [];

    if (!evanEvent.value) {
      return;
    }

    await api.get(evanEvent.value.self + 'registrations/').then((res) => {
      registrations.value = res.data;
    });
  }

  // Sessions ------

  async function createSession(data: SessionData) {
    if (!evanEvent.value) return;

    return api.post(evanEvent.value.self + 'sessions/', data).then((res) => {
      sessions.value.push(res.data);
      notify.success(t('messages.session_created'));
      return res;
    });
  }

  async function fetchSessions() {
    if (!evanEvent.value) return;

    return await api.get(evanEvent.value.self + 'sessions/').then((res) => {
      sessions.value = res.data;
    });
  }

  async function updateSession(session: Session) {
    return await api.put(session.self, session).then((res) => {
      const index = sessions.value.findIndex((s) => s.id === session.id);
      sessions.value[index] = res.data;
      notify.success(t('messages.session_updated'));
      return res;
    });
  }

  function removeSession(session: Session) {
    confirm(t('messages.session_confirm_delete'), () => {
      api.delete(session.self).then(() => {
        sessions.value = sessions.value.filter((s) => s.id !== session.id);
        notify.success(t('messages.session_deleted'));
      });
    });
  }

  // Topics ------

  function sortTopics() {
    if (!evanEvent.value) return;
    evanEvent.value.topics = evanEvent.value.topics.slice().sort((a, b) => a.name.localeCompare(b.name));
  }

  async function createTopic(data: TopicData) {
    if (!evanEvent.value) return;

    return api.post(evanEvent.value.self + 'topics/', data).then((res) => {
      if (!evanEvent.value) return; // so the editor doesn't complain
      evanEvent.value.topics.push(res.data);
      sortTopics();
      notify.success(t('messages.topic_created'));
      return res;
    });
  }

  async function updateTopic(topic: Topic) {
    return await api.put(topic.self, topic).then((res) => {
      if (!evanEvent.value) return; // so the editor doesn't complain
      const index = evanEvent.value.topics.findIndex((t) => t.id === topic.id);
      evanEvent.value.topics[index] = res.data;
      sortTopics();
      notify.success(t('messages.topic_updated'));
      return res;
    });
  }

  function removeTopic(topic: Topic) {
    confirm(t('messages.topic_confirm_delete'), () => {
      api.delete(topic.self).then(() => {
        if (!evanEvent.value) return; // so the editor doesn't complain
        evanEvent.value.topics = evanEvent.value.topics.filter((t) => t.id !== topic.id);
        notify.success(t('messages.topic_deleted'));
      });
    });
  }

  const topicOptions = computed<QuasarSelectOption[]>(() => {
    if (!evanEvent.value) return [];

    return evanEvent.value.topics.map((topic) => ({
      value: topic.id,
      label: topic.name,
    }));
  });

  // Tracks ------

  function sortTracks() {
    if (!evanEvent.value) return;
    evanEvent.value.tracks = evanEvent.value.tracks.slice().sort((a, b) => a.position - b.position);
  }

  async function createTrack(data: TrackData) {
    if (!evanEvent.value) return;

    return api.post(evanEvent.value.self + 'tracks/', data).then((res) => {
      if (!evanEvent.value) return; // so the editor doesn't complain
      evanEvent.value.tracks.push(res.data);
      sortTracks();
      notify.success(t('messages.track_created'));
      return res;
    });
  }

  async function updateTrack(track: Track) {
    return await api.put(track.self, track).then((res) => {
      if (!evanEvent.value) return; // so the editor doesn't complain
      const index = evanEvent.value.tracks.findIndex((t) => t.id === track.id);
      evanEvent.value.tracks[index] = res.data;
      sortTracks();
      notify.success(t('messages.track_updated'));
      return res;
    });
  }

  function removeTrack(track: Track) {
    confirm(t('messages.track_confirm_delete'), () => {
      api.delete(track.self).then(() => {
        if (!evanEvent.value) return; // so the editor doesn't complain
        evanEvent.value.tracks = evanEvent.value.tracks.filter((t) => t.id !== track.id);
        notify.success(t('messages.track_deleted'));
      });
    });
  }

  const trackOptions = computed<QuasarSelectOption[]>(() => {
    if (!evanEvent.value) return [];

    return evanEvent.value.tracks.map((track) => ({
      value: track.id,
      label: track.name,
    }));
  });

  // ------

  return {
    init,
    setData,
    createCoupon,
    createSession,
    createTopic,
    createTrack,
    fetchContents,
    fetchCoupons,
    fetchRegistrations,
    fetchSessions,
    patchEvent,
    updateCoupon,
    updateSession,
    updateTopic,
    updateTrack,
    removeCoupon,
    removeSession,
    removeTopic,
    removeTrack,
    evanEvent,
    contents,
    coupons,
    couponIdsUsed,
    registrations,
    sessions,
    topicOptions,
    trackOptions,
  };
});
