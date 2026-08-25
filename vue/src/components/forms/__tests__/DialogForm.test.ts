import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';

import DialogForm from '../DialogForm.vue';

const mountDialogForm = (props: Record<string, unknown> = {}, slots: Record<string, string> = {}) =>
  mount(DialogForm, {
    props: { icon: 'edit', title: 'My title', ...props },
    slots,
    global: {
      stubs: {
        'q-layout': {
          name: 'q-layout',
          props: ['view', 'container'],
          template: '<div><slot /></div>',
        },
        'q-header': { template: '<header><slot /></header>' },
        'q-footer': { template: '<footer><slot /></footer>' },
        'q-page-container': { template: '<main><slot /></main>' },
        'q-page': { template: '<section><slot /></section>' },
        'q-toolbar': { template: '<div class="toolbar"><slot /></div>' },
        'q-toolbar-title': { template: '<div class="title"><slot /></div>' },
        'q-space': { template: '<span class="space" />' },
        'q-btn': { template: '<button><slot /></button>' },
        'q-icon': { template: '<i />' },
        'q-separator': { template: '<hr />' },
      },
    },
  });

describe('DialogForm', () => {
  it('renders the title in the toolbar', () => {
    const wrapper = mountDialogForm({ title: 'My title' });

    expect(wrapper.find('.title').text()).toContain('My title');
  });

  it('renders the subtitle next to the title when provided', () => {
    const wrapper = mountDialogForm({ title: 'My title', subtitle: 'extra info' });

    expect(wrapper.find('.title').text()).toContain('extra info');
  });

  it('does not render a footer slot when none is provided', () => {
    const wrapper = mountDialogForm({ title: 'My title' });

    expect(wrapper.find('footer').exists()).toBe(false);
  });

  it('renders the footer slot when provided', () => {
    const wrapper = mountDialogForm({ title: 'My title' }, { footer: '<span class="footer-content">save</span>' });

    expect(wrapper.find('footer .footer-content').exists()).toBe(true);
  });

  it('renders the page slot content', () => {
    const wrapper = mountDialogForm({ title: 'My title' }, { page: '<div class="page-body">body</div>' });

    expect(wrapper.find('.page-body').exists()).toBe(true);
  });

  it('renders the tabs slot content', () => {
    const wrapper = mountDialogForm({ title: 'My title' }, { tabs: '<div class="tabs-slot">tabs</div>' });

    expect(wrapper.find('.tabs-slot').exists()).toBe(true);
  });
});
