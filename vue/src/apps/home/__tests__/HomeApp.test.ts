import { describe, it, expect, vi } from 'vitest';
import { reactive } from 'vue';
import { mount } from '@vue/test-utils';
import { createI18n } from 'vue-i18n';

import HomeApp from '../HomeApp.vue';

const mockPageProps = reactive<{ django_user: DjangoAuthenticatedUser | null; events: EvanEvent[] }>({
  django_user: null,
  events: [],
});

vi.mock('@inertiajs/vue3', () => ({
  usePage: () => ({ props: mockPageProps }),
}));

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      home: {
        presentation: 'Event assistant',
        login: 'Sign in',
        upcoming_events: 'Upcoming events',
      },
      user_menu: { dashboard: 'My dashboard' },
    },
  },
} as any);

const STUBS = {
  'ugent-btn': {
    template: '<a class="ugent-btn-stub" v-if="label">{{ label }}</a>',
    props: ['label'],
  },
  'ugent-banner': {
    template: '<div class="ugent-banner-stub"><slot /></div>',
  },
  'q-list': { template: '<ul class="q-list-stub"><slot /></ul>' },
  'q-item': {
    template: '<li class="q-item-stub" :href="href"><slot /></li>',
    props: ['clickable', 'href'],
  },
  'q-item-section': { template: '<div class="q-item-section-stub"><slot /></div>' },
  'q-item-label': { template: '<div class="q-item-label-stub"><slot /></div>' },
  'q-responsive': true,
};

function makeEvent(code: string, name: string): EvanEvent {
  return {
    code,
    name,
    full_name: `${name} full name`,
    city: 'Ghent',
  } as unknown as EvanEvent;
}

function mountApp() {
  return mount(HomeApp, { global: { stubs: STUBS, plugins: [i18n] } });
}

describe('HomeApp', () => {
  it('renders the listing section when upcoming listed events exist', () => {
    mockPageProps.events = [makeEvent('FEARS26', 'FEARS'), makeEvent('WURTL26', 'WURTL')];

    const wrapper = mountApp();

    expect(wrapper.text()).toContain('Upcoming events');
    expect(wrapper.text()).toContain('FEARS');
    expect(wrapper.text()).toContain('WURTL');
    expect(wrapper.find('[href="/e/FEARS26/"]').exists()).toBe(true);
  });

  it('hides the listing section when no upcoming events exist', () => {
    mockPageProps.events = [];

    const wrapper = mountApp();

    expect(wrapper.text()).not.toContain('Upcoming events');
  });
});
