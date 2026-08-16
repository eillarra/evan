import { beforeEach, describe, expect, it, vi } from 'vitest';

// In-memory LocalStorage backing for the quasar wrapper.
const store = new Map<string, unknown>();

vi.mock('quasar', () => ({
  LocalStorage: {
    clear: () => store.clear(),
    getAllKeys: () => Object.keys(Object.fromEntries(store)),
    getItem: (key: string) => store.get(key) ?? null,
    remove: (key: string) => {
      store.delete(key);
    },
    set: (key: string, value: unknown) => {
      store.set(key, value);
    },
  },
}));

import { storage } from '../storage';

describe('storage', () => {
  beforeEach(() => {
    store.clear();
  });

  it('round-trips a value set without a ttl and never expires', () => {
    storage.set('k', { a: 1 });
    expect(storage.get('k')).toEqual({ a: 1 });
  });

  it('returns null for a missing key', () => {
    expect(storage.get('missing')).toBeNull();
  });

  it('returns null and removes the key after its ttl expires', () => {
    const now = Date.now();
    vi.useFakeTimers();
    vi.setSystemTime(now);

    storage.set('ephemeral', 'value', 60); // 60s ttl
    expect(storage.get('ephemeral')).toBe('value');

    vi.advanceTimersByTime(61_000);
    expect(storage.get('ephemeral')).toBeNull();
    expect(store.has('ephemeral')).toBe(false);

    vi.useRealTimers();
  });

  it('removes a single key', () => {
    storage.set('a', 1);
    storage.remove('a');
    expect(storage.get('a')).toBeNull();
  });

  it('removes an array of keys', () => {
    storage.set('a', 1);
    storage.set('b', 2);
    storage.remove(['a', 'b']);
    expect(storage.get('a')).toBeNull();
    expect(storage.get('b')).toBeNull();
  });

  it('clears all keys', () => {
    storage.set('a', 1);
    storage.clear();
    expect(storage.get('a')).toBeNull();
  });

  it('clearExpired sweeps expired keys but leaves fresh ones', () => {
    const now = Date.now();
    vi.useFakeTimers();
    vi.setSystemTime(now);

    storage.set('fresh', 'value', 3600);
    storage.set('stale', 'value', 1);

    vi.advanceTimersByTime(2_000);
    storage.clearExpired();

    expect(storage.get('fresh')).toBe('value');
    expect(storage.get('stale')).toBeNull();

    vi.useRealTimers();
  });
});
