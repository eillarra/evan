import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import GenderSelect from '../GenderSelect.vue';

describe('GenderSelect', () => {
  const mountComponent = (modelValue = 'male') =>
    mount(GenderSelect, {
      props: { modelValue },
      global: {
        stubs: {
          'q-select': {
            name: 'q-select',
            props: ['modelValue', 'options', 'emitValue', 'mapOptions'],
            emits: ['update:modelValue'],
            template: '<div />',
          },
        },
      },
    });

  it('passes the GENDER_OPTIONS list to q-select', () => {
    const wrapper = mountComponent();

    expect(wrapper.findComponent({ name: 'q-select' }).props('options')).toEqual([
      { value: 'male', label: 'Male' },
      { value: 'female', label: 'Female' },
      { value: 'non_binary', label: 'Non-binary' },
      { value: 'prefer_not_to_say', label: 'Prefer not to say' },
    ]);
  });

  it('emits update:modelValue when the selection changes', async () => {
    const wrapper = mountComponent();

    wrapper.findComponent({ name: 'q-select' }).vm.$emit('update:modelValue', 'female');
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('update:modelValue')).toEqual([['female']]);
  });
});
