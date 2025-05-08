<template>
  <div v-if="!hideTitle" class="row q-col-gutter-sm q-mb-lg">
    <h4 class="col-12 col-md-3 q-mt-none q-mb-none">
      {{ $t('remark', 9) }}
    </h4>
  </div>
  <div v-if="loading" class="flex flex-center q-mt-xl">
    <q-spinner color="grey-3" size="4em" />
  </div>
  <div v-else>
    <div class="row justify-center">
      <div style="width: 100%">
        <q-chat-message
          v-for="remark in sortedRemarks"
          :key="remark.id"
          :name="remark.created_by.name"
          :stamp="remark.stamp"
          :bg-color="remark.is_mine ? 'blue-1' : 'grey-2'"
        >
          <div>
            <q-icon
              v-if="remark.is_mine"
              @click="deleteRemark(remark)"
              :name="iconDelete"
              color="red"
              size="20px"
              class="float-right cursor-pointer q-ml-md"
            />
            {{ remark.text }}
          </div>
        </q-chat-message>
      </div>
    </div>
    <div class="bg-white q-pa-lg">
      <q-page-sticky expand position="bottom" class="bg-white z-top">
        <div class="full-width full-height text-right q-px-lg q-pb-lg">
          <q-input v-model="remarkText" :label="$t('models.remark')" autogrow clearable class="q-mb-md" />
          <visibility-options v-if="visibilityOptions" v-model="remarkTags" :options="visibilityOptions" hide-label />
          <q-btn @click="addRemark" unelevated color="ugent" :label="$t('form.save')" :disable="remarkText == ''" />
        </div>
      </q-page-sticky>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue';
import { useI18n } from 'vue-i18n';
import { usePage } from '@inertiajs/vue3';

import { api } from '@/axios';
import { confirm } from '@/utils/dialog';
import { formatDate } from '@/utils/dates';
import { notify } from '@/utils/notify';

import { iconDelete } from '@/icons';

const { t } = useI18n();

const page = usePage();
const djangoUser = computed<DjangoAuthenticatedUser>(() => page.props.django_user as DjangoAuthenticatedUser);

const props = defineProps<{
  apiEndpoint: ApiEndpoint | null;
  remarkTypes?: Record<string, string>;
  visibilityOptions?: string[];
  hideTitle?: boolean;
}>();

const loading = ref<boolean>(true);
const remarks = ref<Remark[]>([]);
const remarkText = ref<string>('');
const remarkTags = ref<Tags>([]);

const sortedRemarks = computed<Remark[]>(() => {
  let mutable = [...remarks.value];
  return mutable
    .sort((a, b) => b.created_at.localeCompare(a.created_at))
    .map((obj) => ({
      ...obj,
      is_mine: obj.created_by?.id == djangoUser.value.id,
      stamp: formatDate(obj.created_at),
    }));
});

async function fetchRemarks() {
  if (!props.apiEndpoint) return;

  remarks.value = [];
  loading.value = true;

  api.get<Remark[]>(props.apiEndpoint).then((res) => {
    remarks.value = res.data;
    loading.value = false;
  });
}

async function addRemark() {
  if (!props.apiEndpoint) return;

  api
    .post<Remark>(props.apiEndpoint, {
      text: remarkText.value,
      tags: remarkTags.value,
    })
    .then(({ data }) => {
      remarks.value.push({ ...data });
      remarkText.value = '';
      remarkTags.value = [];
      notify.success(t('messages.remark_created'));
    });
}

async function deleteRemark(remark: Remark) {
  confirm(t('messages.remark_confirm_delete'), () => {
    api.delete(remark.self).then(() => {
      remarks.value = remarks.value.filter((obj) => obj.id !== remark.id);
      notify.success(t('messages.remark_deleted'));
    });
  });
}

fetchRemarks();

watch(() => props.apiEndpoint, fetchRemarks);
</script>
