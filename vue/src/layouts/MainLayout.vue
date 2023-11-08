<template>
  <div class="container">
    <q-layout view="hhh lpR fff">
      <q-header class="row ugent__header bg-white">
        <q-toolbar class="col-3 col-md-2 bg-white q-pl-none">
          <a href="/" class="q-mr-sm">
            <img src="@/assets/ugent_en.svg" class="logo q-mr-sm" />
          </a>
        </q-toolbar>
        <q-toolbar
          class="col-9 col-md-10 text-white q-pl-md q-pb-sm bg-ugent"
          :class="{ 'q-pl-lg': $q.screen.gt.sm, 'bg-ge': props.django_env == 'staging' }"
          style="align-items: flex-end"
        >
          <h2 class="text-uppercase q-ma-none">Evan</h2>
          <div
            class="absolute-top-right header-links text-white q-py-sm q-px-md q-gutter-x-lg"
            :class="{ 'q-py-md q-px-lg': $q.screen.gt.sm }"
          >
            <a v-if="django_user && django_user.is_staff" href="/admin/">Admin</a>
            <user-menu v-if="django_user" :user="django_user" />
            <a v-else href="/u/ugent/login/">Sign in <q-icon :name="iconLogin" size="xxs"></q-icon></a>
          </div>
        </q-toolbar>
      </q-header>

      <q-drawer
        show-if-above
        v-model="leftDrawer"
        :side="$q.screen.lt.md ? 'right' : 'left'"
        :elevated="$q.screen.lt.md"
        class="q-pt-lg text-weight-medium"
        :width="210"
      >
        <router-view name="drawer" />
      </q-drawer>

      <q-page-container>
        <q-btn
          v-show="$q.screen.lt.md"
          @click="leftDrawer = !leftDrawer"
          flat
          :icon="iconMenu"
          color="ugent"
          class="float-right q-ml-md"
          size="13px"
        ></q-btn>
        <router-view />
        <div class="q-py-lg" />
      </q-page-container>

      <q-footer
        class="ugent__footer bg-ugent text-white q-py-lg q-mt-xl full-width q-px-md"
        :class="{ 'q-pl-lg': $q.screen.gt.sm, 'bg-ge': props.django_env == 'staging' }"
      >
        <div class="row justify-between text-body2">
          <div class="col-12 col-md">
            <p>
              Version&nbsp;<a
                v-if="git_commit_hash && django_user && django_user.is_staff"
                :href="`https://github.ugent.be/eillarra/evan/tree/${git_commit_hash}`"
                >{{ version }}</a
              ><span v-else>{{ version }}</span>
            </p>
          </div>
          <div class="col-12 col-md-9 q-pr-sm">
            <ul :class="{ 'text-right q-gutter-x-md': $q.screen.gt.sm }">
              <li :class="{ inline: $q.screen.gt.sm }">
                <a :href="`mailto:${helpdeskEmail}`">Feedback</a>
              </li>
              <li :class="{ inline: $q.screen.gt.sm }">
                <a href="https://www.ugent.be/en/ghentuniv/privacy/privacystatement.htm" target="_blank" rel="noopener"
                  >Privacy</a
                >
              </li>
              <li :class="{ inline: $q.screen.gt.sm }">
                <span
                  >&copy; {{ year }}
                  <a :href="`https://www.ugent.be/ea/${django_locale}`" target="_blank" rel="noopener"
                    >Department of Electronics and Information Systems (ELIS)</a
                  >, <span class="text-no-wrap">Ghent University</span></span
                >
              </li>
            </ul>
          </div>
        </div>
      </q-footer>
    </q-layout>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue';

import UserMenu from '@/components/UserMenu.vue';

import { iconLogin, iconMenu } from '@/icons';

// get basic info from Django
const props = defineProps<{
  django_csrf_token: string;
  django_debug: boolean;
  django_env: string;
  django_locale: string;
  django_user: DjangoAuthenticatedUser | null;
  git_commit_hash: string | null;
}>();

const version = props.git_commit_hash?.substring(0, 7) || 'DEV';
const helpdeskEmail = 'evan@ugent.be';
const year = new Date().getFullYear();

const leftDrawer = ref(false);
</script>
