import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';

vi.mock('@/components/NoResults.vue', () => ({
  default: {
    name: 'no-results',
    template: '<div data-testid="no-results">No results</div>',
  },
}));

import AlbumViewer from '../AlbumViewer.vue';

const globalStubs = {
  'q-tabs': { template: '<div><slot /></div>' },
  'q-tab': { template: '<div><slot /></div>' },
  'q-badge': { template: '<span><slot /></span>' },
  'q-btn': { template: '<button><slot /></button>' },
  'q-img': { template: '<img />' },
  'q-dialog': { template: '<div><slot /></div>' },
  'q-card': { template: '<div><slot /></div>' },
  'q-card-section': { template: '<div><slot /></div>' },
  'q-space': { template: '<span />' },
};

describe('AlbumViewer', () => {
  const mountComponent = (props: Record<string, unknown>) =>
    mount(AlbumViewer, {
      props,
      global: {
        stubs: globalStubs,
      },
    });

  it('renders the no-results state when the albums prop is missing', () => {
    const wrapper = mountComponent({ eventCode: 'fpl2026', loading: false });

    expect(wrapper.find('[data-testid="no-results"]').exists()).toBe(true);
  });

  it('renders album tabs when albums are provided', () => {
    const wrapper = mountComponent({
      eventCode: 'fpl2026',
      loading: false,
      albums: [{ id: 1, title: 'Social dinner', photos: [] }],
    });

    expect(wrapper.text()).toContain('Social dinner');
  });
});