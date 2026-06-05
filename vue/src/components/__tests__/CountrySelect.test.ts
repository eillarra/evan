import { describe, expect, it, beforeEach } from 'vitest';
import { mount } from '@vue/test-utils';
import { createPinia, setActivePinia } from 'pinia';

import CountrySelect from '../CountrySelect.vue';
import { useCommonStore } from '@/stores/common';

describe('CountrySelect', () => {
  beforeEach(() => {
    setActivePinia(createPinia());
  });

  it('handles null model value and emits updated value from selection', async () => {
    const wrapper = mount(CountrySelect, {
      props: {
        label: 'Country',
        modelValue: null,
      },
      global: {
        stubs: {
          'country-flag': true,
          'q-select': {
            name: 'q-select',
            props: ['modelValue', 'options'],
            emits: ['update:modelValue'],
            template: '<div />',
          },
        },
      },
    });

    const commonStore = useCommonStore();
    commonStore.countries = { BE: 'Belgium' };
    await wrapper.vm.$nextTick();

    expect(wrapper.findComponent({ name: 'q-select' }).props('options')).toEqual([{ code: 'BE', name: 'Belgium' }]);

    wrapper.findComponent({ name: 'q-select' }).vm.$emit('update:modelValue', 'BE');
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('update:modelValue')).toEqual([['BE']]);
  });
});
