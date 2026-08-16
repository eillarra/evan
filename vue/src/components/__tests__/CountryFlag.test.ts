import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import CountryFlag from '../CountryFlag.vue';

describe('CountryFlag', () => {
  const mountComponent = (code: string | null) => mount(CountryFlag, { props: { code } });

  it('generates the correct flag class for a valid uppercase country code', () => {
    const wrapper = mountComponent('BE');
    expect(wrapper.find('i').classes()).toContain('flag-sprite');
    expect(wrapper.find('i').classes()).toContain('flag-b');
    expect(wrapper.find('i').classes()).toContain('flag-_e');
  });

  it('lowercases the code before computing the class', () => {
    const wrapper = mountComponent('nl');
    expect(wrapper.find('i').classes()).toContain('flag-n');
    expect(wrapper.find('i').classes()).toContain('flag-_l');
  });

  it('falls back to flag-zz when the code is null', () => {
    const wrapper = mountComponent(null);
    const classes = wrapper.find('i').classes();
    expect(classes).toContain('flag-sprite');
    expect(classes).toContain('flag-z');
    expect(classes).toContain('flag-_z');
  });

  it('falls back to flag-zz when the code is an empty string', () => {
    const wrapper = mountComponent('');
    const classes = wrapper.find('i').classes();
    expect(classes).toContain('flag-z');
    expect(classes).toContain('flag-_z');
  });
});
