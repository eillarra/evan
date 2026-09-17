import { createPinia, setActivePinia } from 'pinia';
import { beforeEach, describe, expect, it, vi } from 'vitest';
import { createApp, defineComponent, h } from 'vue';

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

// The store registers an onMounted lifecycle hook, so it must be created
// during component setup. Mounting a dummy component provides that context
// and lets the clock cleanup run on unmount.
function useStoreInSetup() {
  let store!: ReturnType<typeof useCommonStore>;
  const app = createApp(
    defineComponent({
      setup() {
        store = useCommonStore();
        return () => h('div');
      },
    }),
  );
  app.mount(document.createElement('div'));
  return { store, app };
}

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

      const { store, app } = useStoreInSetup();
      await store.init();

      expect(store.countries).toEqual(cached);
      expect(apiGet).not.toHaveBeenCalled();
      expect(storageSet).not.toHaveBeenCalled();
      app.unmount();
    });

    it('fetches from the API and stores the result with a 1-hour ttl on cache miss', async () => {
      const fetched = { BE: 'Belgium', FR: 'France' };
      storageGet.mockReturnValue(null);
      apiGet.mockResolvedValue({ data: fetched });

      const { store, app } = useStoreInSetup();
      await store.init();

      expect(store.countries).toEqual(fetched);
      expect(apiGet).toHaveBeenCalledWith('../countries/');
      expect(storageSet).toHaveBeenCalledWith('countries', fetched, 3600);
      app.unmount();
    });
  });

  describe('setTitle', () => {
    it('updates the title ref', () => {
      const { store, app } = useStoreInSetup();
      store.setTitle('My Event');

      expect(store.title).toBe('My Event');
      app.unmount();
    });

    it('has a default title of Evan', () => {
      const { store, app } = useStoreInSetup();
      expect(store.title).toBe('Evan');
      app.unmount();
    });
  });
});
