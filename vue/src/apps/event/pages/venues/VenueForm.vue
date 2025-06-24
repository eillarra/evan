<template>
  <dialog-form :icon="iconVenue" :title="$t('models.venue')" size="md">
    <template #tabs>
      <q-tabs v-model="activeTab" dense narrow-indicator no-caps align="left">
        <q-tab name="general" :label="$t('tabs.general')" />
        <q-tab name="rooms" :label="$t('models.room', 9)" />
      </q-tabs>
    </template>
    <template #page>
      <div class="q-pb-lg q-px-sm">
        <q-tab-panels v-model="activeTab">
          <q-tab-panel name="general">
            <div class="row q-col-gutter-y-sm q-col-gutter-x-md">
              <q-input v-model="formData.name" :label="`${$t('fields.name')} *`" dense class="col-12" />
              <q-input v-model="formData.city" :label="$t('fields.city')" dense class="col-12 col-md-6" />
              <div class="col-12 col-md-6">
                <q-checkbox v-model="formData.is_main" :label="$t('fields.is_main')" />
                <div class="text-caption text-grey-6 q-mt-xs">
                  {{ $t('messages.main_venue_note') }}
                </div>
              </div>
              <q-input
                v-model="formData.website"
                :label="$t('fields.website')"
                type="url"
                dense
                class="col-12 col-md-6"
              />
              <q-input
                v-model="formData.google_place_id"
                :label="$t('fields.google_place_id')"
                dense
                bottom-slots
                class="col-12 col-md-6"
              >
                <template #hint>
                  {{ $t('messages.google_place_id_help') }}.
                  <a
                    href="https://developers.google.com/maps/documentation/places/web-service/place-id"
                    target="_blank"
                    class="text-primary"
                    @click.stop
                  >
                    Find Place IDs here
                  </a>
                </template>
              </q-input>
              <marked-textarea v-model="formData.presentation" :label="$t('fields.presentation')" class="col-12" />
            </div>
          </q-tab-panel>
          <q-tab-panel name="rooms">
            <div class="q-mb-md">
              <div v-if="!props.obj" class="text-grey-6 text-center q-py-md">
                {{ $t('venue.save_first_to_add_rooms') }}
              </div>
              <div v-else-if="roomsData.length === 0" class="text-grey-6 text-center q-py-md">
                {{ $t('venue.no_rooms') }}
              </div>
              <rooms-table v-else :rooms="roomsData" :venue="props.obj" />
            </div>
          </q-tab-panel>
        </q-tab-panels>
      </div>
    </template>
    <template #footer>
      <div class="flex q-gutter-sm q-pa-lg">
        <q-space />
        <q-btn
          v-if="activeTab === 'rooms' && props.obj"
          outline
          color="blue-1"
          :label="`${$t('form.new')} ${$t('models.room').toLocaleLowerCase()}`"
          :icon="iconAdd"
          class="text-ugent"
          @click="createRoomDialogVisible = true"
        />
        <update-btn
          v-else
          @click="createUpdate"
          :disabled="!formData.name"
          :loading="loading"
          :label="props.obj ? $t('form.update') : $t('form.create')"
        />
      </div>
    </template>
  </dialog-form>

  <q-dialog v-model="createRoomDialogVisible">
    <room-form :parent="props.obj" @create:obj="onRoomCreated" />
  </q-dialog>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue';

import { useStore } from '../../store';
import { useMinimumLoading } from '@/composables/useMinimumLoading';

import UpdateBtn from '@/components/buttons/UpdateBtn.vue';
import DialogForm from '@/components/forms/DialogForm.vue';
import MarkedTextarea from '@/components/forms/MarkedTextarea.vue';
import RoomForm from './RoomForm.vue';
import RoomsTable from './RoomsTable.vue';

import { iconVenue, iconAdd } from '@/icons';

const props = defineProps<{
  obj?: Venue;
}>();

const emit = defineEmits<{
  (e: 'create:obj'): void;
  (e: 'update:obj'): void;
}>();

const store = useStore();
const { loading, executeWithMinLoading } = useMinimumLoading();

const activeTab = ref('general');
const createRoomDialogVisible = ref(false);

const formData = ref<VenueData>({
  name: props.obj?.name || '',
  city: props.obj?.city || '',
  presentation: props.obj?.presentation || '',
  is_main: props.obj?.is_main || false,
  website: props.obj?.website || '',
  google_place_id: props.obj?.google_place_id || '',
});

const roomsData = computed(() => {
  if (!props.obj?.id) return [];

  // Find the current venue in the store to get the latest rooms data
  const currentVenue = store.evanEvent?.venues.find((v) => v.id === props.obj?.id);
  return currentVenue?.rooms ? [...currentVenue.rooms].sort((a, b) => a.position - b.position) : [];
});

// Initialize form data from venue if editing

async function createUpdate() {
  if (!formData.value.name) return;

  await executeWithMinLoading(async () => {
    if (props.obj) {
      await store.updateVenue({ ...props.obj, ...formData.value });
      emit('update:obj');
    } else {
      await store.createVenue(formData.value);
      emit('create:obj');
    }
  });
}

function onRoomCreated() {
  createRoomDialogVisible.value = false;
}
</script>
