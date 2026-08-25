import { describe, expect, it } from 'vitest';
import { mount } from '@vue/test-utils';
import { createI18n } from 'vue-i18n';

import DateSelect from '../DateSelect.vue';

const i18n = createI18n({
  legacy: false,
  locale: 'en',
  messages: { en: { field: { date: 'Date' }, form: { close: 'Close' } } },
  globalInjection: true,
});

const mountDateSelect = (props: Record<string, unknown> = {}) =>
  mount(DateSelect, {
    props: { modelValue: null, ...props },
    global: {
      plugins: [i18n],
      stubs: {
        'q-input': {
          name: 'q-input',
          props: ['modelValue', 'label', 'disable', 'readonly', 'placeholder', 'mask'],
          emits: ['update:modelValue'],
          template: '<div><slot name="append" /></div>',
        },
        'q-icon': { template: '<span><slot /></span>' },
        'q-popup-proxy': { template: '<span><slot /></span>' },
        'q-date': {
          name: 'q-date',
          props: ['modelValue', 'mask', 'options'],
          emits: ['update:modelValue'],
          template: '<div />',
        },
        'q-time': {
          name: 'q-time',
          props: ['modelValue', 'format24h', 'options'],
          emits: ['update:modelValue'],
          template: '<div />',
        },
        'q-btn': { template: '<button><slot /></button>' },
      },
    },
  });

describe('DateSelect', () => {
  it('defaults to the date calendar type when no type is given', () => {
    const wrapper = mountDateSelect({ modelValue: '2026-08-20' });

    expect(wrapper.findComponent({ name: 'q-date' }).exists()).toBe(true);
    expect(wrapper.findComponent({ name: 'q-time' }).exists()).toBe(false);
  });

  it('renders a date picker for the date type', () => {
    const wrapper = mountDateSelect({ modelValue: '2026-08-20', type: 'date' });

    expect(wrapper.findComponent({ name: 'q-date' }).exists()).toBe(true);
  });

  it('renders a time picker for the time type and hides the date picker', () => {
    const wrapper = mountDateSelect({ modelValue: '2026-08-20T10:30:00', type: 'time' });

    expect(wrapper.findComponent({ name: 'q-time' }).exists()).toBe(true);
    expect(wrapper.findComponent({ name: 'q-date' }).exists()).toBe(false);
  });

  it('renders both date and time pickers for the datetime type', () => {
    const wrapper = mountDateSelect({ modelValue: '2026-08-20T10:30:00', type: 'datetime' });

    expect(wrapper.findComponent({ name: 'q-date' }).exists()).toBe(true);
    expect(wrapper.findComponent({ name: 'q-time' }).exists()).toBe(true);
  });

  it('emits the combined datetime when date and time are chosen', async () => {
    const wrapper = mountDateSelect({ modelValue: null, type: 'datetime' });

    wrapper.findComponent({ name: 'q-date' }).vm.$emit('update:modelValue', '2026-08-20');
    wrapper.findComponent({ name: 'q-time' }).vm.$emit('update:modelValue', '10:30:00');
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('update:modelValue')).toEqual([['2026-08-20T10:30:00']]);
  });

  it('emits only the date for the date type when a date is chosen', async () => {
    const wrapper = mountDateSelect({ modelValue: null, type: 'date' });

    wrapper.findComponent({ name: 'q-date' }).vm.$emit('update:modelValue', '2026-08-20');
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('update:modelValue')).toEqual([['2026-08-20']]);
  });

  it('emits only the time for the time type when a time is chosen', async () => {
    const wrapper = mountDateSelect({ modelValue: null, type: 'time' });

    wrapper.findComponent({ name: 'q-time' }).vm.$emit('update:modelValue', '10:30:00');
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('update:modelValue')).toEqual([['10:30:00']]);
  });

  it('hides the append pickers when readonly', () => {
    const wrapper = mountDateSelect({ modelValue: '2026-08-20', type: 'date', readonly: true });

    expect(wrapper.findComponent({ name: 'q-date' }).exists()).toBe(false);
  });
});
