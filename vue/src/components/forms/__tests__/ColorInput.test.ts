import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';

import ColorInput from '../ColorInput.vue';

const mountColorInput = (modelValue = '#1e64c8', props: Record<string, unknown> = {}) =>
  mount(ColorInput, {
    props: { modelValue, ...props },
    global: {
      stubs: {
        'q-input': {
          name: 'q-input',
          props: ['modelValue', 'label', 'dense', 'disable', 'readonly', 'clearable', 'mask', 'placeholder', 'prefix'],
          emits: ['update:modelValue'],
          template: '<div><slot name="append" /></div>',
        },
        'q-icon': { template: '<span><slot /></span>' },
        'q-popup-proxy': { template: '<span><slot /></span>' },
        'q-color': {
          name: 'q-color',
          props: ['modelValue', 'formatModel'],
          emits: ['update:modelValue'],
          template: '<div />',
        },
      },
    },
  });

describe('ColorInput', () => {
  it('strips the leading hash when passing the value to the text field', () => {
    const wrapper = mountColorInput('#1e64c8');

    expect(wrapper.findComponent({ name: 'q-input' }).props('modelValue')).toBe('1e64c8');
  });

  it('keeps the value as-is when no leading hash is present', () => {
    const wrapper = mountColorInput('ffaa00');

    expect(wrapper.findComponent({ name: 'q-input' }).props('modelValue')).toBe('ffaa00');
  });

  it('emits the color with a leading hash when the user types a hex value', async () => {
    const wrapper = mountColorInput('#1e64c8');

    wrapper.findComponent({ name: 'q-input' }).vm.$emit('update:modelValue', '00ff00');
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('update:modelValue')).toEqual([['#00ff00']]);
  });

  it('emits the color as-is when the user already includes the hash', async () => {
    const wrapper = mountColorInput('#1e64c8');

    wrapper.findComponent({ name: 'q-input' }).vm.$emit('update:modelValue', '#00ff00');
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('update:modelValue')).toEqual([['#00ff00']]);
  });

  it('emits an empty string when the value is cleared', async () => {
    const wrapper = mountColorInput('#1e64c8');

    wrapper.findComponent({ name: 'q-input' }).vm.$emit('update:modelValue', '');
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('update:modelValue')).toEqual([['']]);
  });

  it('forwards the selected color from the color picker', async () => {
    const wrapper = mountColorInput('#1e64c8');

    wrapper.findComponent({ name: 'q-color' }).vm.$emit('update:modelValue', '#abcdef');
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('update:modelValue')).toEqual([['#abcdef']]);
  });

  it('passes the current model value to the color picker', () => {
    const wrapper = mountColorInput('#1e64c8');

    expect(wrapper.findComponent({ name: 'q-color' }).props('modelValue')).toBe('#1e64c8');
  });
});
