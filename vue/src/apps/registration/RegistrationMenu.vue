<template>
  <q-scroll-area class="fit">
    <div class="q-pb-xl q-pr-md">
      <q-list :dense="$q.screen.gt.sm" class="q-mt-xs">
        <q-item-label header>{{ $t('overview') }}</q-item-label>
        <q-item clickable :to="{ name: 'registration' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconRegistration" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('models.registration') }}</q-item-section>
        </q-item>
        <q-item
          clickable
          :href="registration ? `../${registration.uuid}/payment/` : '#'"
          active-class="bg-ugent text-white"
          :disable="registration === null"
        >
          <q-item-section avatar>
            <q-icon :name="iconPayment" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('payment') }}</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'profile' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconAccount" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('user_menu.profile') }}</q-item-section>
        </q-item>
        <q-item-label header>{{ $t('about') }}</q-item-label>
        <q-item clickable :to="{ name: 'event' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconEvent" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('models.event') }}</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'albums' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconPhotoAlbum" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('album', 9) }}</q-item-section>
        </q-item>
      </q-list>
    </div>
  </q-scroll-area>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia';

import { useStore } from './store';

import { iconAccount, iconEvent, iconPayment, iconRegistration, iconPhotoAlbum } from '@/icons';

const store = useStore();

const { registration } = storeToRefs(store);
</script>
