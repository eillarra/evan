<template>
  <div>
    <div class="row ugent__submenu q-mb-lg">
      <div class="menu-item">
        <!--<span>Registration</span>-->
      </div>
    </div>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { usePage } from '@inertiajs/vue3';

import { useCommonStore } from '@/stores/common';
import { useUserStore } from '@/stores/user';
import { useStore } from './store';

const page = usePage();
const userStore = useUserStore();
const store = useStore();

const user = computed<AuthenticatedUser>(() => page.props.user as AuthenticatedUser);
const evanEvent = computed<EvanEvent>(() => page.props.event as EvanEvent);
const isPreview = computed<boolean>(() => (page.props.preview as boolean) ?? false);

userStore.setData(user.value);

if (isPreview.value) {
  store.setPreviewData(evanEvent.value);
} else {
  store.setData(evanEvent.value);
}

useCommonStore().setTitle(`${evanEvent.value.name}`);
</script>
