<template>
  <q-btn
    unelevated
    color="ugent"
    :label="computedLabel"
    :loading="loading || internalLoading"
    :disabled="disabled || loading || internalLoading"
    @click="handleClick"
    v-bind="$attrs"
  />
</template>

<script setup lang="ts">
import { computed, ref } from 'vue';
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

const emit = defineEmits<{
  click: [];
}>();

defineOptions({
  inheritAttrs: false,
});

const internalLoading = ref(false);

function handleClick() {
  if (props.loading || props.disabled || internalLoading.value) return;

  // Set internal loading immediately to prevent race conditions before
  // the parent has a chance to set its own loading state.
  internalLoading.value = true;

  emit('click');

  setTimeout(() => {
    internalLoading.value = false;
  }, 100);
}

const computedLabel = computed(() => {
  if (props.label) return props.label;
  return props.isCreate ? t('form.create') : t('form.update');
});
</script>
