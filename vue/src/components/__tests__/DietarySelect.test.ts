import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import DietarySelect from '../DietarySelect.vue';

describe('DietarySelect', () => {
  const mountComponent = (modelValue = 'none') =>
    mount(DietarySelect, {
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

  it('exposes the seven dietary options in order', () => {
    const wrapper = mountComponent();

    expect(wrapper.findComponent({ name: 'q-select' }).props('options')).toEqual([
      { value: 'none', label: 'No special requirements' },
      { value: 'vegetarian', label: 'Vegetarian' },
      { value: 'vegan', label: 'Vegan' },
      { value: 'gluten_free', label: 'Gluten free' },
      { value: 'dairy_free', label: 'Dairy free' },
      { value: 'nut_free', label: 'Nut free' },
      { value: 'other', label: 'Other' },
    ]);
  });

  it('emits update:modelValue when the selection changes', async () => {
    const wrapper = mountComponent();

    wrapper.findComponent({ name: 'q-select' }).vm.$emit('update:modelValue', 'vegan');
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('update:modelValue')).toEqual([['vegan']]);
  });
});
