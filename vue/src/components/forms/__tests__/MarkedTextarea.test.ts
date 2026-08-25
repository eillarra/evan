import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';

import MarkedTextarea from '../MarkedTextarea.vue';

const mountMarkedTextarea = (modelValue = '', props: Record<string, unknown> = {}) =>
  mount(MarkedTextarea, {
    props: { label: 'Body', modelValue, ...props },
    global: {
      mocks: {
        $q: { screen: { gt: { md: false } } },
      },
      stubs: {
        'q-input': {
          name: 'q-input',
          props: ['modelValue', 'label', 'dense', 'autogrow', 'bottomSlots', 'inputStyle'],
          emits: ['update:modelValue'],
          template: '<textarea :value="modelValue" @input="$emit(\'update:modelValue\', $event.target.value)" />',
        },
        'marked-div': {
          name: 'marked-div',
          props: ['text', 'style'],
          template: '<div class="preview" />',
        },
      },
    },
  });

describe('MarkedTextarea', () => {
  it('initialises the editable text from the model value', () => {
    const wrapper = mountMarkedTextarea('hello world');

    expect(wrapper.find('textarea').element.value).toBe('hello world');
  });

  it('emits the updated value when the textarea changes', async () => {
    const wrapper = mountMarkedTextarea('initial');

    await wrapper.find('textarea').setValue('new content');

    expect(wrapper.emitted('update:modelValue')).toEqual([['new content']]);
  });

  it('passes the current text to the preview component', () => {
    const wrapper = mountMarkedTextarea('# Title');

    expect(wrapper.findComponent({ name: 'marked-div' }).props('text')).toBe('# Title');
  });

  it('updates the preview as the text changes', async () => {
    const wrapper = mountMarkedTextarea('start');

    await wrapper.find('textarea').setValue('updated text');

    expect(wrapper.findComponent({ name: 'marked-div' }).props('text')).toBe('updated text');
  });
});
