<template>
  <span>
    <a class="cursor-pointer">
      <span class="text-uppercase">{{ locale }}</span>
      <q-menu anchor="top end" self="bottom right" :offset="[0, 8]">
        <q-list dense style="min-width: 100px" class="text-body2 q-py-sm">
          <q-item
            v-for="l in locales"
            :key="l.code"
            clickable
            :disable="l.code == props.locale"
            @click="change(l.code)"
          >
            <q-item-section>{{ l.name }}</q-item-section>
          </q-item>
        </q-list>
      </q-menu>
    </a>
    <form ref="localeForm" :action="props.actionUrl" method="post">
      <input type="hidden" name="csrfmiddlewaretoken" :value="csrfToken" />
      <input type="hidden" name="language" :value="locale" />
    </form>
  </span>
</template>

<script setup lang="ts">
import { ref } from 'vue';

const locales = [
  { code: 'en', name: 'English' },
  { code: 'nl', name: 'Nederlands' },
];

const props = defineProps({
  csrfToken: String,
  locale: String,
  actionUrl: {
    type: String,
    default: '/i18n/setlang/',
  },
});

const localeForm = ref();

function change(lang: string) {
  localeForm.value.language.value = lang;
  localeForm.value.submit();
}
</script>
