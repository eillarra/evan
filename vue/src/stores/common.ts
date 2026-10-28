import { ref } from 'vue';
import { defineStore } from 'pinia';

import { api } from '@/axios';
import { storage } from '@/utils/storage';

interface CountryMap {
  [key: string]: string;
}

export const useCommonStore = defineStore('common', () => {
  const countries = ref<CountryMap | null>(null);
  const title = ref<string>('Evan');

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

  function setTitle(newTitle: string) {
    title.value = newTitle;
  }

  return {
    init,
    setTitle,
    countries,
    title,
  };
});
