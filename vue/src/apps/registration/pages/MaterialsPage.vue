<template>
  <div class="row q-col-gutter-sm q-mb-lg">
    <h3 class="text-ugent col-12 col-md-3 q-mb-none use-default-q-btn">
      {{ $t('models.materials') }}
    </h3>
    <div class="col-12">
      <no-results v-if="!materials.length" />
      <q-markup-table v-else dense flat class="use-default-q-btn full-width q-mb-lg text-body1">
        <tbody>
          <tr v-for="material in materials" :key="material.file.id">
            <td>{{ material.session.title }}</td>
            <td>
              <a :href="material.file.file" target="_blank">{{ displayName(material.file.file) }}</a>
            </td>
            <td>{{ material.file.description || '-' }}</td>
          </tr>
        </tbody>
      </q-markup-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { usePage } from '@inertiajs/vue3';

import NoResults from '@/components/NoResults.vue';

const page = usePage();

interface Material {
  session: Session;
  file: RelatedFile;
}

const materials = computed<Material[]>(() => {
  const sessions = (page.props.sessions as Session[]) ?? [];
  return sessions.flatMap((session) => (session.files ?? []).map((file) => ({ session, file })));
});

function displayName(fileUrl: string): string {
  if (!fileUrl) return '';
  return fileUrl.split('/').pop() || fileUrl;
}
</script>
