import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';

import SelectorDialog from '../SelectorDialog.vue';

const mountSelectorDialog = (props: Record<string, unknown> = {}, slots: Record<string, string> = {}) =>
  mount(SelectorDialog, {
    props: { modelValue: true, title: 'Pick one', searchPlaceholder: 'Search...', searchQuery: '', ...props },
    slots,
    global: {
      stubs: {
        'q-dialog': {
          name: 'q-dialog',
          props: ['modelValue', 'persistent'],
          emits: ['update:modelValue'],
          template: '<div :data-open="modelValue"><slot /></div>',
        },
        'q-card': { template: '<div class="card"><slot /></div>' },
        'q-card-section': { template: '<section><slot /></section>' },
        'q-card-actions': { template: '<div class="actions"><slot /></div>' },
        'q-input': {
          name: 'q-input',
          props: ['modelValue', 'placeholder', 'outlined', 'dense', 'clearable'],
          emits: ['update:modelValue'],
          template: '<input :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        'q-icon': { template: '<i />' },
        'q-list': { template: '<ul><slot /></ul>' },
        'q-btn': { template: '<button><slot /></button>' },
      },
    },
  });

describe('SelectorDialog', () => {
  it('renders the dialog title', () => {
    const wrapper = mountSelectorDialog({ title: 'Choose a speaker' });

    expect(wrapper.text()).toContain('Choose a speaker');
  });

  it('renders the provided items slot', () => {
    const wrapper = mountSelectorDialog({}, { items: '<li class="item-row">Alice</li>' });

    expect(wrapper.find('.item-row').exists()).toBe(true);
  });

  it('emits update:modelValue=false when the cancel button is clicked', async () => {
    const wrapper = mountSelectorDialog({ modelValue: true, cancelLabel: 'Cancel' });

    await wrapper.find('.actions button').trigger('click');

    expect(wrapper.emitted('update:modelValue')).toEqual([[false]]);
  });

  it('emits update:searchQuery when the search input changes', async () => {
    const wrapper = mountSelectorDialog({ searchQuery: '' });

    await wrapper.find('input').setValue('alice');

    expect(wrapper.emitted('update:searchQuery')).toEqual([['alice']]);
  });

  it('reflects the dialog open state via the model-value prop', () => {
    const open = mountSelectorDialog({ modelValue: true });
    const closed = mountSelectorDialog({ modelValue: false });

    expect(open.findComponent({ name: 'q-dialog' }).props('modelValue')).toBe(true);
    expect(closed.findComponent({ name: 'q-dialog' }).props('modelValue')).toBe(false);
  });
});
