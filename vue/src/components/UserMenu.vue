<template>
  <a class="cursor-pointer">
    <span v-show="$q.screen.gt.xs">{{ displayName }} &nbsp;</span><q-icon :name="iconAccount" size="xxs" />
    <q-menu anchor="top end" self="bottom right" :offset="[0, 8]" style="min-width: 140px">
      <q-list dense class="text-body2 q-py-sm">
        <q-item clickable tag="a" :href="`/u/dashboard/`">
          <q-item-section>{{ $t('user_menu.dashboard') }}</q-item-section>
        </q-item>
        <q-separator class="q-my-sm" />
        <q-item clickable tag="a" href="/u/logout/">
          <q-item-section>{{ $t('user_menu.logout') }}</q-item-section>
          <q-item-section side><q-icon :name="iconLogout" size="xs" /></q-item-section>
        </q-item>
      </q-list>
    </q-menu>
  </a>
</template>

<script setup lang="ts">
import { computed } from 'vue';

import { iconAccount, iconLogout } from '@/icons';

const props = defineProps<{
  user: DjangoAuthenticatedUser;
}>();

const displayName = computed<string>(() => {
  if (props.user) {
    return `${props.user.first_name} ${props.user.last_name}` || props.user.username;
  }
  return '';
});
</script>
