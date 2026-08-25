import { describe, it, expect } from 'vitest';
import { mount } from '@vue/test-utils';

import RegistrationFormFields from '../RegistrationFormFields.vue';

const mountComponent = (
  props: { fields: ExtraDataField[]; feeType?: string },
  modelValue: Record<string, unknown> = {},
) => {
  return mount(RegistrationFormFields, {
    props: {
      ...props,
      extraData: modelValue,
    },
    global: {
      stubs: {
        QCheckbox: { template: '<div class="q-checkbox" />' },
        QInput: { template: '<div class="q-input" />' },
        QRadio: { template: '<div class="q-radio" />' },
        QSelect: { template: '<div class="q-select" />' },
        QItem: { template: '<div class="q-item"><slot /></div>' },
        QItemSection: { template: '<div class="q-item-section"><slot /></div>' },
        QItemLabel: { template: '<div class="q-item-label"><slot /></div>' },
        QList: { template: '<div class="q-list"><slot /></div>' },
      },
    },
  });
};

describe('RegistrationFormFields', () => {
  it('renders text and checkbox fields', () => {
    const wrapper = mountComponent({
      fields: [
        { code: 'paper_id', label: 'Paper ID', field_type: 'text', required: true },
        { code: 'agree', label: 'Agree', field_type: 'checkbox', required: false },
      ],
    });

    expect(wrapper.findAll('.q-input')).toHaveLength(1);
    expect(wrapper.findAll('.q-checkbox')).toHaveLength(1);
  });

  it('filters fields by fee type when show_for is set', async () => {
    const wrapper = mountComponent({
      feeType: 'full',
      fields: [
        { code: 'paper_id', label: 'Paper ID', field_type: 'text', required: true, show_for: ['full'] },
        { code: 'student_id', label: 'Student ID', field_type: 'text', required: false, show_for: ['student'] },
      ],
    });

    expect(wrapper.findAll('.q-input')).toHaveLength(1);

    await wrapper.setProps({ feeType: 'student' });

    expect(wrapper.findAll('.q-input')).toHaveLength(1);
  });

  it('renders radio options inside q-items', () => {
    const wrapper = mountComponent({
      fields: [
        {
          code: 'arrival_day',
          label: 'Arrival day',
          field_type: 'radio',
          required: true,
          options: [
            { value: 'saturday', label: 'Saturday' },
            { value: 'sunday', label: 'Sunday' },
          ],
        },
      ],
    });

    expect(wrapper.findAll('.q-radio')).toHaveLength(2);
    expect(wrapper.findAll('.q-item')).toHaveLength(2);
  });

  it('renders multiselect options inside q-items', () => {
    const wrapper = mountComponent({
      fields: [
        {
          code: 'tutorials',
          label: 'Tutorials',
          field_type: 'multiselect',
          required: false,
          options: [
            { value: 'chisel', label: 'Chisel' },
            { value: 'finn', label: 'FINN' },
          ],
        },
      ],
    });

    expect(wrapper.findAll('.q-checkbox')).toHaveLength(2);
    expect(wrapper.findAll('.q-item')).toHaveLength(2);
  });

  it('renders select as q-select', () => {
    const wrapper = mountComponent({
      fields: [
        {
          code: 'transport',
          label: 'Transport card',
          field_type: 'select',
          required: false,
          options: [
            { value: 'yes', label: 'Yes' },
            { value: 'no', label: 'No' },
          ],
        },
      ],
    });

    expect(wrapper.findAll('.q-select')).toHaveLength(1);
  });

  it('renders time as q-input', () => {
    const wrapper = mountComponent({
      fields: [{ code: 'arrival_time', label: 'Arrival time', field_type: 'time', required: false }],
    });

    expect(wrapper.findAll('.q-input')).toHaveLength(1);
  });

  it('renders description text when provided', () => {
    const wrapper = mountComponent({
      fields: [
        {
          code: 'transport_card',
          label: 'Need a transport card?',
          field_type: 'radio',
          description: 'The conference center is a 25-minute walk from the city center.',
          options: [{ value: 'yes', label: 'yes' }],
        },
      ],
    });

    expect(wrapper.text()).toContain('25-minute walk from the city center');
  });

  it('hides field when show_when condition is unmet', () => {
    const wrapper = mountComponent(
      {
        fields: [
          { code: 'arrival_day', label: 'Arrival day', field_type: 'text', required: false },
          {
            code: 'arrival_time',
            label: 'Arrival time',
            field_type: 'time',
            required: false,
            show_when: ['arrival_day', 'saturday'],
          },
        ],
      },
      { arrival_day: 'sunday' },
    );

    expect(wrapper.findAll('.q-input')).toHaveLength(1);
  });

  it('shows field when show_when condition is met', () => {
    const wrapper = mountComponent(
      {
        fields: [
          { code: 'arrival_day', label: 'Arrival day', field_type: 'text', required: false },
          {
            code: 'arrival_time',
            label: 'Arrival time',
            field_type: 'time',
            required: false,
            show_when: ['arrival_day', 'saturday'],
          },
        ],
      },
      { arrival_day: 'saturday' },
    );

    expect(wrapper.findAll('.q-input')).toHaveLength(2);
  });

  it('requires both show_for and show_when to pass', async () => {
    const wrapper = mountComponent(
      {
        feeType: 'full',
        fields: [
          {
            code: 'conditional',
            label: 'Conditional',
            field_type: 'text',
            required: false,
            show_for: ['full'],
            show_when: ['arrival_day', 'saturday'],
          },
        ],
      },
      { arrival_day: 'sunday' },
    );

    expect(wrapper.findAll('.q-input')).toHaveLength(0);

    await wrapper.setProps({ extraData: { arrival_day: 'saturday' } });

    expect(wrapper.findAll('.q-input')).toHaveLength(1);
  });
});
