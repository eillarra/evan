<template>
  <div v-if="evanEvent" class="row q-col-gutter-x-xl">
    <h3 class="text-ugent col-12">Event</h3>
    <div class="col-12 col-md-7">
      <marked-div :text="evanEvent?.presentation" class="q-mb-xl" />
    </div>
    <!--{{ evanEvent }} - {{ user }}-->
  </div>
</template>

<script setup lang="ts">
import { storeToRefs } from 'pinia';

// import { useUserStore } from '@/stores/user';
import { useStore } from '../store';

import MarkedDiv from '@/components/MarkedDiv.vue';

// const userStore = useUserStore();
const store = useStore();

// const { user } = storeToRefs(userStore);
const { evanEvent } = storeToRefs(store);
</script>
