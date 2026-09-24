<template>
  <ugent-banner :title="event.name" :subtitle="event.full_name">
    <template #default>
      <p class="q-mb-none">{{ event.dates_display }}</p>
      <p class="q-mb-none">{{ event.city }}, {{ event.country.name }}</p>
    </template>
    <template #image>
      <img src="@/assets/hetpand.jpg" />
    </template>
  </ugent-banner>
  <div class="q-px-lg q-pb-xl">
    <marked-div :text="event.presentation" class="q-mb-xl" />
    <div class="row q-gutter-sm items-center">
      <ugent-btn
        v-if="event.registration_url"
        :label="$t('public_event.register')"
        color="yellow"
        :href="event.registration_url"
      />
      <ugent-btn v-if="canManage" :label="$t('public_event.manage')" outline color="yellow" :href="event.manage_url" />
      <a v-if="event.website" :href="event.website" class="q-ml-sm evan-public-event__website">
        {{ event.website }}
      </a>
    </div>
    <p v-if="event.email" class="q-mt-lg q-mb-none">{{ $t('public_event.contact') }}: {{ event.email }}</p>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { usePage } from '@inertiajs/vue3';

import MarkedDiv from '@/components/MarkedDiv.vue';
import UgentBanner from '@/components/UgentBanner.vue';
import UgentBtn from '@/components/UgentBtn.vue';

const page = usePage();

const event = computed<EvanEvent>(() => page.props.event as EvanEvent);
const canManage = computed<boolean>(() => page.props.can_manage as boolean);
</script>
