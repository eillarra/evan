import { describe, it, expect, vi, beforeEach } from 'vitest';
import { mount, flushPromises } from '@vue/test-utils';
import { createI18n } from 'vue-i18n';

const { mockGet, mockPost, mockDelete, mockAxiosGet } = vi.hoisted(() => ({
  mockGet: vi.fn(),
  mockPost: vi.fn(),
  mockDelete: vi.fn(),
  mockAxiosGet: vi.fn(),
}));

mockGet.mockResolvedValue({ data: [] });
mockPost.mockResolvedValue({ data: {} });
mockDelete.mockResolvedValue({ data: {} });
mockAxiosGet.mockResolvedValue({ data: new Blob(['content']) });

vi.mock('@/axios', () => ({
  api: {
    get: mockGet,
    post: mockPost,
    delete: mockDelete,
  },
  axios: {
    get: mockAxiosGet,
  },
}));

vi.mock('@/utils/dialog', () => ({ confirm: vi.fn() }));
vi.mock('@/utils/notify', () => ({ notify: { success: vi.fn(), error: vi.fn() } }));

import FilesView from '../FilesView.vue';

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: {
    en: {
      fields: {
        visibility: 'Visibility',
        visibility_public: 'Public',
        visibility_attendees: 'Attendees',
        visibility_organizers: 'Organizers',
        description: 'Description',
      },
      models: { file: 'File' },
      form: { new: 'New', create: 'Create' },
      messages: {
        file_created: 'File created',
        file_deleted: 'File deleted',
        file_download_failed: 'File download failed',
        file_confirm_delete: 'Are you sure?',
      },
    },
  },
} as any);

const mountView = (props: Record<string, unknown> = {}) =>
  mount(FilesView, {
    props: { apiEndpoint: '/api/v1/rel/30/1/files/', ...props },
    global: {
      plugins: [i18n],
      stubs: {
        'q-spinner': true,
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

/** Reach the component's internals the way the template does. */
const internals = (wrapper: ReturnType<typeof mountView>) =>
  wrapper.vm as unknown as {
    visibilityOptions: { value: string }[];
    formData: { visibility: string; description: string | null };
    file: File | null;
    addRelatedFile: () => Promise<void>;
    downloadFile: (file: RelatedFile) => Promise<void>;
  };

describe('FilesView', () => {
  beforeEach(() => {
    mockGet.mockClear();
    mockPost.mockClear();
    mockDelete.mockClear();
    mockAxiosGet.mockClear();
    mockGet.mockResolvedValue({ data: [] });
    mockPost.mockResolvedValue({
      data: {
        id: 2,
        self: '/api/v1/rel/30/1/files/2/',
        file: '/media/files/30/1/slides.pdf',
        visibility: 'organizers',
        description: 'Slides',
        tags: [],
      },
    });
  });

  it('offers the three visibility tiers', async () => {
    const wrapper = mountView();
    await flushPromises();

    expect(internals(wrapper).visibilityOptions.map((option) => option.value)).toEqual([
      'public',
      'attendees',
      'organizers',
    ]);
  });

  it('restricts the offered tiers to the given options', async () => {
    const wrapper = mountView({ visibilityOptions: ['public', 'attendees'] });
    await flushPromises();

    expect(internals(wrapper).visibilityOptions.map((option) => option.value)).toEqual(['public', 'attendees']);
  });

  it('sends the chosen visibility tier when uploading', async () => {
    const wrapper = mountView();
    await flushPromises();

    const vm = internals(wrapper);
    vm.formData.visibility = 'organizers';
    vm.formData.description = 'Slides';
    vm.file = new File(['content'], 'slides.pdf');

    await vm.addRelatedFile();

    const formData = mockPost.mock.calls[0][1] as FormData;
    expect(JSON.parse(formData.get('json') as string).visibility).toBe('organizers');
  });

  it('lists each file with its visibility label', async () => {
    mockGet.mockResolvedValue({
      data: [
        {
          id: 1,
          self: '/api/v1/rel/30/1/files/1/',
          file: '/media/files/30/1/slides.pdf',
          visibility: 'attendees',
          description: 'Slides',
          tags: [],
        },
      ],
    });

    const wrapper = mountView();
    await flushPromises();

    expect(wrapper.text()).toContain('Attendees');
    expect(wrapper.text()).toContain('Slides');
  });

  it('sends the secret when listing the files', async () => {
    mountView({ secret: 'the-secret' });
    await flushPromises();

    expect(mockGet).toHaveBeenCalledWith(
      '/api/v1/rel/30/1/files/',
      expect.objectContaining({ headers: { 'X-Evan-Secret': 'the-secret' } }),
    );
  });

  it('sends the secret when uploading a file', async () => {
    const wrapper = mountView({ secret: 'the-secret' });
    await flushPromises();

    const vm = internals(wrapper);
    vm.formData.description = 'Slides';
    vm.file = new File(['content'], 'slides.pdf');

    await vm.addRelatedFile();

    expect(mockPost).toHaveBeenCalledWith(
      '/api/v1/rel/30/1/files/',
      expect.anything(),
      expect.objectContaining({ headers: expect.objectContaining({ 'X-Evan-Secret': 'the-secret' }) }),
    );
  });

  it('fetches the file through the media path with the secret when downloading', async () => {
    const wrapper = mountView({ secret: 'the-secret' });
    await flushPromises();

    await internals(wrapper).downloadFile({
      id: 1,
      self: '/api/v1/rel/30/1/files/1/',
      file: '/media/files/30/1/slides.pdf',
      visibility: 'organizers',
      description: 'Slides',
      tags: [],
    });

    expect(mockAxiosGet).toHaveBeenCalledWith(
      '/media/files/30/1/slides.pdf',
      expect.objectContaining({ headers: { 'X-Evan-Secret': 'the-secret' }, responseType: 'blob' }),
    );
  });
});
