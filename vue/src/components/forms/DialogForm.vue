<style lang="scss">
.ugent__dialog-layout {
  height: 700px;

  .q-dialog__inner--minimized > & {
    width: 900px !important;
    max-width: 100vw;
  }

  .q-stepper--vertical .q-stepper__tab {
    padding: 12px 24px 12px 20px;
  }

  &.size-xs {
    height: 300px;

    .q-dialog__inner--minimized > & {
      width: 400px !important;
    }
  }

  &.size-sm {
    height: 480px;

    .q-dialog__inner--minimized > & {
      width: 500px !important;
    }
  }
}
</style>

<template>
  <q-layout
    view="hHh lpR fFf"
    container
    class="bg-white ugent__dialog-layout ugent__form"
    :class="{ 'size-sm': size === 'sm', 'size-xs': size === 'xs' }"
  >
    <q-header class="bg-white">
      <q-toolbar class="text-primary q-pt-sm q-pb-xs q-pl-lg q-pr-sm use-default-q-btn">
        <q-icon :name="icon" />
        <q-toolbar-title v-if="title" class="col-10">
          <span>{{ title }}</span
          ><span v-if="subtitle" class="text-caption q-pl-md">{{ subtitle }}</span>
        </q-toolbar-title>
        <q-space />
        <q-btn flat round v-close-popup :icon="iconClose" />
      </q-toolbar>
      <q-toolbar class="text-dark text-body1 q-px-lg" style="min-height: auto">
        <slot name="tabs"></slot>
      </q-toolbar>
    </q-header>
    <q-page-container>
      <q-page>
        <slot name="page"></slot>
      </q-page>
    </q-page-container>
    <q-footer v-if="$slots.footer" class="bg-white text-dark">
      <q-separator />
      <slot name="footer"></slot>
    </q-footer>
  </q-layout>
</template>

<script setup lang="ts">
import { iconClose } from '@/icons';

const props = defineProps<{
  icon: string;
  title: string | undefined;
  subtitle?: string | undefined;
  size?: string;
}>();

const size = props.size || 'md';
</script>
