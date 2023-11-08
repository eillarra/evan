<style lang="scss">
.ugent__banner .box {
  max-width: 380px;
  margin-left: 0;
  padding: 20px;
  background-color: #1e64c8;
  color: white;

  @media (min-width: 1024px) {
    position: absolute;
    bottom: -30px;
    right: 45px;
  }

  h1 {
    font-size: 38px;
    font-weight: 500;
    line-height: 40px;
    margin-top: 0;
    margin-bottom: 13px;
  }

  h2 {
    font-family: 'UGent Panno SemiLight', 'Arial', sans-serif;
    font-size: 20px;
    font-weight: 400;
    line-height: 30px;
    margin-bottom: 0;
  }
}
</style>

<template>
  <div class="ugent__banner row q-my-xl">
    <div class="col-12 col-md-4 bg-tertiary q-pa-lg">
      <slot></slot>
    </div>
    <div class="col-12 col-md bg-ugent relative-position">
      <q-responsive :ratio="5 / 3.5">
        <slot name="image">
          <img src="https://www.ugent.be/nl/@@images/central_subsite_image" />
        </slot>
      </q-responsive>
      <div v-if="title" class="box">
        <h1>{{ title }}</h1>
        <h2 v-if="subtitle">{{ subtitle }}</h2>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{
  title?: string;
  subtitle?: string;
}>();
</script>
