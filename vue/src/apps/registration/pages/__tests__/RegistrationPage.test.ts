import { describe, it, expect, vi, beforeEach } from 'vitest';
import { reactive, nextTick } from 'vue';
import { mount, flushPromises } from '@vue/test-utils';
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
    put: vi.fn().mockResolvedValue({ data: {} }),
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
      fields: {
        first_name: 'First name',
        last_name: 'Last name',
        email: 'Email',
        affiliation: 'Affiliation',
        country: 'Country',
        name: 'Name',
      },
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
  is_sold_out: false,
  remaining_capacity: null,
});

const makeEvent = (...fees: Fee[]) =>
  ({
    code: 'TEST26',
    is_virtual: false,
    fees,
    registration_configuration: { fee_selection: null, form_fields: [], accompanying_persons: true },
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
    end_at: '2026-09-01T22:30:00',
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
  extra_data: {
    gender: '',
    dietary: 'none',
    special_needs: null,
    connect: false,
  },
};

// --- Test helpers -----------------------------------------------------------

/**
 * Stubs for all child components and Quasar components.
 * evan-section-title renders its slot so we can find section headings in wrapper.text().
 */
const GLOBAL_STUBS = {
  'evan-section-title': { template: '<div class="section-title"><slot /></div>' },
  'ugent-btn': {
    props: ['disable', 'label', 'loading'],
    template: '<button :disabled="disable" @click="$emit(\'click\')">{{ label }}</button>',
  },
  'readonly-field': true,
  'profile-info-fields': true,
  'country-select': true,
  'dietary-select': true,
  'gender-select': true,
  'accompanying-persons': true,
  'fee-form-component': true,
  'q-select': true,
  'q-page': { template: '<div><slot /></div>' },
  'q-input': true,
  'q-checkbox': true,
  'q-radio': {
    props: ['modelValue', 'val', 'disable'],
    emits: ['click', 'update:modelValue'],
    template:
      '<input type="radio" :data-val="val" :data-checked="modelValue === val" :disabled="disable" @click="$emit(\'click\', $event)" />',
  },
  'q-list': { template: '<div><slot /></div>' },
  'q-item': { template: '<label><slot /></label>' },
  'q-item-section': { template: '<div><slot /></div>' },
  'q-item-label': { template: '<div><slot /></div>' },
  'q-badge': { template: '<span />' },
  'q-btn': {
    props: ['label', 'disable', 'href'],
    template: '<a :href="href" :aria-disabled="disable">{{ label }}</a>',
  },
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
  vi.stubGlobal('scrollTo', vi.fn());
});

const mountPage = () =>
  mount(RegistrationPage, {
    global: {
      plugins: [pinia, i18n],
      stubs: GLOBAL_STUBS,
      directives: {
        ripple: () => {},
      },
    },
  });

// --- Tests ------------------------------------------------------------------

describe('RegistrationPage', () => {
  describe('Save workflow', () => {
    it('updates profile before updating registration', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();

      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = { ...mockUser };

      await nextTick();

      const callOrder: string[] = [];
      vi.spyOn(userStore, 'updateUser').mockImplementation(async () => {
        callOrder.push('profile');
      });
      vi.spyOn(store, 'updateRegistration').mockImplementation(async () => {
        callOrder.push('registration');
      });

      await wrapper.find('button').trigger('click');
      await flushPromises();

      expect(callOrder).toEqual(['profile', 'registration']);
    });

    it('normalizes all-caps first and last names before saving profile', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();

      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = {
        ...mockUser,
        first_name: 'JEAN',
        last_name: "DUPONT-D'ARC",
      };

      await nextTick();

      const updateUserSpy = vi.spyOn(userStore, 'updateUser').mockResolvedValue();
      vi.spyOn(store, 'updateRegistration').mockResolvedValue();

      await wrapper.find('button').trigger('click');
      await flushPromises();

      expect(updateUserSpy).toHaveBeenCalledWith(
        expect.objectContaining({
          first_name: 'Jean',
          last_name: "Dupont-D'Arc",
        }),
      );
    });
  });

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
          accompanying_persons: true,
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
          accompanying_persons: true,
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

    it('includes accompanying person extras in the summary total', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = {
        ...makeRegistration('onsite__regular'),
        extra_data: {
          _internal: { share_email_with_sponsors: false, allow_photo_sharing: true },
          accompanying_persons: [
            {
              name: 'Guest User',
              dietary: 'none',
              selected_social_events: [1],
            },
          ],
        },
      };
      userStore.user = mockUser;
      mockPageProps.sessions = [makeSocialSession()];

      await nextTick();

      expect(wrapper.text()).toContain('Accompanying persons');
      expect(wrapper.text()).toContain('€ 50');
      expect(wrapper.text()).toContain('€ 250');
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

  describe('Program sessions in registration form', () => {
    const makeProgramSession = (id: number, title: string, extra: Partial<SessionExtraData> = {}): Session =>
      ({
        id,
        is_social_event: false,
        is_private: false,
        title,
        start_at: '2026-09-03T10:00:00',
        extra_attendees_fee: 0,
        slug: `session-${id}`,
        code: `S${id}`,
        description: '',
        extra_data: { committees: [], important_dates: [], ...extra },
      }) as any;

    it('shows program sessions marked selectable_in_form when program_session_selection is false', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [makeProgramSession(10, 'Tutorial: Chisel')];
      mockPageProps.sessions[0].extra_data!.selectable_in_form = true;

      await nextTick();

      expect(wrapper.text()).toContain('Tutorial: Chisel');
    });

    it('hides program sessions without selectable_in_form when program_session_selection is false', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [makeProgramSession(10, 'Hidden talk')];

      await nextTick();

      expect(wrapper.text()).not.toContain('Hidden talk');
    });

    it('shows all non-private program sessions when program_session_selection is true', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = {
        ...makeEvent(makeFee('onsite__regular', false)),
        registration_configuration: {
          fee_selection: null,
          form_fields: [],
          accompanying_persons: true,
          program_session_selection: true,
        },
      } as any;
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [makeProgramSession(10, 'Any talk')];

      await nextTick();

      expect(wrapper.text()).toContain('Any talk');
    });

    it('hides private sessions even when program_session_selection is true', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = {
        ...makeEvent(makeFee('onsite__regular', false)),
        registration_configuration: {
          fee_selection: null,
          form_fields: [],
          accompanying_persons: true,
          program_session_selection: true,
        },
      } as any;
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [makeProgramSession(10, 'Closed door', {})];
      mockPageProps.sessions[0].is_private = true;

      await nextTick();

      expect(wrapper.text()).not.toContain('Closed door');
    });

    it('renders grouped sessions inline in the sorted list', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [
        makeProgramSession(11, 'Track c-H', { group: 'Parallel slot 1', selectable_in_form: true }),
        makeProgramSession(12, 'Journal j-B', { group: 'Parallel slot 1', selectable_in_form: true }),
      ];

      await nextTick();

      expect(wrapper.text()).toContain('Track c-H');
      expect(wrapper.text()).toContain('Journal j-B');
    });

    it('deselects a grouped session when its selected radio is clicked again', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [
        makeProgramSession(11, 'Track c-H', { group: 'Parallel slot 1', selectable_in_form: true }),
        makeProgramSession(12, 'Journal j-B', { group: 'Parallel slot 1', selectable_in_form: true }),
      ];

      await nextTick();

      const radios = wrapper.findAll('input[type="radio"]');
      expect(radios).toHaveLength(2);

      // Select the first option in the group.
      await radios[0].trigger('click');
      await nextTick();
      expect(radios[0].attributes('data-checked')).toBe('true');
      expect(radios[1].attributes('data-checked')).toBe('false');

      // Click the already-selected radio again — it should deselect.
      await radios[0].trigger('click');
      await nextTick();
      expect(radios[0].attributes('data-checked')).toBe('false');
      expect(radios[1].attributes('data-checked')).toBe('false');
    });

    it('switches selection within a group when a sibling radio is clicked', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [
        makeProgramSession(11, 'Track c-H', { group: 'Parallel slot 1', selectable_in_form: true }),
        makeProgramSession(12, 'Journal j-B', { group: 'Parallel slot 1', selectable_in_form: true }),
      ];

      await nextTick();

      const radios = wrapper.findAll('input[type="radio"]');

      // Select the first option.
      await radios[0].trigger('click');
      await nextTick();
      expect(radios[0].attributes('data-checked')).toBe('true');

      // Click the sibling — selection must move, not accumulate.
      await radios[1].trigger('click');
      await nextTick();
      expect(radios[0].attributes('data-checked')).toBe('false');
      expect(radios[1].attributes('data-checked')).toBe('true');
    });

    it('renders a color dot for grouped sessions', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [
        makeProgramSession(11, 'Track c-H', { group: 'Parallel slot 1', selectable_in_form: true }),
        makeProgramSession(12, 'Journal j-B', { group: 'Parallel slot 1', selectable_in_form: true }),
      ];

      await nextTick();

      const dots = wrapper.findAll('.group-dot');
      expect(dots).toHaveLength(2);
      // Same group → same color.
      expect(dots[0].attributes('style')).toBe(dots[1].attributes('style'));
    });

    it('uses different colors for different groups', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [
        makeProgramSession(11, 'Track c-H', { group: 'Parallel slot 1', selectable_in_form: true }),
        makeProgramSession(12, 'Journal j-B', { group: 'Parallel slot 2', selectable_in_form: true }),
      ];

      await nextTick();

      const dots = wrapper.findAll('.group-dot');
      expect(dots).toHaveLength(2);
      expect(dots[0].attributes('style')).not.toBe(dots[1].attributes('style'));
    });

    it('sorts sessions by start time', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [
        makeProgramSession(20, 'Late talk', { selectable_in_form: true }),
        makeProgramSession(10, 'Early talk', { selectable_in_form: true }),
      ];
      mockPageProps.sessions[0].start_at = '2026-09-05T14:00:00';
      mockPageProps.sessions[1].start_at = '2026-09-05T09:00:00';

      await nextTick();

      const text = wrapper.text();
      const earlyIdx = text.indexOf('Early talk');
      const lateIdx = text.indexOf('Late talk');
      expect(earlyIdx).toBeLessThan(lateIdx);
    });

    it('renders ungrouped program sessions alongside social events', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [makeSocialSession(), makeProgramSession(20, 'Workshop: FINN')];
      mockPageProps.sessions[1].extra_data!.selectable_in_form = true;

      await nextTick();

      expect(wrapper.text()).toContain('Gala Dinner');
      expect(wrapper.text()).toContain('Workshop: FINN');
    });

    it('shows a Sessions block before Social events when program sessions are selectable', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [
        makeProgramSession(20, 'Workshop: FINN', { selectable_in_form: true }),
        makeSocialSession(),
      ];

      await nextTick();

      const text = wrapper.text();
      const sessionsIdx = text.indexOf('Sessions');
      const socialIdx = text.indexOf('Social events');
      expect(sessionsIdx).toBeGreaterThanOrEqual(0);
      expect(socialIdx).toBeGreaterThanOrEqual(0);
      expect(sessionsIdx).toBeLessThan(socialIdx);
      expect(text).toContain('Workshop: FINN');
      expect(text).toContain('Gala Dinner');
    });

    it('uses the regular subtitle when program_session_selection is enabled', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = {
        ...makeEvent(makeFee('onsite__regular', false)),
        registration_configuration: {
          fee_selection: null,
          form_fields: [],
          accompanying_persons: true,
          program_session_selection: true,
        },
      } as any;
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [makeProgramSession(10, 'Any talk')];

      await nextTick();

      const text = wrapper.text();
      expect(text).toContain('Sessions');
      expect(text).toContain('Select the sessions you would like to attend:');
    });

    it('uses the constrained subtitle when program_session_selection is disabled', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [makeProgramSession(10, 'Any talk', { selectable_in_form: true })];

      await nextTick();

      const text = wrapper.text();
      expect(text).toContain('Sessions');
      expect(text).toContain('Choose the sessions you will likely follow:');
      expect(text).not.toContain('Select the sessions you would like to attend:');
    });

    it('does not render a sessions block when only social events exist', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [makeSocialSession()];

      await nextTick();

      const text = wrapper.text();
      expect(text).toContain('Social events');
      expect(text).not.toContain('Sessions');
    });

    it('shows the session time range next to the date caption', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [
        makeProgramSession(10, 'Workshop: Chisel', { selectable_in_form: true }),
        makeSocialSession(),
      ];
      mockPageProps.sessions[0].start_at = '2026-09-03T10:00:00';
      mockPageProps.sessions[0].end_at = '2026-09-03T11:30:00';

      await nextTick();

      const text = wrapper.text();
      expect(text).toContain('10:00-11:30');
    });

    it('never shows program sessions in the summary box', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [
        makeProgramSession(10, 'Workshop: Chisel', { selectable_in_form: true }),
        makeSocialSession(),
      ];

      await nextTick();

      const summary = wrapper.find('.registration-summary-sidebar');
      expect(summary.text()).not.toContain('Workshop: Chisel');
    });

    it('filters program sessions by the selected fee days config', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      const dayFee: Fee = {
        ...makeFee('onsite__regular', false),
        config: { included_social_events: [], days: ['2026-09-03'] },
      };
      store.evanEvent = makeEvent(dayFee);
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [
        makeProgramSession(10, 'Wednesday workshop', { selectable_in_form: true }),
        makeProgramSession(20, 'Thursday keynote', { selectable_in_form: true }),
      ];
      mockPageProps.sessions[0].start_at = '2026-09-03T09:00:00';
      mockPageProps.sessions[1].start_at = '2026-09-04T09:00:00';

      await nextTick();

      const text = wrapper.text();
      expect(text).toContain('Wednesday workshop');
      expect(text).not.toContain('Thursday keynote');
    });

    it('shows all program sessions when the fee has no days config', async () => {
      const wrapper = mountPage();

      const store = useStore();
      const userStore = useUserStore();
      store.evanEvent = makeEvent(makeFee('onsite__regular', false));
      store.loading = false;
      store.registration = makeRegistration('onsite__regular');
      userStore.user = mockUser;
      mockPageProps.sessions = [
        makeProgramSession(10, 'Wednesday workshop', { selectable_in_form: true }),
        makeProgramSession(20, 'Thursday keynote', { selectable_in_form: true }),
      ];
      mockPageProps.sessions[0].start_at = '2026-09-03T09:00:00';
      mockPageProps.sessions[1].start_at = '2026-09-04T09:00:00';

      await nextTick();

      const text = wrapper.text();
      expect(text).toContain('Wednesday workshop');
      expect(text).toContain('Thursday keynote');
    });
  });
});
