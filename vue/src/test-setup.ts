import { config } from '@vue/test-utils';

// Vue attempts to set the "prefix" DOM prop on stubbed <q-input-stub> /
// <q-select-stub> elements (QInput/QSelect expose a "prefix" prop), but
// Element.prefix is read-only in happy-dom, so Vue throws and warns.
// This floods test output with ~1500 lines of noise per run. Filter that
// specific warning only; surface everything else untouched.
config.global.config.warnHandler = (msg: string, _instance: unknown, trace: string) => {
  if (msg.includes('Failed setting prop "prefix"')) {
    return;
  }
  console.warn(msg, trace);
};
