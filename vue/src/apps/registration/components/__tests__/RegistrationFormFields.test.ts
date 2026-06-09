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
        'q-input': true,
        'q-checkbox': true,
      },
    },
  });
};

describe('RegistrationFormFields', () => {
  it('renders all fields when no show_for is defined', () => {
    const wrapper = mountComponent({
      fields: [
        { code: 'paper_id', label: 'Paper ID', field_type: 'text', required: true },
        { code: 'agree', label: 'Agree', field_type: 'checkbox', required: false },
      ],
    });

    expect(wrapper.findAll('q-input-stub')).toHaveLength(1);
    expect(wrapper.findAll('q-checkbox-stub')).toHaveLength(1);
  });

  it('filters fields by fee type when show_for is set', async () => {
    const wrapper = mountComponent({
      feeType: 'full',
      fields: [
        { code: 'paper_id', label: 'Paper ID', field_type: 'text', required: true, show_for: ['full'] },
        { code: 'student_id', label: 'Student ID', field_type: 'text', required: false, show_for: ['student'] },
      ],
    });

    expect(wrapper.findAll('q-input-stub')).toHaveLength(1);

    await wrapper.setProps({ feeType: 'student' });

    expect(wrapper.findAll('q-input-stub')).toHaveLength(1);
  });
});
