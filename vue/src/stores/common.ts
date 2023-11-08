import { onMounted, onUnmounted, ref } from 'vue';
import { defineStore } from 'pinia';

import { api } from '@/axios';
import { storage } from '@/utils/storage';

interface CountryMap {
  [key: string]: string;
}

export const useCommonStore = defineStore('common', () => {
  const countries = ref<CountryMap | null>(null);
  const now = ref<Date>(new Date());

  async function init() {
    await getCountries();
  }

  async function getCountries() {
    const countriesFound = storage.get('countries');
    if (countriesFound) {
      countries.value = countriesFound;
      return;
    }

    await api.get('../countries/').then((res) => {
      storage.set('countries', res.data, 60 * 60);
      countries.value = res.data;
    });
  }

  onMounted(() => {
    const interval = setInterval(() => {
      now.value = new Date();
    }, 1000);
    onUnmounted(() => clearInterval(interval));
  });

  return {
    init,
    countries,
    now,
  };
});
