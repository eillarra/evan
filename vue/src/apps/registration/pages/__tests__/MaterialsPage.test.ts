import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { reactive } from 'vue';
import { createI18n } from 'vue-i18n';

const mockPageProps = reactive<{ sessions: Session[] }>({ sessions: [] });

vi.mock('@inertiajs/vue3', () => ({
  usePage: () => ({ props: mockPageProps }),
}));

import MaterialsPage from '../MaterialsPage.vue';

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      models: { materials: 'Materials' },
    },
  },
} as any);

const makeSession = (id: number, title: string, files: Partial<RelatedFile>[]): Session =>
  ({
    id,
    title,
    files: files.map((file, index) => ({
      id: index + 1,
      self: `/api/v1/rel/30/${id}/files/${index + 1}/`,
      file: `/media/files/30/${id}/slides.pdf`,
      visibility: 'attendees',
      description: 'Slides',
      tags: [],
      ...file,
    })),
  }) as unknown as Session;

const mountPage = () =>
  mount(MaterialsPage, {
    global: {
      plugins: [i18n],
      stubs: {
        NoResults: { template: '<div class="no-results" />' },
        'q-markup-table': { template: '<table><tbody><slot /></tbody></table>' },
      },
    },
  });

describe('Registration MaterialsPage', () => {
  beforeEach(() => {
    mockPageProps.sessions = [];
  });

  it('shows an empty state when the event has no session materials', async () => {
    mockPageProps.sessions = [makeSession(1, 'Keynote', [])];

    const wrapper = mountPage();
    await flushPromises();

    expect(wrapper.find('.no-results').exists()).toBe(true);
  });

  it('lists the materials of every session', async () => {
    mockPageProps.sessions = [
      makeSession(1, 'Keynote', [{ description: 'Keynote slides' }]),
      makeSession(2, 'Workshop', [{ description: 'Workshop handout' }]),
    ];

    const wrapper = mountPage();
    await flushPromises();

    expect(wrapper.text()).toContain('Keynote');
    expect(wrapper.text()).toContain('Keynote slides');
    expect(wrapper.text()).toContain('Workshop');
    expect(wrapper.text()).toContain('Workshop handout');
  });

  it('links each material to its download URL', async () => {
    mockPageProps.sessions = [makeSession(1, 'Keynote', [{ description: 'Keynote slides' }])];

    const wrapper = mountPage();
    await flushPromises();

    expect(wrapper.find('a').attributes('href')).toBe('/media/files/30/1/slides.pdf');
  });
});
