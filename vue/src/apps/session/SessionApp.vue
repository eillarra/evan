<template>
  <div>
    <div class="row ugent__submenu q-mb-lg">
      <div class="menu-item">
        <span>{{ evanEvent.name }} session management</span>
      </div>
    </div>
    <router-view />
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { usePage } from '@inertiajs/vue3';

import { useStore } from './store';

const page = usePage();
const store = useStore();

const evanEvent = computed<EvanEvent>(() => page.props.event as EvanEvent);
const session = computed<Session>(() => page.props.session as Session);
const secret = computed<string>(() => page.props.secret as string);

store.setData(evanEvent.value, session.value, secret.value);
</script>
