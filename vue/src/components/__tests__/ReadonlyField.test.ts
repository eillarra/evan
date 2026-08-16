import { mount } from '@vue/test-utils';
import { describe, expect, it, vi } from 'vitest';

vi.mock('@/components/CopyIcon.vue', () => ({
  default: {
    name: 'copy-icon',
    props: ['text'],
    template: '<span data-testid="copy-icon" />',
  },
}));

import ReadonlyField from '../forms/ReadonlyField.vue';

describe('ReadonlyField', () => {
  const mountComponent = (props: { label: string; value: string | number; withCopy?: boolean }) =>
    mount(ReadonlyField, {
      props,
      global: {
        stubs: {
          'q-field': {
            name: 'q-field',
            template: '<div><slot name="control" /><slot name="append" /></div>',
          },
        },
      },
    });

  it('renders the value in the control slot', () => {
    const wrapper = mountComponent({ label: 'Name', value: 'Jane Doe' });

    expect(wrapper.text()).toContain('Jane Doe');
  });

  it('renders a copy icon when withCopy is true', () => {
    const wrapper = mountComponent({ label: 'Email', value: 'jane@example.com', withCopy: true });

    expect(wrapper.find('[data-testid="copy-icon"]').exists()).toBe(true);
  });

  it('does not render a copy icon when withCopy is absent', () => {
    const wrapper = mountComponent({ label: 'Email', value: 'jane@example.com' });

    expect(wrapper.find('[data-testid="copy-icon"]').exists()).toBe(false);
  });
});
