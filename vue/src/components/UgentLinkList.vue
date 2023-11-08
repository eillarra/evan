<style lang="scss">
.ugent__link-list {
  h4 {
    margin: 0 0 10px 0;
  }

  .q-focus-helper {
    display: none;
  }

  .q-item {
    &:hover {
      .q-item__section--main {
        text-decoration: underline;
      }
    }
  }

  .q-item--dense,
  .q-list--dense > .q-item {
    padding: 0;
  }

  .q-item__section--side {
    padding-right: 8px;
  }

  .q-item__section--avatar {
    min-width: auto;
  }
}
</style>

<template>
  <div class="ugent__link-list">
    <h4 v-if="title">{{ title }}</h4>
    <q-list dense>
      <q-item v-for="item in items" :key="item.label" :to="item.to" :href="item.href" :target="item.target">
        <q-item-section avatar>
          <q-icon color="ugent" name="east" size="14px" />
        </q-item-section>
        <q-item-section>{{ item.label }}</q-item-section>
      </q-item>
    </q-list>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  items: {
    label: string;
    href?: string;
    to?: object;
    target?: string;
  }[];
  title?: string;
}>();
</script>
