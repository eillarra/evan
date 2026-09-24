import { describe, it, expect, vi } from 'vitest';
import { reactive } from 'vue';
import { mount } from '@vue/test-utils';
import { createI18n } from 'vue-i18n';

import PublicEventApp from '../PublicEventApp.vue';

const mockPageProps = reactive<{ event: Partial<EvanEvent>; can_manage: boolean }>({
  event: {},
  can_manage: false,
});

vi.mock('@inertiajs/vue3', () => ({
  usePage: () => ({ props: mockPageProps }),
}));

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      public_event: {
        register: 'Register',
        manage: 'Manage event',
        contact: 'Contact',
      },
    },
  },
} as any);

const ALL_MODULES_OFF: EventModules = {
  payments: false,
  content: false,
  program: false,
  papers: false,
  communications: false,
};

const STUBS = {
  'marked-div': {
    template: '<div class="marked-div-stub">{{ text }}</div>',
    props: ['text'],
  },
  'ugent-btn': {
    template: '<a class="ugent-btn-stub" v-if="label" :href="href">{{ label }}</a>',
    props: ['label', 'href'],
  },
  'ugent-banner': {
    template: '<div class="ugent-banner-stub"><h1>{{ title }}</h1><h2>{{ subtitle }}</h2><slot /></div>',
    props: ['title', 'subtitle'],
  },
  'q-responsive': true,
};

function makeEvent(overrides: Partial<EvanEvent> = {}): EvanEvent {
  return {
    code: 'FEARS26',
    name: 'FEARS',
    full_name: 'Forum for Engineering, Architecture & Science',
    city: 'Ghent',
    country: { code: 'BE', name: 'Belgium' },
    presentation: 'A great event.',
    website: 'https://example.com',
    email: 'organizer@example.com',
    dates_display: 'September 24-26, 2026',
    registration_url: '/r/FEARS26/',
    manage_url: '/e/FEARS26/manage/',
    modules: { ...ALL_MODULES_OFF },
    registration_audience: 'public',
    listing_status: 'listed',
    decline_reason: '',
    is_listed: true,
    url: '/e/FEARS26/',
    fees: [],
    ...overrides,
  } as unknown as EvanEvent;
}

function mountApp() {
  return mount(PublicEventApp, {
    global: { stubs: STUBS, plugins: [i18n] },
  });
}

describe('PublicEventApp', () => {
  it('renders the core event identity', () => {
    mockPageProps.event = makeEvent();

    const wrapper = mountApp();

    expect(wrapper.text()).toContain('FEARS');
    expect(wrapper.text()).toContain('Forum for Engineering, Architecture & Science');
    expect(wrapper.text()).toContain('September 24-26, 2026');
    expect(wrapper.text()).toContain('Ghent, Belgium');
    expect(wrapper.text()).toContain('organizer@example.com');
  });

  it('renders the presentation markdown', () => {
    mockPageProps.event = makeEvent();

    const wrapper = mountApp();

    expect(wrapper.find('.marked-div-stub').text()).toContain('A great event.');
  });

  it('shows the registration CTA when the event is open for registration', () => {
    mockPageProps.event = makeEvent();

    const wrapper = mountApp();

    const cta = wrapper.find('.ugent-btn-stub');
    expect(cta.attributes('href')).toBe('/r/FEARS26/');
    expect(cta.text()).toBe('Register');
  });

  it('hides the registration CTA when registration is not open', () => {
    mockPageProps.event = makeEvent({ registration_url: '' });

    const wrapper = mountApp();

    expect(wrapper.text()).not.toContain('Register');
  });

  it('shows the Manage link only to managers', () => {
    mockPageProps.event = makeEvent();
    mockPageProps.can_manage = false;
    expect(mountApp().text()).not.toContain('Manage event');

    mockPageProps.can_manage = true;
    const manageLink = mountApp()
      .findAll('.ugent-btn-stub')
      .find((btn) => btn.text() === 'Manage event');
    expect(manageLink?.attributes('href')).toBe('/e/FEARS26/manage/');
  });

  it('renders no module sections for a minimal event', () => {
    mockPageProps.event = makeEvent();
    mockPageProps.can_manage = false;

    const wrapper = mountApp();

    // V1 public page is display-only: no payments, program, papers or content sections.
    expect(wrapper.text()).not.toContain('Fees');
    expect(wrapper.text()).not.toContain('Program');
    expect(wrapper.text()).not.toContain('Sponsors');
  });
});
