import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const storageGet = vi.fn();
const storageSet = vi.fn();

vi.mock('@/utils/storage', () => ({
  storage: {
    get: (k: string) => storageGet(k),
    set: (k: string, v: unknown, ttl?: number) => storageSet(k, v, ttl),
  },
}));

const apiGet = vi.fn();

vi.mock('@/axios', () => ({
  api: {
    get: (url: string) => apiGet(url),
  },
}));

import { useCommonStore } from '../common';

describe('useCommonStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    storageGet.mockReset();
    storageSet.mockReset();
    apiGet.mockReset();
  });

  describe('init (country loading)', () => {
    it('uses the cached value from storage without hitting the API', async () => {
      const cached = { BE: 'Belgium', NL: 'Netherlands' };
      storageGet.mockReturnValue(cached);

      const store = useCommonStore();
      await store.init();

      expect(store.countries).toEqual(cached);
      expect(apiGet).not.toHaveBeenCalled();
      expect(storageSet).not.toHaveBeenCalled();
    });

    it('fetches from the API and stores the result with a 1-hour ttl on cache miss', async () => {
      const fetched = { BE: 'Belgium', FR: 'France' };
      storageGet.mockReturnValue(null);
      apiGet.mockResolvedValue({ data: fetched });

      const store = useCommonStore();
      await store.init();

      expect(store.countries).toEqual(fetched);
      expect(apiGet).toHaveBeenCalledWith('../countries/');
      expect(storageSet).toHaveBeenCalledWith('countries', fetched, 3600);
    });
  });

  describe('setTitle', () => {
    it('updates the title ref', () => {
      const store = useCommonStore();
      store.setTitle('My Event');

      expect(store.title).toBe('My Event');
    });

    it('has a default title of Evan', () => {
      const store = useCommonStore();
      expect(store.title).toBe('Evan');
    });
  });
});
