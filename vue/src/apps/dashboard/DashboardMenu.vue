<template>
  <q-scroll-area class="fit">
    <div class="q-pb-xl q-pr-md">
      <q-list :dense="$q.screen.gt.sm" class="q-mt-xs">
        <q-item-label header>Dashboard</q-item-label>
        <q-item clickable :to="{ name: 'registrations' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconRegistrations" size="xs" />
          </q-item-section>
          <q-item-section>Your registrations</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'events' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconEvent" size="xs" />
          </q-item-section>
          <q-item-section>Your events</q-item-section>
        </q-item>
        <!--<q-item-label header>Account</q-item-label>
        <q-item clickable :to="{ name: 'emails' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconEmails" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('fields.email', 9) }}</q-item-section>
        </q-item>-->
      </q-list>
    </div>
  </q-scroll-area>
</template>

<script setup lang="ts">
import { iconEvent, iconRegistrations } from '@/icons';
</script>
