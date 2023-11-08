import { ref } from 'vue';
import { defineStore } from 'pinia';
import { pick } from 'lodash-es';

import { api } from '@/axios.ts';

export const useUserStore = defineStore('user', () => {
  const user = ref<AuthenticatedUser | null>(null);

  async function init(djangoUser: AuthenticatedUser) {
    user.value = djangoUser;
  }

  async function updateUser(fields: string[]) {
    await api.patch('/user/account/', pick(user.value, fields)).then((res) => {
      user.value = res.data;
      // notify.success('updated');
    });
  }

  return {
    init,
    updateUser,
    user,
  };
});
