import { mount } from '@vue/test-utils';
import { describe, expect, it } from 'vitest';

import MarkedDiv from '../MarkedDiv.vue';

describe('MarkedDiv', () => {
  const mountComponent = (text: string) => mount(MarkedDiv, { props: { text } });

  it('renders markdown text as HTML inside a .marked div', () => {
    const wrapper = mountComponent('# Hello');

    const div = wrapper.find('div.marked');
    expect(div.exists()).toBe(true);
    expect(div.html()).toContain('<h1');
    expect(div.html()).toContain('Hello');
  });

  it('renders nothing when text is empty', () => {
    const wrapper = mountComponent('');

    expect(wrapper.find('div.marked').exists()).toBe(false);
  });
});
