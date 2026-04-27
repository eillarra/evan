import { describe, it, expect } from 'vitest';
import { defineComponent, nextTick } from 'vue';
import { mount } from '@vue/test-utils';

import FeeFormComponent from '../FeeFormComponent.vue';

/**
 * Interactive QSelect stub that syncs modelValue via a native <select>.
 * This lets tests use setValue() to drive formData changes inside the component.
 */
const QSelectStub = defineComponent({
  props: ['modelValue', 'options', 'label'],
  emits: ['update:modelValue'],
  template: `
    <select :value="modelValue" @change="$emit('update:modelValue', $event.target.value)">
      <option value="">-- none --</option>
      <option v-for="opt in options" :key="opt.value" :value="opt.value">{{ opt.label }}</option>
    </select>
  `,
});

const STUBS = {
  'q-select': QSelectStub,
  'q-input': true,
};

/**
 * A simple two-level fee config:
 *   Level 1: attendance_type (onsite | online), no dependency.
 *   Level 2: profile (regular | student), only shown when attendance_type == onsite.
 */
const TWO_LEVEL_CONFIG: FeeSelectionConfig = {
  criteria: [
    {
      code: 'attendance_type',
      question: 'Attendance type',
      options: [
        { value: 'onsite', label: 'On-site' },
        { value: 'online', label: 'Online' },
      ],
    },
    {
      code: 'profile',
      question: 'Profile',
      depends_on: ['attendance_type', ['onsite']],
      options: [
        { value: 'regular', label: 'Regular' },
        { value: 'student', label: 'Student' },
      ],
    },
  ],
};

const VALID_FEES = ['onsite__regular', 'onsite__student', 'online'];

const mountFeeForm = async (fee = '', feeConfig = TWO_LEVEL_CONFIG) => {
  const wrapper = mount(FeeFormComponent, {
    props: { feeConfig, validFees: VALID_FEES, fee },
    global: { stubs: STUBS },
  });
  // onMounted initialises formData, then the watcher fires and visibleCriteria updates.
  // Two ticks are needed: one for onMounted, one for the reactive re-render.
  await nextTick();
  await nextTick();
  return wrapper;
};

describe('FeeFormComponent', () => {
  describe('initial criteria visibility', () => {
    it('shows only the independent criterion when no fee is pre-selected', async () => {
      const wrapper = await mountFeeForm('');
      // Only attendance_type criterion (no depends_on) should be rendered.
      expect(wrapper.findAll('select')).toHaveLength(1);
    });

    it('shows both criteria when initialized with a fee that satisfies the dependency', async () => {
      const wrapper = await mountFeeForm('onsite__regular');
      // attendance_type = 'onsite' satisfies profile's depends_on, so both criteria show.
      expect(wrapper.findAll('select')).toHaveLength(2);
    });

    it('shows only the independent criterion for a fee that does not satisfy the dependency', async () => {
      const wrapper = await mountFeeForm('online');
      // attendance_type = 'online' does NOT satisfy profile's depends_on, so only one criterion.
      expect(wrapper.findAll('select')).toHaveLength(1);
    });
  });

  describe('dynamic criteria visibility (user interaction)', () => {
    it('reveals dependent criterion after selecting a qualifying value', async () => {
      const wrapper = await mountFeeForm('');
      expect(wrapper.findAll('select')).toHaveLength(1);

      // Simulate selecting 'onsite' for attendance_type.
      await wrapper.find('select').setValue('onsite');

      expect(wrapper.findAll('select')).toHaveLength(2);
    });

    it('hides dependent criterion when the dependency value changes to a non-qualifying value', async () => {
      const wrapper = await mountFeeForm('onsite__regular');
      expect(wrapper.findAll('select')).toHaveLength(2);

      // Change attendance_type to 'online', which does not satisfy the profile dependency.
      await wrapper.findAll('select')[0].setValue('online');

      expect(wrapper.findAll('select')).toHaveLength(1);
    });
  });

  describe('fee type emission', () => {
    it('emits the joined criteria values as the fee type', async () => {
      const wrapper = await mountFeeForm('');

      await wrapper.find('select').setValue('onsite');
      await wrapper.findAll('select')[1].setValue('student');

      const emitted = wrapper.emitted('update:fee') as string[][];
      expect(emitted.at(-1)![0]).toBe('onsite__student');
    });

    it('emits only non-null values (no trailing separator for single-level selections)', async () => {
      const wrapper = await mountFeeForm('');

      await wrapper.find('select').setValue('online');

      const emitted = wrapper.emitted('update:fee') as string[][];
      expect(emitted.at(-1)![0]).toBe('online');
    });
  });

  describe('extra_data fields', () => {
    const CONFIG_WITH_EXTRA_FIELDS: FeeSelectionConfig = {
      criteria: [
        {
          code: 'attendance_type',
          question: 'Attendance type',
          options: [
            { value: 'onsite', label: 'On-site' },
            { value: 'online', label: 'Online' },
          ],
          extra_data_fields: [
            { code: 'hotel', label: 'Hotel name', field_type: 'text', required: false, show_for: ['onsite'] },
          ],
        },
      ],
    };

    it('shows extra_data fields when the selected value matches show_for', async () => {
      const wrapper = mount(FeeFormComponent, {
        props: { feeConfig: CONFIG_WITH_EXTRA_FIELDS, validFees: ['onsite', 'online'], fee: '' },
        global: { stubs: STUBS },
      });

      await wrapper.find('select').setValue('onsite');

      // q-input stub renders as <q-input-stub>, confirming the field is rendered.
      expect(wrapper.find('q-input-stub').exists()).toBe(true);
    });

    it('hides extra_data fields when the selected value does not match show_for', async () => {
      const wrapper = mount(FeeFormComponent, {
        props: { feeConfig: CONFIG_WITH_EXTRA_FIELDS, validFees: ['onsite', 'online'], fee: '' },
        global: { stubs: STUBS },
      });

      await wrapper.find('select').setValue('online');

      expect(wrapper.find('q-input-stub').exists()).toBe(false);
    });
  });
});
