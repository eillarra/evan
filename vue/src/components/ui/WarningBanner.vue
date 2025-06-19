<template>
  <q-banner dense inline-actions :class="bannerClasses" class="q-pl-md" role="alert">
    <template v-slot:avatar>
      <q-icon :name="iconName" :color="iconColor" size="sm" class="justify-center" />
    </template>
    <slot />
    <template v-if="$slots.action" v-slot:action>
      <slot name="action" />
    </template>
  </q-banner>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import { iconNotifyError, iconNotifyInfo, iconNotifyOk, iconNotifyWarning } from '@/icons';

const props = withDefaults(
  defineProps<{
    type?: 'info' | 'warning' | 'error' | 'success';
    dense?: boolean;
  }>(),
  {
    type: 'info',
    dense: true,
  },
);

const typeConfig = {
  info: {
    icon: iconNotifyInfo,
    color: 'ugent',
    bgClass: 'bg-blue-1',
    textClass: 'text-ugent',
  },
  warning: {
    icon: iconNotifyWarning,
    color: 'orange',
    bgClass: 'bg-orange-1',
    textClass: 'text-dark',
  },
  error: {
    icon: iconNotifyError,
    color: 'red',
    bgClass: 'bg-red-1',
    textClass: 'text-red-9',
  },
  success: {
    icon: iconNotifyOk,
    color: 'green',
    bgClass: 'bg-green-1',
    textClass: 'text-green-9',
  },
};

const config = computed(() => typeConfig[props.type]);

const iconName = computed(() => config.value.icon);
const iconColor = computed(() => config.value.color);

const bannerClasses = computed(() => [config.value.bgClass, config.value.textClass, { dense: props.dense }]);
</script>
