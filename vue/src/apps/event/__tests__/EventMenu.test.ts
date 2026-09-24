import { describe, it, expect, vi } from 'vitest';
import { reactive } from 'vue';
import { mount } from '@vue/test-utils';
import { createI18n } from 'vue-i18n';

import EventMenu from '../EventMenu.vue';

const mockPageProps = reactive<{ event: Partial<ManagedEvanEvent> }>({ event: {} });

vi.mock('@inertiajs/vue3', () => ({
  usePage: () => ({ props: mockPageProps }),
}));

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      overview: 'Overview',
      event_management: 'Event management',
      stats: 'Stats',
      send_emails: 'Send emails',
      album: 'Photo album | Photo albums',
      models: {
        registration: 'Registration | Registrations',
        coupon: 'Coupon | Coupons',
        event: 'Event | Events',
        important_date: 'Important date | Important dates',
        session: 'Session | Sessions',
        keynote: 'Keynote | Keynotes',
        paper: 'Paper | Papers',
        content: 'Content | Contents',
        sponsor: 'Sponsor | Sponsors',
        venue: 'Venue | Venues',
        venues_rooms: 'Venues & rooms',
        tracks_topics: 'Tracks & topics',
      },
      fields: { email: 'Email | Emails' },
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
  'q-scroll-area': { template: '<div class="q-scroll-area-stub"><slot /></div>' },
  'q-list': { template: '<div class="q-list-stub"><slot /></div>' },
  'q-item': {
    template: `<div class="q-item-stub" :data-to="(to && to.name) || ''"><slot /></div>`,
    props: ['clickable', 'to'],
  },
  'q-item-label': { template: '<div class="q-item-label-stub"><slot /></div>' },
  'q-item-section': {
    template: '<div class="q-item-section-stub"><slot /></div>',
  },
  'q-icon': true,
};

function setModules(modules: EventModules) {
  mockPageProps.event = { modules } as ManagedEvanEvent;
}

function mountMenu() {
  return mount(EventMenu, {
    global: {
      stubs: STUBS,
      plugins: [i18n],
      config: { globalProperties: { $q: { screen: { gt: { sm: false } } } } },
    },
  });
}

function routeNames(wrapper: ReturnType<typeof mount>): string[] {
  return wrapper.findAll('.q-item-stub').map((item) => item.attributes('data-to'));
}

describe('EventMenu', () => {
  it('shows only core sections when all modules are disabled', () => {
    setModules({ ...ALL_MODULES_OFF });

    const routes = routeNames(mountMenu());

    expect(routes).toContain('stats');
    expect(routes).toContain('registrations');
    expect(routes).toContain('event');
    expect(routes).toContain('dates');
    expect(routes).toContain('emails');
    expect(routes).not.toContain('coupons');
    expect(routes).not.toContain('venues');
    expect(routes).not.toContain('taxonomy');
    expect(routes).not.toContain('sessions');
    expect(routes).not.toContain('keynotes');
    expect(routes).not.toContain('papers');
    expect(routes).not.toContain('emailplans');
    expect(routes).not.toContain('contents');
    expect(routes).not.toContain('sponsors');
    expect(routes).not.toContain('albums');
  });

  it('shows a module section when its module is enabled', () => {
    setModules({ ...ALL_MODULES_OFF, payments: true, papers: true, communications: true });

    const routes = routeNames(mountMenu());

    expect(routes).toContain('coupons');
    expect(routes).toContain('papers');
    expect(routes).toContain('emailplans');
  });

  it('shows program and content sections when those modules are enabled', () => {
    setModules({ ...ALL_MODULES_OFF, program: true, content: true });

    const routes = routeNames(mountMenu());

    expect(routes).toContain('venues');
    expect(routes).toContain('taxonomy');
    expect(routes).toContain('sessions');
    expect(routes).toContain('keynotes');
    expect(routes).toContain('contents');
    expect(routes).toContain('sponsors');
    expect(routes).toContain('albums');
  });

  it('renders no module-specific entries when the event prop carries no modules', () => {
    mockPageProps.event = {} as ManagedEvanEvent;

    const routes = routeNames(mountMenu());

    expect(routes).not.toContain('coupons');
    expect(routes).not.toContain('sessions');
    expect(routes).toContain('stats');
  });
});
