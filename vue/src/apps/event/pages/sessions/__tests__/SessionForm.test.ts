import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';
import { createI18n } from 'vue-i18n';
import { nextTick } from 'vue';

import SessionForm from '../SessionForm.vue';
import { useStore } from '../../store';

// Regression test for EVAN-FRONTEND-13: "ReferenceError: Cannot access 'Y'
// before initialization". Opening the form on an existing session that already
// had a `program` triggered an `immediate: true` watcher which referenced a
// `const` (the debounced renderer) declared further down in <script setup>,
// hitting the temporal dead zone during setup().

const mockValidateTemplate = vi.fn().mockResolvedValue({
  is_valid: true,
  errors: [],
  paper_references: [],
  keynote_references: [],
});
const mockRenderTemplate = vi.fn().mockResolvedValue('<p>rendered program</p>');

vi.mock('@/composables/useProgramTemplate', () => ({
  useProgramTemplate: () => ({
    validateTemplate: mockValidateTemplate,
    renderTemplate: mockRenderTemplate,
  }),
}));

// Quasar's debounce is a real timer (500/1000ms). Override only that export so
// the wrapped function runs immediately — the synchronous path that triggered
// EVAN-FRONTEND-13 — without wiping out the rest of Quasar's component exports.
vi.mock('quasar', async (importOriginal) => {
  const actual = await importOriginal<typeof import('quasar')>();
  return {
    ...actual,
    debounce:
      (fn: (...args: any[]) => void) =>
      (...args: any[]) =>
        fn(...args),
  };
});

vi.mock('@/composables/useMinimumLoading', () => ({
  useMinimumLoading: () => ({
    loading: { value: false },
    executeWithMinLoading: vi.fn(async (fn: () => Promise<unknown>) => fn()),
  }),
}));

vi.mock('@/utils/dialog', () => ({ confirm: vi.fn() }));
vi.mock('@/utils/notify', () => ({ notify: { success: vi.fn(), error: vi.fn(), info: vi.fn() } }));
vi.mock('@/axios.ts', () => ({
  api: {
    get: vi.fn().mockResolvedValue({ data: [] }),
    post: vi.fn().mockResolvedValue({ data: {} }),
    put: vi.fn().mockResolvedValue({ data: {} }),
    patch: vi.fn().mockResolvedValue({ data: {} }),
    delete: vi.fn().mockResolvedValue({ data: {} }),
  },
}));

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: { en: {} },
} as any);

const SESSION_WITH_PROGRAM: Session = {
  id: 42,
  code: 'S1',
  title: 'Existing session',
  description: '',
  program: 'Welcome by [paperi:1]',
  start_at: null,
  end_at: null,
  track: null,
  topics: [],
  room: null,
  is_social_event: false,
  extra_attendees_fee: 0,
  subsessions: [],
} as unknown as Session;

let pinia: ReturnType<typeof createPinia>;

beforeEach(() => {
  pinia = createPinia();
  setActivePinia(pinia);
});

const mountSessionForm = async (obj?: Session) => {
  const wrapper = mount(SessionForm, {
    props: obj ? { obj } : {},
    global: {
      plugins: [pinia, i18n],
      stubs: {
        // Stub heavy children to keep this a behavioural boundary test, not
        // a full render test.
        DialogForm: { template: '<div><slot name="tabs" /><slot name="page" /><slot name="footer" /></div>' },
        ProgramTemplateEditor: true,
        MarkedTextarea: true,
        DateSelect: true,
        ReadonlyField: true,
        WarningBanner: true,
        SubsessionForm: true,
        UpdateBtn: true,
        'evan-select': true,
        'q-tabs': { template: '<div class="q-tabs"><slot /></div>' },
        'q-tab': { template: '<div class="q-tab" />', props: ['name', 'label'] },
        'q-tab-panels': { template: '<div class="q-tab-panels"><slot /></div>' },
        'q-tab-panel': { template: '<div class="q-tab-panel"><slot /></div>' },
        'q-input': true,
        'q-checkbox': true,
        'q-btn': { template: '<button @click="$emit(\'click\')"><slot /></button>' },
        'q-space': true,
      },
    },
  });

  await nextTick();
  await nextTick();
  return wrapper;
};

describe('SessionForm (regression: EVAN-FRONTEND-13)', () => {
  beforeEach(() => {
    mockValidateTemplate.mockClear();
    mockRenderTemplate.mockClear();
  });

  it('does not throw when mounted on a session that already has a program', async () => {
    // Before the fix, setup() threw synchronously: "Cannot access 'Y' before
    // initialization" because the `immediate: true` program watcher ran
    // before the debounced-render `const` was initialised.
    await expect(mountSessionForm(SESSION_WITH_PROGRAM)).resolves.toBeTruthy();
  });

  it('renders the program for an existing session without error', async () => {
    const wrapper = await mountSessionForm(SESSION_WITH_PROGRAM);

    // The component mounted without throwing and rendered its root.
    expect(wrapper.exists()).toBe(true);
    // Debounced rendering was scheduled for the existing program.
    expect(mockRenderTemplate).toHaveBeenCalledWith('Welcome by [paperi:1]');
  });
});
