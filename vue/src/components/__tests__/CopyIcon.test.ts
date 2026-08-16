import { mount } from '@vue/test-utils';
import { beforeEach, describe, expect, it, vi } from 'vitest';

const copyToClipboard = vi.fn();
const notifyInfo = vi.fn();

vi.mock('quasar', () => ({
  copyToClipboard: (text: string) => copyToClipboard(text),
  QIcon: { name: 'QIcon', template: '<i @click="$emit(\'click\', $event)"><slot /></i>', emits: ['click'] },
}));

vi.mock('@/utils/notify', () => ({
  notify: {
    info: (msg: string) => notifyInfo(msg),
  },
}));

vi.mock('vue-i18n', () => ({
  useI18n: () => ({ t: (key: string) => key }),
}));

import CopyIcon from '../CopyIcon.vue';

describe('CopyIcon', () => {
  const mountComponent = (text: string | number = 'hello', iconSize?: string) =>
    mount(CopyIcon, {
      props: { text, ...(iconSize ? { iconSize } : {}) },
    });

  beforeEach(() => {
    copyToClipboard.mockReset();
    notifyInfo.mockReset();
    copyToClipboard.mockResolvedValue(undefined);
  });

  it('copies the text to the clipboard and notifies on click', async () => {
    const wrapper = mountComponent('copy-me');

    await wrapper.find('i').trigger('click');
    await vi.waitFor(() => expect(copyToClipboard).toHaveBeenCalled());

    expect(copyToClipboard).toHaveBeenCalledWith('copy-me');
    expect(notifyInfo).toHaveBeenCalledWith('messages.copied_to_clipboard');
  });

  it('coerces a numeric text to a string before copying', async () => {
    const wrapper = mountComponent(42);

    await wrapper.find('i').trigger('click');
    await vi.waitFor(() => expect(copyToClipboard).toHaveBeenCalled());

    expect(copyToClipboard).toHaveBeenCalledWith('42');
  });
});
