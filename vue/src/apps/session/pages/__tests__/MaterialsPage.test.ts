import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';

const { mockGet } = vi.hoisted(() => ({
  mockGet: vi.fn(),
}));

mockGet.mockResolvedValue({ data: [] });

vi.mock('@/axios.ts', () => ({
  api: { get: mockGet, post: vi.fn(), delete: vi.fn() },
}));

vi.mock('@/utils/dialog', () => ({ confirm: vi.fn() }));
vi.mock('@/utils/notify', () => ({ notify: { success: vi.fn(), error: vi.fn() } }));

// The store calls useI18n() when it is created, which needs a component
// context; a plain stub keeps the store usable outside a component.
vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}));

import MaterialsPage from '../MaterialsPage.vue';
import { useStore } from '../../store';

describe('Session MaterialsPage', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
    mockGet.mockClear();
    mockGet.mockResolvedValue({ data: [] });
  });

  it('lists the session materials through the secret', async () => {
    const pinia = createPinia();
    setActivePinia(pinia);
    const store = useStore();
    store.setData(
      { code: 'ev', name: 'Event' } as EvanEvent,
      { id: 7, rel_files: '/api/v1/rel/30/7/files/' } as Session,
      'the-secret',
    );

    const wrapper = mount(MaterialsPage, {
      global: {
        plugins: [pinia],
        mocks: { $t: (key: string) => key },
        stubs: {
          NoResults: true,
          'q-markup-table': { template: '<table><tbody><slot /></tbody></table>' },
          'q-btn': { template: '<button><slot /></button>' },
          'q-space': true,
          'q-dialog': true,
          'q-file': true,
          'q-select': true,
          'q-input': true,
        },
      },
    });
    await flushPromises();

    expect(mockGet).toHaveBeenCalledWith(
      '/api/v1/rel/30/7/files/',
      expect.objectContaining({ headers: { 'X-Evan-Secret': 'the-secret' } }),
    );
    expect(wrapper.exists()).toBe(true);
  });
});
