import { computed, onScopeDispose, ref, shallowRef } from 'vue';
import { useI18n } from 'vue-i18n';
import { defineStore } from 'pinia';

import { api } from '@/axios.ts';
import { confirm } from '@/utils/dialog';
import { notify } from '@/utils/notify';
import { tags_to_dict } from '@/utils/tags.ts';

export const useStore = defineStore('evanEvent', () => {
  const emails = shallowRef<Email[]>([]);
  const evanEvent = ref<ManagedEvanEvent | null>(null);
  const contents = ref<Content[]>([]);
  const coupons = ref<Coupon[]>([]);
  const keynotes = ref<Keynote[]>([]);
  const papers = ref<Paper[]>([]);
  const registrations = ref<Registration[]>([]);
  const sessions = ref<Session[]>([]);
  const venues = ref<Venue[]>([]);

  const { t } = useI18n();

  let refetchTimeoutId: NodeJS.Timeout | null = null;

  onScopeDispose(() => {
    if (refetchTimeoutId) {
      clearTimeout(refetchTimeoutId);
      refetchTimeoutId = null;
    }
  });

  async function setData(inertiaEvanEvent: ManagedEvanEvent) {
    evanEvent.value = inertiaEvanEvent;
    await init();
  }

  async function init() {
    await refetch(true);
  }

  async function fecthProgramData() {
    await fetchSessions();
    await fetchKeynotes();
    await fetchPapers();
  }

  async function refetch(first?: boolean) {
    await fetchRegistrations();
    await fetchEmails();

    if (!first) {
      notify.info(t('messages.data_refreshed'));
    }

    if (refetchTimeoutId) {
      clearTimeout(refetchTimeoutId);
    }
    refetchTimeoutId = setTimeout(() => refetch(), 2 * 60 * 1000); // Refetch every 2 minutes
  }

  async function fetchEmails() {
    if (!evanEvent.value) {
      return;
    }

    await api.get(evanEvent.value.self + 'emails/').then((res) => {
      emails.value = res.data.map((obj: Email) => ({
        ...obj,
        // -----
        _tags_dict: tags_to_dict(obj.tags),
      }));
    });
  }

  // Event ------

  async function patchEvent(data: Partial<ManagedEvanEvent>): Promise<void> {
    if (!evanEvent.value) return;

    return api.patch(evanEvent.value.self, data);
  }

  async function updateEvent(): Promise<void> {
    if (!evanEvent.value) return;

    return api.put(evanEvent.value.self, evanEvent.value).then(() => {
      notify.success(t('messages.event_updated'));
    });
  }

  async function updateEventPartial(data: Partial<ManagedEvanEvent>): Promise<void> {
    if (!evanEvent.value) return;

    return api.patch(evanEvent.value.self, data).then(() => {
      // Update the local state with the new data
      Object.assign(evanEvent.value!, data);
      notify.success(t('messages.event_updated'));
    });
  }

  async function updateBadgeConfig(badgesConfig: BadgesConfig): Promise<void> {
    if (!evanEvent.value) return;

    const currentExtraData = evanEvent.value.extra_data || { important_dates: [] };
    const extraData = {
      extra_data: {
        ...currentExtraData,
        badges: badgesConfig,
      },
    };

    await patchEvent(extraData);

    // Update local state
    if (evanEvent.value.extra_data) {
      evanEvent.value.extra_data.badges = badgesConfig;
    } else {
      evanEvent.value.extra_data = { important_dates: [], badges: badgesConfig };
    }
  }

  // Contents ------

  async function fetchContents() {
    if (!evanEvent.value) {
      return;
    }

    await api.get(evanEvent.value.self + 'contents/').then((res) => {
      contents.value = res.data;
    });
  }

  async function updateContent(content: Content, data: Partial<Content>) {
    return api.patch(content.self, data).then((res) => {
      const index = contents.value.findIndex((c) => c.id === content.id);
      contents.value[index] = res.data;
      notify.success(t('messages.content_updated'));
    });
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

  // Papers ------

  async function createPaper(data: PaperData) {
    if (!evanEvent.value) return;

    return api.post(evanEvent.value.self + 'papers/', data).then((res) => {
      papers.value.push(res.data);
      notify.success(t('messages.paper_created'));
      return res;
    });
  }

  async function fetchPapers() {
    if (!evanEvent.value) return;

    return await api.get(evanEvent.value.self + 'papers/').then((res) => {
      papers.value = res.data;
    });
  }

  async function updatePaper(paper: Paper) {
    return await api.put(paper.self, paper).then((res) => {
      const index = papers.value.findIndex((s) => s.id === paper.id);
      papers.value[index] = res.data;
      notify.success(t('messages.paper_updated'));
      return res;
    });
  }

  function removePaper(session: Paper) {
    confirm(t('messages.paper_confirm_delete'), () => {
      api.delete(session.self).then(() => {
        papers.value = papers.value.filter((s) => s.id !== session.id);
        notify.success(t('messages.paper_deleted'));
      });
    });
  }

  // Keynotes ------

  async function createKeynote(data: KeynoteData) {
    if (!evanEvent.value) return;

    return api.post(evanEvent.value.self + 'keynotes/', data).then((res) => {
      keynotes.value.push(res.data);
      notify.success(t('messages.keynote_created'));
      return res;
    });
  }

  async function fetchKeynotes() {
    if (!evanEvent.value) return;

    return await api.get(evanEvent.value.self + 'keynotes/').then((res) => {
      keynotes.value = res.data;
    });
  }

  async function updateKeynote(keynote: Keynote) {
    return await api.put(keynote.self, keynote).then((res) => {
      const index = keynotes.value.findIndex((s) => s.id === keynote.id);
      keynotes.value[index] = res.data;
      notify.success(t('messages.keynote_updated'));
      return res;
    });
  }

  function removeKeynote(keynote: Keynote) {
    confirm(t('messages.keynote_confirm_delete'), () => {
      api.delete(keynote.self).then(() => {
        keynotes.value = keynotes.value.filter((s) => s.id !== keynote.id);
        notify.success(t('messages.keynote_deleted'));
      });
    });
  }

  // Registrations ------

  async function fetchRegistrations() {
    if (!evanEvent.value) {
      return;
    }

    await api.get(evanEvent.value.self + 'registrations/').then((res) => {
      registrations.value = res.data.map((obj: Registration) => ({
        ...obj,
        // -----
        _tags_dict: tags_to_dict(obj.tags),
      }));
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
    return await api.put(session.self, session).then(async (res) => {
      const index = sessions.value.findIndex((s) => s.id === session.id);
      sessions.value[index] = res.data;
      notify.success(t('messages.session_updated'));

      // Refetch keynotes and papers since program template might have assigned items
      if (session.program) {
        await Promise.all([fetchKeynotes(), fetchPapers()]);
      }

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

  // Subsessions ------

  async function createSubsession(sessionId: number, data: SubsessionData) {
    const sessionIndex = sessions.value.findIndex((s) => s.id === sessionId);
    if (sessionIndex === -1) return;

    const session = sessions.value[sessionIndex];
    return api.post(session.self + 'subsessions/', data).then((res) => {
      const currentSubsessions = session.subsessions || [];
      // Ensure the subsession has the session ID
      const subsessionWithSessionId = { ...res.data, session: sessionId };
      const newSubsessions = [...currentSubsessions, subsessionWithSessionId].sort((a, b) => a.order - b.order);

      // Replace the session object to trigger reactivity
      sessions.value[sessionIndex] = {
        ...session,
        subsessions: newSubsessions,
      };

      notify.success(t('messages.subsession_created'));
      return res;
    });
  }

  async function updateSubsession(subsession: Subsession) {
    return await api.put(subsession.self, subsession).then(async (res) => {
      // If subsession.session is not set, we need to find it by searching all sessions
      let sessionIndex = -1;
      if (subsession.session) {
        sessionIndex = sessions.value.findIndex((s) => s.id === subsession.session);
      } else {
        // Find the session that contains this subsession
        for (let i = 0; i < sessions.value.length; i++) {
          if (sessions.value[i].subsessions?.some((sub) => sub.id === subsession.id)) {
            sessionIndex = i;
            break;
          }
        }
      }

      if (sessionIndex !== -1 && sessions.value[sessionIndex].subsessions) {
        const session = sessions.value[sessionIndex];
        const subsessionIndex = session.subsessions!.findIndex((sub) => sub.id === subsession.id);

        if (subsessionIndex !== -1) {
          const newSubsessions = [...session.subsessions!];
          // Ensure the updated subsession has the session ID
          newSubsessions[subsessionIndex] = { ...res.data, session: session.id };
          newSubsessions.sort((a, b) => a.order - b.order);

          // Replace the session object to trigger reactivity
          sessions.value[sessionIndex] = {
            ...session,
            subsessions: newSubsessions,
          };
        }
      }

      notify.success(t('messages.subsession_updated'));

      // Refetch keynotes and papers since program template might have assigned items
      if (subsession.program) {
        await Promise.all([fetchKeynotes(), fetchPapers()]);
      }

      return res;
    });
  }

  function removeSubsession(subsession: Subsession) {
    confirm(t('messages.subsession_confirm_delete'), () => {
      api.delete(subsession.self).then(() => {
        console.log('test', subsession.session);
        // If subsession.session is not set, we need to find it by searching all sessions
        let sessionIndex = -1;
        if (subsession.session) {
          sessionIndex = sessions.value.findIndex((s) => s.id === subsession.session);
        } else {
          // Find the session that contains this subsession
          for (let i = 0; i < sessions.value.length; i++) {
            if (sessions.value[i].subsessions?.some((sub) => sub.id === subsession.id)) {
              sessionIndex = i;
              break;
            }
          }
        }

        if (sessionIndex !== -1 && sessions.value[sessionIndex].subsessions) {
          const session = sessions.value[sessionIndex];

          // Create a new session object with updated subsessions
          const updatedSession = {
            ...session,
            subsessions: session.subsessions!.filter((sub) => sub.id !== subsession.id),
          };

          // Replace the session in the array to trigger reactivity
          sessions.value[sessionIndex] = updatedSession;
        }
        notify.success(t('messages.subsession_deleted'));
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

  // Venues ------

  function sortVenues() {
    if (!evanEvent.value) return;
    evanEvent.value.venues = evanEvent.value.venues.slice().sort((a, b) => {
      if (a.is_main !== b.is_main) {
        return a.is_main ? -1 : 1;
      }
      return a.name.localeCompare(b.name);
    });
  }

  async function createVenue(data: VenueData) {
    if (!evanEvent.value) return;

    return api.post(evanEvent.value.self + 'venues/', data).then((res) => {
      if (!evanEvent.value) return;

      // If this new venue is being set as main, update other venues to not be main
      if (res.data.is_main) {
        evanEvent.value.venues.forEach((v) => {
          v.is_main = false;
        });
      }

      evanEvent.value.venues.push(res.data);
      sortVenues();
      notify.success(t('messages.venue_created'));
      return res;
    });
  }

  async function updateVenue(venue: Venue) {
    return await api.put(venue.self, venue).then((res) => {
      if (!evanEvent.value) return;

      // If this venue is being set as main, update other venues to not be main
      if (res.data.is_main) {
        evanEvent.value.venues.forEach((v) => {
          if (v.id !== venue.id) {
            v.is_main = false;
          }
        });
      }

      const index = evanEvent.value.venues.findIndex((v) => v.id === venue.id);
      evanEvent.value.venues[index] = res.data;
      sortVenues();
      notify.success(t('messages.venue_updated'));
      return res;
    });
  }

  function removeVenue(venue: Venue) {
    confirm(t('messages.venue_confirm_delete'), () => {
      api.delete(venue.self).then(() => {
        if (!evanEvent.value) return;
        evanEvent.value.venues = evanEvent.value.venues.filter((v) => v.id !== venue.id);
        notify.success(t('messages.venue_deleted'));
      });
    });
  }

  // Rooms ------

  async function createRoom(data: RoomData) {
    if (!evanEvent.value) return;

    return api.post(evanEvent.value.self + 'rooms/', data).then((res) => {
      if (!evanEvent.value) return;
      const venueIndex = evanEvent.value.venues.findIndex((v) => v.id === data.venue);
      if (venueIndex !== -1) {
        evanEvent.value.venues[venueIndex].rooms.push(res.data);
        evanEvent.value.venues[venueIndex].rooms.sort((a, b) => a.position - b.position);
      }
      notify.success(t('messages.room_created'));
      return res;
    });
  }

  async function updateRoom(room: Room) {
    return await api.put(room.self, room).then((res) => {
      if (!evanEvent.value) return;
      for (const venue of evanEvent.value.venues) {
        const roomIndex = venue.rooms.findIndex((r) => r.id === room.id);
        if (roomIndex !== -1) {
          venue.rooms[roomIndex] = res.data;
          venue.rooms.sort((a, b) => a.position - b.position);
          break;
        }
      }
      notify.success(t('messages.room_updated'));
      return res;
    });
  }

  function removeRoom(room: Room) {
    confirm(t('messages.room_confirm_delete'), () => {
      api.delete(room.self).then(() => {
        if (!evanEvent.value) return;
        for (const venue of evanEvent.value.venues) {
          const roomIndex = venue.rooms.findIndex((r) => r.id === room.id);
          if (roomIndex !== -1) {
            venue.rooms.splice(roomIndex, 1);
            break;
          }
        }
        notify.success(t('messages.room_deleted'));
      });
    });
  }

  // Sessions Options ------

  const sessionOptions = computed<QuasarSelectOption[]>(() => {
    if (!sessions.value) return [];

    return sessions.value
      .sort((a, b) => (a.code || '').localeCompare(b.code || ''))
      .map((session) => ({
        value: session.id,
        label: session.code || session.title,
      }));
  });

  return {
    init,
    setData,
    createCoupon,
    createKeynote,
    createPaper,
    createSession,
    createSubsession,
    createTopic,
    createTrack,
    createVenue,
    createRoom,
    fetchContents,
    fetchCoupons,
    fetchKeynotes,
    fetchPapers,
    fetchRegistrations,
    fetchSessions,
    fecthProgramData,
    patchEvent,
    updateEvent,
    updateEventPartial,
    updateBadgeConfig,
    updateContent,
    updateCoupon,
    updateKeynote,
    updatePaper,
    updateSession,
    updateSubsession,
    updateTopic,
    updateTrack,
    updateVenue,
    updateRoom,
    removeCoupon,
    removeKeynote,
    removePaper,
    removeSession,
    removeSubsession,
    removeTopic,
    removeTrack,
    removeVenue,
    removeRoom,
    evanEvent,
    contents,
    coupons,
    couponIdsUsed,
    emails,
    keynotes,
    papers,
    registrations,
    sessions,
    venues,
    topicOptions,
    trackOptions,
    sessionOptions,
  };
});
