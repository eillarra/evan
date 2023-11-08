<template>
  <ugent-banner title="Evan" :subtitle="$t('home.presentation')">
    <template #default>
      <ugent-btn v-if="user" :label="$t('user_menu.dashboard')" color="yellow" href="/u/dashboard/" />
      <div v-else class="fit column justify-between">
        <form method="post" action="/u/login/" class="q-mb-xl">
          <input type="hidden" name="csrfmiddlewaretoken" :value="csrfToken" />
          <ugent-btn :label="$t('home.login')" color="yellow" type="submit" />
        </form>
      </div>
    </template>
    <template #image>
      <img src="@/assets/hetpand.jpg" />
    </template>
  </ugent-banner>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { usePage } from '@inertiajs/vue3';

import UgentBanner from '@/components/UgentBanner.vue';
import UgentBtn from '@/components/UgentBtn.vue';

const page = usePage();

const user = computed<DjangoAuthenticatedUser>(() => page.props.django_user as DjangoAuthenticatedUser);
const csrfToken = computed<string>(() => page.props.django_csrf_token as string);
</script>
