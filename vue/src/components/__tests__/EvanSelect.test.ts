import { mount } from '@vue/test-utils';
import { defineComponent, type PropType } from 'vue';
import { describe, expect, it } from 'vitest';

import EvanSelect from '../EvanSelect.vue';
import { iconBadgeReception } from '@/icons';

interface Option {
  label: string;
  value: string | null;
  icon?: string;
}

const options = [
  { label: 'Reception', value: 'reception', icon: iconBadgeReception },
  { label: 'No icon', value: null },
];

const QSelectStub = defineComponent({
  name: 'q-select',
  props: {
    modelValue: { type: [String, Number, Boolean] as PropType<string | number | boolean | null>, default: null },
    options: { type: Array as PropType<Option[]>, default: (): Option[] => [] },
  },
  computed: {
    currentOpt(): Option {
      return this.options.find((option: Option) => option.value === this.modelValue) ?? this.options[0];
    },
  },
  template: `
    <div class="select-stub">
      <div class="selected"><slot name="selected-item" :opt="currentOpt" /></div>
      <div v-for="opt in options" class="option">
        <slot name="option" :opt="opt" :itemProps="{}" />
      </div>
    </div>
  `,
});

const mountComponent = (modelValue: string | null = null) =>
  mount(EvanSelect, {
    props: { label: 'Badge icon', modelValue, options },
    global: {
      stubs: {
        'q-select': QSelectStub,
        'q-item': { name: 'q-item', template: '<div class="q-item-stub"><slot /></div>' },
        'q-icon': { name: 'q-icon', props: ['name'], template: '<i class="q-icon-stub"><slot /></i>' },
      },
    },
  });

describe('EvanSelect', () => {
  it('renders the option icon image next to the label in the dropdown', () => {
    const wrapper = mountComponent();

    const optionWithIcon = wrapper.findAll('.option')[0];
    const iconEl = optionWithIcon.findComponent({ name: 'q-icon' });
    expect(iconEl.props('name')).toBe(iconBadgeReception);

    const optionWithoutIcon = wrapper.findAll('.option')[1];
    expect(optionWithoutIcon.find('.q-icon-stub').exists()).toBe(false);
  });

  it('shows the icon of the selected value in the closed select', () => {
    const wrapper = mountComponent('reception');

    const selected = wrapper.find('.selected');
    expect(selected.findComponent({ name: 'q-icon' }).props('name')).toBe(iconBadgeReception);
    expect(selected.text()).toContain('Reception');
  });

  it('shows no image when the selected option has no icon', () => {
    const wrapper = mountComponent();

    expect(wrapper.find('.selected .q-icon-stub').exists()).toBe(false);
  });

  it('emits update:modelValue when the value changes', async () => {
    const wrapper = mountComponent();

    wrapper.findComponent({ name: 'q-select' }).vm.$emit('update:modelValue', 'reception');
    await wrapper.vm.$nextTick();

    expect(wrapper.emitted('update:modelValue')).toEqual([['reception']]);
  });
});
