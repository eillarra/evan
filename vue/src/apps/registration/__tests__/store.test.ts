import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiGet = vi.fn();
const apiPost = vi.fn();
const apiPut = vi.fn();
const notifySuccess = vi.fn();

vi.mock('@/axios.ts', () => ({
  api: {
    get: (url: string) => apiGet(url),
    post: (url: string, data: unknown) => apiPost(url, data),
    put: (url: string, data: unknown) => apiPut(url, data),
  },
}));

vi.mock('@/utils/notify', () => ({
  notify: {
    success: (msg: string) => notifySuccess(msg),
  },
}));

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}));

import { useStore } from '../store';

describe('useStore (registration)', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    apiGet.mockReset();
    apiPost.mockReset();
    apiPut.mockReset();
    notifySuccess.mockReset();
  });

  describe('getRegistrations (via setData → init)', () => {
    it('sets the registration matching the event code and clears loading', async () => {
      const event = { code: 'EV2026' } as unknown as EvanEvent;
      const matchingReg = { event: { code: 'EV2026' }, is_accepted: false, no_show: false } as unknown as Registration;
      const otherReg = { event: { code: 'OTHER' }, is_accepted: false, no_show: false } as unknown as Registration;

      const store = useStore();
      apiGet.mockResolvedValue({ data: [otherReg, matchingReg] });

      await store.setData(event);

      expect(store.registration).toEqual(matchingReg);
      expect(store.loading).toBe(false);
      expect(apiGet).toHaveBeenCalledTimes(1);
    });

    it('fetches albums when the registration is accepted and not no_show', async () => {
      const event = { code: 'EV2026' } as unknown as EvanEvent;
      const matchingReg = {
        event: { code: 'EV2026' },
        is_accepted: true,
        no_show: false,
      } as unknown as Registration;

      const store = useStore();
      apiGet.mockImplementation((url: string) => {
        if (url === '/user/registrations/') {
          return Promise.resolve({ data: [matchingReg] });
        }
        if (url.startsWith('/events/') && url.endsWith('/albums/?include_photos=true')) {
          return Promise.resolve({ data: [] });
        }
        return Promise.resolve({ data: [] });
      });

      await store.setData(event);

      expect(apiGet).toHaveBeenCalledWith('/events/EV2026/albums/?include_photos=true');
    });

    it('does not fetch albums when the registration is no_show', async () => {
      const event = { code: 'EV2026' } as unknown as EvanEvent;
      const matchingReg = {
        event: { code: 'EV2026' },
        is_accepted: true,
        no_show: true,
      } as unknown as Registration;

      const store = useStore();
      apiGet.mockResolvedValue({ data: [matchingReg] });

      await store.setData(event);

      expect(apiGet).toHaveBeenCalledTimes(1);
    });

    it('sets registration to null when no matching event code is found', async () => {
      const event = { code: 'EV2026' } as unknown as EvanEvent;
      const otherReg = { event: { code: 'OTHER' }, is_accepted: false, no_show: false } as unknown as Registration;

      const store = useStore();
      apiGet.mockResolvedValue({ data: [otherReg] });

      await store.setData(event);

      expect(store.registration).toBeNull();
      expect(store.loading).toBe(false);
    });
  });

  describe('createRegistration', () => {
    it('POSTs to the event register URL and notifies on success', async () => {
      const event = { code: 'EV2026' } as unknown as EvanEvent;
      const created = { event: { code: 'EV2026' }, is_accepted: false } as unknown as Registration;

      const store = useStore();
      store.evanEvent = event;

      apiPost.mockResolvedValue({ data: created });

      await store.createRegistration({ first_name: 'Jane' } as unknown as RegistrationData);

      expect(apiPost).toHaveBeenCalledWith('/events/EV2026/register/', { first_name: 'Jane' });
      expect(store.registration).toEqual(created);
      expect(notifySuccess).toHaveBeenCalledWith('messages.registration_created');
    });

    it('early-returns when no event is set', async () => {
      const store = useStore();

      await store.createRegistration({} as RegistrationData);

      expect(apiPost).not.toHaveBeenCalled();
    });
  });

  describe('updateRegistration', () => {
    it('PUTs to the registration self URL and notifies on success', async () => {
      const existing = { self: '/registrations/42/', event: { code: 'EV2026' } } as unknown as Registration;
      const updated = { ...existing, first_name: 'Jane' } as unknown as Registration;

      const store = useStore();
      store.registration = existing;

      apiPut.mockResolvedValue({ data: updated });

      await store.updateRegistration({ first_name: 'Jane' } as unknown as RegistrationData);

      expect(apiPut).toHaveBeenCalledWith('/registrations/42/', { first_name: 'Jane' });
      expect(store.registration).toEqual(updated);
      expect(notifySuccess).toHaveBeenCalledWith('messages.registration_updated');
    });

    it('early-returns when no registration is set', async () => {
      const store = useStore();

      await store.updateRegistration({} as RegistrationData);

      expect(apiPut).not.toHaveBeenCalled();
    });
  });
});
