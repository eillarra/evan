<template>
  <div class="row ugent__submenu q-mb-lg">
    <div class="menu-item">
      <span>Dashboard</span>
    </div>
  </div>
  <router-view />
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { usePage } from '@inertiajs/vue3';

const page = usePage();
</script>
