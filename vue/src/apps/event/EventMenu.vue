<template>
  <q-scroll-area class="fit">
    <div class="q-pb-xl q-pr-md">
      <q-list :dense="$q.screen.gt.sm" class="q-mt-xs">
        <q-item-label header>{{ $t('overview') }}</q-item-label>
        <q-item clickable :to="{ name: 'stats' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconStats" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('stats') }}</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'registrations' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconRegistrations" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('models.registration', 9) }}</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'coupons' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconCoupon" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('models.coupon', 9) }}</q-item-section>
        </q-item>
        <q-item-label header>{{ $t('event_management') }}</q-item-label>
        <q-item clickable :to="{ name: 'event' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconEvent" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('models.event') }}</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'dates' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconImportantDates" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('models.important_date', 9) }}</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'venues' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconVenue" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('models.venues_rooms') }}</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'taxonomy' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconLabel" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('models.tracks_topics') }}</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'sessions' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconPlanning" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('models.session', 9) }}</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'keynotes' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconKeynote" size="xs" />
          </q-item-section>
          <q-item-section>— {{ $t('models.keynote', 9) }}</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'papers' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconPaper" size="xs" />
          </q-item-section>
          <q-item-section>— {{ $t('models.paper', 9) }}</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'emailplans' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconInfo" size="xs"></q-icon>
          </q-item-section>
          <q-item-section>{{ $t('send_emails') }}</q-item-section>
        </q-item>
        <q-item-label header>Website</q-item-label>
        <q-item clickable :to="{ name: 'contents' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconContent" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('models.content', 9) }}</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'sponsors' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconSponsor" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('models.sponsor', 9) }}</q-item-section>
        </q-item>
        <q-item clickable :to="{ name: 'albums' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconPhotoAlbum" size="xs" />
          </q-item-section>
          <q-item-section>{{ $t('album', 9) }}</q-item-section>
        </q-item>
        <q-item-label header>Logs</q-item-label>
        <q-item clickable :to="{ name: 'emails' }" active-class="bg-ugent text-white">
          <q-item-section avatar>
            <q-icon :name="iconEmails" size="xs"></q-icon>
          </q-item-section>
          <q-item-section>{{ $t('fields.email', 9) }}</q-item-section>
        </q-item>
      </q-list>
    </div>
  </q-scroll-area>
</template>

<script setup lang="ts">
import {
  iconContent,
  iconCoupon,
  iconEmails,
  iconEvent,
  iconImportantDates,
  iconInfo,
  iconKeynote,
  iconLabel,
  iconPaper,
  iconPhotoAlbum,
  iconPlanning,
  iconRegistrations,
  iconSponsor,
  iconStats,
  iconVenue,
} from '@/icons';
</script>
