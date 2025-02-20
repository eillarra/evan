import { shallowRef } from 'vue';
import { defineStore } from 'pinia';

import { api } from '@/axios.ts';

export const useUserStore = defineStore('user', () => {
  const user = shallowRef<AuthenticatedUser | null>(null);

  async function setData(inertiaUser: AuthenticatedUser) {
    user.value = inertiaUser;
    await init();
  }

  async function init() {}

  async function updateUser(data: Partial<UserData>) {
    if (!user.value) return;
    await api.patch(user.value.self, data).then((res) => {
      user.value = res.data;
    });
  }

  return {
    init,
    setData,
    updateUser,
    user,
  };
});
