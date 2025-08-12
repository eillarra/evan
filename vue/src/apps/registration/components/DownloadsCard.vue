<template>
  <q-card flat bordered square>
    <q-card-section>
      <div class="text-h6">Downloads</div>
      <div class="text-subtitle2">You can download your receipt and certificate here (after the event).</div>
    </q-card-section>
    <q-separator />
    <q-list>
      <q-item
        v-if="registration.receipt_url"
        clickable
        :href="registration.receipt_url"
        target="_blank"
        rel="noopener"
        active-class="bg-ugent text-white"
      >
        <q-item-section>Download receipt (PDF)</q-item-section>
      </q-item>
      <q-item
        v-if="eventIsClosed && registration.certificate_url"
        clickable
        :href="registration.certificate_url"
        target="_blank"
        rel="noopener"
        active-class="bg-ugent text-white"
      >
        <q-item-section>Download certificate of attendance (PDF)</q-item-section>
      </q-item>
    </q-list>
  </q-card>
</template>

<script setup lang="ts">
defineProps<{
  eventIsClosed: boolean;
  registration: Registration;
}>();
</script>
