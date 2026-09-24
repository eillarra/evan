import { createI18n } from 'vue-i18n';

import messages from './locales';

export type MessageLanguages = keyof typeof messages;
export type MessageSchema = (typeof messages)['en'];

// See https://vue-i18n.intlify.dev/guide/advanced/typescript.html#global-resource-schema-type-definition
// Empty interfaces are the documented vue-i18n augmentation pattern; the rule was renamed
// from `no-empty-interface` to `no-empty-object-type` in typescript-eslint v8.
/* eslint-disable @typescript-eslint/no-empty-object-type */
declare module 'vue-i18n' {
  export interface DefineLocaleMessage extends MessageSchema {}
  export interface DefineDateTimeFormat {}
  export interface DefineNumberFormat {}
}
/* eslint-enable @typescript-eslint/no-empty-object-type */

export { createI18n, messages };
