import { describe, it, expect, vi, beforeEach } from 'vitest';
import { reactive, nextTick } from 'vue';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createI18n } from 'vue-i18n';

import RegistrationPage from '../RegistrationPage.vue';
import { useStore } from '../../store';
import { useUserStore } from '@/stores/user';

// --- Module mocks -----------------------------------------------------------

const mockPageProps = reactive<{ sessions: Session[]; preview: boolean }>({ sessions: [], preview: false });

vi.mock('@inertiajs/vue3', () => ({
  usePage: () => ({ props: mockPageProps }),
}));

vi.mock('@/axios.ts', () => ({
  api: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    patch: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

vi.mock('@/utils/notify', () => ({
  notify: { success: vi.fn(), error: vi.fn() },
}));

// --- Fixtures ----------------------------------------------------------------

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      fields: { name: 'Name', email: 'Email', affiliation: 'Affiliation', country: 'Country' },
      form: { update: 'Update', create: 'Create' },
      messages: { registration_created: 'Registered', registration_updated: 'Updated' },
    },
  },
} as any);

const makeFee = (type: string, isOnline: boolean): Fee => ({
  type,
  online_only: isOnline,
  value: 200,
  early_value: null,
  onsite_value: null,
  notes: `${type} fee`,
  config: { included_social_events: [] },
});

const makeEvent = (...fees: Fee[]) =>
  ({
    code: 'TEST26',
    is_virtual: false,
    fees,
    registration_configuration: { fee_selection: null, form_fields: [] },
    registration_early_deadline: '',
  }) as any;

const makeVirtualEvent = (...fees: Fee[]) =>
  ({
    ...makeEvent(...fees),
    is_virtual: true,
  }) as any;

const makeRegistration = (feeType: string): any => ({
  fee_type: feeType,
  sessions: [],
  extra_data: { _internal: { share_email_with_sponsors: false, allow_photo_sharing: true } },
  visa_requested: false,
});

const makeSocialSession = (): Session =>
  ({
    id: 1,
    is_social_event: true,
    title: 'Gala Dinner',
    start_at: '2026-09-01T19:00:00',
    extra_attendees_fee: 50,
    slug: 'gala-dinner',
    code: 'GALA',
    description: '',
    extra_data: { committees: [], important_dates: [] },
  }) as any;

const mockUser: any = {
  first_name: 'Test',
  last_name: 'User',
  email: 'test@test.com',
  affiliation: 'UGent',
  country: 'BE',
  self: '/api/users/1/',
  extra_data: {},
};

// --- Test helpers -----------------------------------------------------------

/**
 * Stubs for all child components and Quasar components.
 * evan-section-title renders its slot so we can find section headings in wrapper.text().
 */
const GLOBAL_STUBS = {
  'evan-section-title': { template: '<div class="section-title"><slot /></div>' },
  'ugent-btn': { props: ['disable', 'label'], template: '<button :disabled="disable">{{ label }}</button>' },
  'readonly-field': true,
  'country-select': true,
  'dietary-select': true,
  'gender-select': true,
  'accompanying-persons': true,
  'fee-form-component': true,
  'q-select': true,
  'q-input': true,
  'q-checkbox': true,
  'q-list': { template: '<div><slot /></div>' },
  'q-item': { template: '<label><slot /></label>' },
  'q-item-section': { template: '<div><slot /></div>' },
  'q-item-label': { template: '<div><slot /></div>' },
  'q-badge': { template: '<span />' },
  'q-separator': true,
  'q-space': true,
};

let pinia: ReturnType<typeof createPinia>;

beforeEach(() => {
  pinia = createPinia();
  setActivePinia(pinia);
  // Reset shared reactive page props between tests.
  mockPageProps.sessions = [];
  mockPageProps.preview = false;
});

const mountPage = () =>
  mount(RegistrationPage, {
    global: {
      plugins: [pinia, i18n],
      stubs: GLOBAL_STUBS,
    },
  });

// --- Tests ------------------------------------------------------------------

describe('RegistrationPage', () => {
  describe('Form-level custom fields', () => {
    it('disables submit when a required global registration field is missing', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();

      store.evanEvent = {
        ...makeEvent(makeFee('onsite__regular', false)),
        registration_configuration: {
          fee_selection: null,
          form_fields: [
            {
              code: 'paper_id',
              label: 'Paper ID',
              field_type: 'text',
              required: true,
            },
          ],
        },
      } as any;
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;

      await nextTick();

      expect(wrapper.find('button').attributes('disabled')).toBeDefined();
    });

    it('enables submit when a required global registration field is provided', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();

      store.evanEvent = {
        ...makeEvent(makeFee('onsite__regular', false)),
        registration_configuration: {
          fee_selection: null,
          form_fields: [
            {
              code: 'paper_id',
              label: 'Paper ID',
              field_type: 'text',
              required: true,
            },
          ],
        },
      } as any;
      store.loading = false;
      store.registration = {
        ...makeRegistration('onsite__regular'),
        extra_data: {
          _internal: { share_email_with_sponsors: false, allow_photo_sharing: true },
          paper_id: '42',
        },
      };
      userStore.user = mockUser;

      await nextTick();

      expect(wrapper.find('button').attributes('disabled')).toBeUndefined();
    });
  });

  describe('Social events section', () => {
    it('shows the social events section when the selected fee is not online and social events exist', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [makeSocialSession()];

      await nextTick();

      expect(wrapper.text()).toContain('Social events');
    });

    it('hides the social events section when the selected fee is online', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('online__regular', true));
      store.loading = false;
      store.registration = makeRegistration('online__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [makeSocialSession()];

      await nextTick();

      expect(wrapper.text()).not.toContain('Social events');
    });

    it('hides the social events section when there are no social event sessions', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = []; // no social events

      await nextTick();

      expect(wrapper.text()).not.toContain('Social events');
    });
  });

  describe('Special needs section', () => {
    it('shows the special needs section when the selected fee is not online and user is logged in', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;

      await nextTick();

      expect(wrapper.text()).toContain('Special needs');
    });

    it('hides the special needs section when the selected fee is online', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('online__regular', true));
      store.loading = false;
      store.registration = makeRegistration('online__regular');
      userStore.user = mockUser;

      await nextTick();

      expect(wrapper.text()).not.toContain('Special needs');
    });

    it('hides the special needs section when no user is logged in', async () => {
      const wrapper = mountPage();

      const store = useStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      // userStore.user remains null

      await nextTick();

      expect(wrapper.text()).not.toContain('Special needs');
    });
  });

  describe('Accompanying persons section', () => {
    it('shows the accompanying persons section when the selected fee is not online and social events exist', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [makeSocialSession()];

      await nextTick();

      expect(wrapper.text()).toContain('Accompanying persons');
    });

    it('hides the accompanying persons section when the selected fee is online', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('online__regular', true));
      store.loading = false;
      store.registration = makeRegistration('online__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [makeSocialSession()];

      await nextTick();

      expect(wrapper.text()).not.toContain('Accompanying persons');
    });
  });

  describe('Travel visa section', () => {
    it('shows the travel visa section when the selected fee is not online', async () => {
      const wrapper = mountPage();

      const store = useStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');

      await nextTick();

      expect(wrapper.text()).toContain('Travel visa');
    });

    it('hides the travel visa section when the selected fee is online', async () => {
      const wrapper = mountPage();

      const store = useStore();
      store.evanEvent = makeEvent(makeFee('online__regular', true));
      store.loading = false;
      store.registration = makeRegistration('online__regular');

      await nextTick();

      expect(wrapper.text()).not.toContain('Travel visa');
    });
  });

  describe('Photo consent item', () => {
    it('shows the photo consent item when the selected fee is not online', async () => {
      const wrapper = mountPage();

      const store = useStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');

      await nextTick();

      expect(wrapper.text()).toContain('I do not want my photos taken during the event');
    });

    it('hides the photo consent item when the selected fee is online', async () => {
      const wrapper = mountPage();

      const store = useStore();
      store.evanEvent = makeEvent(makeFee('online__regular', true));
      store.loading = false;
      store.registration = makeRegistration('online__regular');

      await nextTick();

      expect(wrapper.text()).not.toContain('I do not want my photos taken during the event');
    });

    it('hides the photo consent item for a virtual event even with an onsite fee type', async () => {
      const wrapper = mountPage();

      const store = useStore();
      store.evanEvent = makeVirtualEvent(makeFee('regular', false));
      store.loading = false;
      store.registration = makeRegistration('regular');

      await nextTick();

      expect(wrapper.text()).not.toContain('I do not want my photos taken during the event');
    });
  });

  describe('Virtual event (is_virtual = true)', () => {
    it('hides travel visa, photo consent, social events, and accompanying persons for a virtual event', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeVirtualEvent(makeFee('regular', false));
      store.loading = false;
      store.registration = makeRegistration('regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [makeSocialSession()];

      await nextTick();

      expect(wrapper.text()).not.toContain('Travel visa');
      expect(wrapper.text()).not.toContain('I do not want my photos taken during the event');
      expect(wrapper.text()).not.toContain('Social events');
      expect(wrapper.text()).not.toContain('Special needs');
      expect(wrapper.text()).not.toContain('Accompanying persons');
    });
  });
});
