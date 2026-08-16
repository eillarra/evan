import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import AccompanyingPersons from '../AccompanyingPersons.vue';

const socialEvents: Session[] = [
  { id: 1, title: 'Welcome Reception', start_at: '2026-09-01T18:00', extra_attendees_fee: 20 } as unknown as Session,
  { id: 2, title: 'Conference Dinner', start_at: '2026-09-03T19:00', extra_attendees_fee: 45 } as unknown as Session,
  { id: 3, title: 'Free Tour', start_at: '2026-09-05T10:00', extra_attendees_fee: 0 } as unknown as Session,
];

const stubs = {
  'q-card': { template: '<div class="q-card"><slot /></div>' },
  'q-input': { template: '<div class="q-input"><slot name="append" /></div>' },
  'q-btn': { template: '<button @click="$emit(\'click\')"><slot /></button>', emits: ['click'] },
  'q-list': { template: '<div class="q-list"><slot /></div>' },
  'q-item': { template: '<div class="q-item"><slot name="avatar" /><slot /><slot name="side" /></div>' },
  'q-item-section': { template: '<div class="q-item-section"><slot /></div>' },
  'q-item-label': { template: '<span class="q-item-label"><slot /></span>' },
  'q-checkbox': { template: '<input type="checkbox" />' },
  'q-badge': { template: '<span class="q-badge"><slot /></span>' },
  DietarySelect: { template: '<div class="dietary-select" />' },
};

const mountComponent = (modelValue: AccompanyingPerson[] = []) =>
  mount(AccompanyingPersons, {
    props: { modelValue, socialEvents },
    global: { stubs },
  });

describe('AccompanyingPersons', () => {
  it('shows the empty-state message when no accompanying persons are present', () => {
    const wrapper = mountComponent([]);

    expect(wrapper.text()).toContain('No accompanying persons added.');
  });

  it('emits an appended array with a blank person when addPerson is clicked', async () => {
    const wrapper = mountComponent([]);

    await wrapper.find('button').trigger('click');

    const emitted = wrapper.emitted('update:modelValue');
    expect(emitted).toBeTruthy();
    expect(emitted![0][0]).toHaveLength(1);
    expect(emitted![0][0][0]).toEqual({
      name: '',
      selected_social_events: [],
      dietary: 'none',
    });
  });

  it('emits an array without the removed index when removePerson is triggered', async () => {
    const persons: AccompanyingPerson[] = [
      { name: 'Alice', selected_social_events: [1], dietary: 'none' },
      { name: 'Bob', selected_social_events: [2], dietary: 'vegetarian' },
    ];
    const wrapper = mountComponent(persons);

    // The delete button is inside the first person card's q-input append slot.
    const deleteButtons = wrapper.findAll('button');
    await deleteButtons[0].trigger('click');

    const emitted = wrapper.emitted('update:modelValue');
    expect(emitted).toBeTruthy();
    expect(emitted![0][0]).toHaveLength(1);
    expect(emitted![0][0][0].name).toBe('Bob');
  });

  it('computes the total additional fee across all persons and selected events', () => {
    const persons: AccompanyingPerson[] = [
      { name: 'Alice', selected_social_events: [1, 3], dietary: 'none' }, // 20 + 0
      { name: 'Bob', selected_social_events: [2], dietary: 'vegetarian' }, // 45
    ];
    const wrapper = mountComponent(persons);

    expect(wrapper.text()).toContain('65');
  });

  it('skips selected event ids that do not exist in the socialEvents list', () => {
    const persons: AccompanyingPerson[] = [
      { name: 'Alice', selected_social_events: [999], dietary: 'none' }, // 999 not in list
    ];
    const wrapper = mountComponent(persons);

    // Fee badge only renders when totalAdditionalFee > 0, so it should be absent.
    expect(wrapper.text()).not.toContain('Additional fee');
  });

  it('shows zero total when all selected events are free', () => {
    const persons: AccompanyingPerson[] = [
      { name: 'Alice', selected_social_events: [3], dietary: 'none' }, // Free tour, fee 0
    ];
    const wrapper = mountComponent(persons);

    expect(wrapper.text()).not.toContain('Additional fee');
  });
});
