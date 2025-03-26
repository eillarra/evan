<template>
  <full-dialog :icon="iconEmail" :title="$t('fields.email')" class="small" hide-drawer>
    <template #tabs>
      <table class="q-px-md q-py-sm q-mt-sm q-mb-lg bg-grey-2 full-width">
        <tbody>
          <tr>
            <td class="text-no-wrap q-td q-table--col-auto-width q-pr-md">
              <strong>{{ $t('fields.sent_at') }}:</strong>
            </td>
            <td colspan="2">{{ formatDate(email.sent_at) }}</td>
          </tr>
          <tr>
            <td class="text-no-wrap q-td q-table--col-auto-width q-pr-md">
              <strong>{{ $t('fields.sent_to') }}:</strong>
            </td>
            <td>
              <span>{{ toNameEmails }}</span>
            </td>
            <td class="q-td q-table--col-auto-width">
              <q-icon @click="copyText(toNameEmails)" :name="iconCopy" size="14px" class="cursor-pointer q-ml-xs" />
            </td>
          </tr>
          <tr>
            <td>
              <strong>{{ $t('fields.subject') }}:</strong>
            </td>
            <td colspan="2">{{ email.subject }}</td>
          </tr>
          <tr>
            <td><strong>Tags:</strong></td>
            <td colspan="2">
              <div class="q-gutter-xs">
                <q-badge v-for="tag in sortedTags" :key="tag" :label="tag" outline dense color="dark" />
              </div>
            </td>
          </tr>
        </tbody>
      </table>
    </template>
    <template #page>
      <div class="q-mx-lg q-pb-xl">
        <marked-div :text="email.body" class="bg-grey-1 q-mt-sm q-pa-md" />
      </div>
    </template>
  </full-dialog>
</template>

<script setup lang="ts">
import { computed, ref, onMounted } from 'vue';
import { useI18n } from 'vue-i18n';
import { copyToClipboard } from 'quasar';

import { api } from '@/axios.ts';
import { notify } from '@/utils/notify';
import { formatDate } from '@/utils/dates';

import FullDialog from '@/components/FullDialog.vue';
import MarkedDiv from '@/components/MarkedDiv.vue';

import { iconCopy, iconEmail } from '@/icons';

const { t } = useI18n();

const props = defineProps<{
  obj: Email;
  internships?: Internship[];
}>();

const extraData = ref();
const email = computed<FullEmail>(() => ({
  ...props.obj,
  ...extraData.value,
}));

const userDict = computed<Record<EmailAddress, UserTiny>>(() => {
  const userDict: Record<EmailAddress, UserTiny> = {};

  if (extraData.value) {
    extraData.value.internship?.mentors.forEach((mentor: Mentor) => {
      userDict[mentor.user.email] = mentor.user;
    });
    const studentUser = extraData.value.internship?.Student?.User;
    if (studentUser) {
      userDict[studentUser.email] = studentUser;
    }
  }

  return userDict;
});

const toNameEmails = computed<string>(() => {
  // if extraData.value is not yet set, return the original value
  if (!extraData.value || !Object.keys(userDict.value).length) {
    return props.obj.to.join(', ');
  }
  // else look the extraData.internship.mentors data and return matching names and emails, or just original email
  return props.obj.to
    .map((to: string) => {
      const user = userDict.value[to];
      return user ? `${user.name} <${to}>` : to;
    })
    .join(', ');
});

const sortedTags = computed<string[]>(() => {
  const tagsCopy = [...props.obj.tags];
  return tagsCopy.sort();
});

function copyText(text: string) {
  copyToClipboard(text).then(() => {
    notify.info(t('copied_to_clipboard'));
  });
}

function fetchEmail() {
  api.get(props.obj.self).then((response) => {
    extraData.value = response.data;
  });
}

onMounted(() => {
  fetchEmail();
});
</script>
