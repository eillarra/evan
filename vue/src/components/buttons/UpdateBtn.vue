<template>
  <q-btn
    unelevated
    color="ugent"
    :label="computedLabel"
    :loading="loading"
    :disabled="disabled || loading"
    @click="$emit('click')"
    v-bind="$attrs"
  />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { useI18n } from 'vue-i18n';

interface Props {
  loading?: boolean;
  disabled?: boolean;
  label?: string;
  isCreate?: boolean;
}

const props = withDefaults(defineProps<Props>(), {
  loading: false,
  disabled: false,
  label: undefined,
  isCreate: false,
});

const { t } = useI18n();

defineEmits<{
  click: [];
}>();

defineOptions({
  inheritAttrs: false,
});

const computedLabel = computed(() => {
  if (props.label) return props.label;
  return props.isCreate ? t('form.create') : t('form.update');
});
</script>
