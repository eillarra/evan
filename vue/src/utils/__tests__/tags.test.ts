import { describe, expect, it } from 'vitest';

import { tags_to_dict } from '../tags';

describe('tags_to_dict', () => {
  it('converts a simple key:value pair', () => {
    expect(tags_to_dict(['tag1:value1'])).toEqual({ tag1: 'value1' });
  });

  it('converts multiple pairs', () => {
    expect(tags_to_dict(['tag1:value1', 'tag2:value2'])).toEqual({ tag1: 'value1', tag2: 'value2' });
  });

  it('preserves colons inside double-quoted values and strips the quotes', () => {
    expect(tags_to_dict(['tag3:"hour:min"'])).toEqual({ tag3: 'hour:min' });
  });

  it('returns an empty object for an empty array', () => {
    expect(tags_to_dict([])).toEqual({});
  });

  it('keeps colons in unquoted values joined back together', () => {
    expect(tags_to_dict(['path:a:b:c'])).toEqual({ path: 'a:b:c' });
  });

  it('strips leading and trailing double quotes from a fully-quoted value', () => {
    expect(tags_to_dict(['label:"hello world"'])).toEqual({ label: 'hello world' });
  });

  it('handles a key without a value', () => {
    expect(tags_to_dict(['lonely'])).toEqual({ lonely: '' });
  });

  it('last value wins for duplicate keys', () => {
    expect(tags_to_dict(['k:first', 'k:second'])).toEqual({ k: 'second' });
  });
});
