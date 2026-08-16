import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const apiPatch = vi.fn();

vi.mock('@/axios', () => ({
  api: {
    patch: (url: string, data: unknown) => apiPatch(url, data),
  },
}));

import { useUserStore } from '../user';

describe('useUserStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    apiPatch.mockReset();
  });

  describe('setData', () => {
    it('sets the user and completes without error', async () => {
      const store = useUserStore();
      const inertiaUser = { id: 1, username: 'jane', self: '/users/1/' } as unknown as AuthenticatedUser;

      await store.setData(inertiaUser);

      expect(store.user).toEqual(inertiaUser);
    });
  });

  describe('updateUser', () => {
    it('early-returns when no user is set', async () => {
      const store = useUserStore();

      await store.updateUser({ first_name: 'Jane' });

      expect(apiPatch).not.toHaveBeenCalled();
    });

    it('PATCHes the user self URL and updates the user from the response', async () => {
      const store = useUserStore();
      const initial = { id: 1, username: 'jane', self: '/users/1/' } as unknown as AuthenticatedUser;
      await store.setData(initial);

      const updated = { ...initial, first_name: 'Jane' };
      apiPatch.mockResolvedValue({ data: updated });

      await store.updateUser({ first_name: 'Jane' });

      expect(apiPatch).toHaveBeenCalledWith('/users/1/', { first_name: 'Jane' });
      expect(store.user).toEqual(updated);
    });
  });
});
