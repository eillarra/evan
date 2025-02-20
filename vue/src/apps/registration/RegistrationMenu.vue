<template>
  <q-scroll-area class="fit">
    <div class="q-pb-xl q-pr-md">
      <q-list :dense="$q.screen.gt.sm" class="q-mt-xs">
        <q-item-label header>{{ $t('overview') }}</q-item-label>
        <q-item clickable :to="{ name: 'registration' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconPlanning" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('models.registration') }}</q-item-section>
        </q-item>
        <!--<q-item clickable :to="{ name: 'attendees' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconContact" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('models.committee', 9) }}</q-item-section>
        </q-item>-->
      </q-list>
    </div>
  </q-scroll-area>
</template>

<script setup lang="ts">
import { iconContact, iconPlanning } from '@/icons';
</script>
