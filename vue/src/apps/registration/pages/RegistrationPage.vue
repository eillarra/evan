<style scoped>
.registration-summary-sidebar {
  align-self: flex-start;
}

@media (min-width: 1024px) {
  .registration-summary-sidebar {
    position: sticky;
    top: 16px;
  }
}
</style>

<template>
  <q-page v-if="!loading">
    <div class="row q-col-gutter-x-xl">
      <h3 class="text-ugent col-12">
        <span v-if="registration">My registration</span>
        <span v-else>New registration</span>
      </h3>
      <div v-if="mutableRegistration" class="col-12 col-md-7">
        <profile-info-fields v-if="user" v-model:user="user" />

        <evan-section-title>Registration fee</evan-section-title>
        <fee-form-component
          v-if="evanEvent?.registration_configuration?.fee_selection"
          v-model:fee="mutableRegistration.fee_type"
          v-model:extraData="mutableRegistration.extra_data"
          :fee-config="evanEvent?.registration_configuration?.fee_selection"
          :valid-fees="validFees"
          :fees="evanEvent?.fees"
        />
        <q-select
          v-else
          v-model="mutableRegistration.fee_type"
          :options="feeOptions"
          label="Fee"
          dense
          options-dense
          class="col-12"
          map-options
          emit-value
        />
        <p v-if="selectedFee" class="bg-blue-1 text-black q-my-md q-pa-md">
          <q-badge class="float-right text-body1 text-white text-weight-bold"
            >€ {{ isEarly ? selectedFee.early_value || selectedFee.value : selectedFee.value }}</q-badge
          >
          <small>
            <span>{{ selectedFee.notes }}</span>
            <strong v-if="selectedFee.remaining_capacity !== null">
              <span> - </span>
              <template v-if="selectedFee.is_sold_out">{{ $t('fee.sold_out') }}</template>
              <template v-else>
                {{
                  selectedFee.remaining_capacity === 1
                    ? $t('fee.remaining_one')
                    : $t('fee.remaining', { n: selectedFee.remaining_capacity })
                }}</template
              >
            </strong>
          </small>
        </p>

        <template v-if="registrationFormFields.length">
          <evan-section-title>Additional registration information</evan-section-title>
          <registration-form-fields
            v-model:extraData="mutableRegistration.extra_data"
            :fields="registrationFormFields"
            :fee-type="mutableRegistration.fee_type"
          />
        </template>

        <template v-if="socialEvents.length > 0 && !isOnlineAttendee">
          <evan-section-title>Social events</evan-section-title>
          <p>Choose the social events you would like to attend:</p>
          <q-list dense>
            <q-item v-for="session in socialEvents" :key="session.id" tag="label">
              <q-item-section avatar>
                <q-checkbox v-model="selectedSocialEvents" :val="session.id" keep-color />
              </q-item-section>
              <q-item-section>
                <q-item-label>{{ session.title }}</q-item-label>
                <q-item-label caption>{{ formatDate(session.start_at || '', 'dddd, MMMM D, YYYY') }}</q-item-label>
              </q-item-section>
              <q-item-section v-show="selectedFee" side>
                <q-badge v-if="includedSocialEvents.includes(session.id)" outline color="primary" label="Included" />
                <q-badge v-else color="primary" :label="`+ € ${session.extra_attendees_fee}`" />
              </q-item-section>
            </q-item>
          </q-list>
          <p v-if="socialEventFee" class="bg-blue-1 text-black q-my-md q-pa-md">
            <q-badge class="float-right text-body1 text-white text-weight-bold">€ {{ socialEventFee }}</q-badge>
            <small>Additional fee for selected social events</small>
          </p>
        </template>

        <template v-if="user && !isOnlineAttendee">
          <evan-section-title>Special needs</evan-section-title>
          <p>
            The following information will only be used to provide you with a better experience during physical events.
            We will <strong>never</strong> share your personal information with third parties.
          </p>
          <div class="row q-col-gutter-y-sm q-col-gutter-x-md items-start q-mb-sm">
            <dietary-select v-model="user.extra_data.dietary" class="col-12" />
            <q-input
              v-model="user.extra_data.special_needs"
              label="Any other special needs (dietary, access restrictions, etc)?"
              dense
              class="col-12"
            />
          </div>
        </template>

        <template v-if="!isOnlineAttendee">
          <evan-section-title>Travel visa</evan-section-title>
          <q-list dense>
            <q-item tag="label">
              <q-item-section avatar>
                <q-checkbox v-model="mutableRegistration.visa_requested" keep-color />
              </q-item-section>
              <q-item-section>
                <q-item-label>I require an Invitation Letter for my visa application</q-item-label>
              </q-item-section>
            </q-item>
          </q-list>
        </template>

        <template
          v-if="
            socialEvents.length > 0 && !isOnlineAttendee && evanEvent.registration_configuration.accompanying_persons
          "
        >
          <evan-section-title>Accompanying persons</evan-section-title>
          <accompanying-persons v-model="accompaningPersons" :social-events="socialEvents" />
        </template>

        <evan-section-title>Privacy</evan-section-title>
        <q-list dense>
          <q-item tag="label">
            <q-item-section avatar>
              <q-checkbox v-model="allowContact" keep-color />
            </q-item-section>
            <q-item-section>
              <q-item-label>Allow other attendees to contact me</q-item-label>
              <q-item-label caption
                >Attendees can send you messages through our internal contact form.
                <strong>We will never share your email directly.</strong></q-item-label
              >
            </q-item-section>
          </q-item>

          <q-item tag="label">
            <q-item-section avatar>
              <q-checkbox v-model="sponsorEmailConsent" keep-color />
            </q-item-section>
            <q-item-section>
              <q-item-label>Allow sponsors to contact me</q-item-label>
              <q-item-label caption>We will share your name, affiliation, and email with event sponsors</q-item-label>
            </q-item-section>
          </q-item>

          <q-item v-if="!isOnlineAttendee" tag="label">
            <q-item-section avatar>
              <q-checkbox v-model="photoConsent" keep-color />
            </q-item-section>
            <q-item-section>
              <q-item-label>I do not want my photos taken during the event</q-item-label>
              <q-item-label caption
                >We may photograph the event and use photos in official materials and social media</q-item-label
              >
            </q-item-section>
          </q-item>
        </q-list>

        <ugent-btn
          @click="saveRegistration"
          :label="registration ? $t('form.update') : $t('form.create')"
          color="primary"
          class="q-mt-xl"
          :disable="!formIsValid || preview || saving"
          :loading="saving"
        />
        <q-space class="q-mb-xl" />
      </div>
      <div
        v-if="mutableRegistration || preview || paymentReminderDemo"
        class="col-12 col-md registration-summary-sidebar"
      >
        <div v-if="preview && !registration" class="bg-orange-1 q-pa-md q-mb-md font-weight-bold">
          This registration form is read-only. For preview purposes only.
        </div>
        <div class="bg-grey-1 q-py-lg q-px-md">
          <div class="row items-start q-mb-md">
            <evan-section-title class="col text-no-wrap" first>Summary</evan-section-title>
            <div class="q-ml-auto flex items-center">
              <q-badge v-if="selectedFee" outline color="primary" :label="isEarly ? 'Early bird' : 'Regular'" />
            </div>
          </div>

          <div v-if="!selectedFee" class="text-body2 text-grey-6 q-mb-md">Choose a fee.</div>
          <div v-if="selectedFee" class="text-body2">
            <div class="row items-center q-mb-sm">
              <div class="col">{{ selectedFee.notes }}</div>
              <div class="col-auto text-weight-bold">
                € {{ isEarly && selectedFee.early_value ? selectedFee.early_value : selectedFee.value }}
              </div>
            </div>

            <div
              v-for="event in socialEvents"
              :key="event.id"
              v-show="selectedSocialEvents.includes(event.id)"
              class="row items-center q-mb-sm"
            >
              <div class="col">
                {{ event.title }} <span class="text-grey-7">({{ formatDate(event.start_at || '', 'ddd') }})</span>
              </div>
              <div class="col-auto text-weight-bold">
                <span v-if="includedSocialEvents.includes(event.id)">Included</span>
                <span v-else>€ {{ event.extra_attendees_fee }}</span>
              </div>
            </div>

            <div v-if="accompanyingPersonsFee > 0" class="row items-center q-mb-sm">
              <div class="col">Accompanying persons</div>
              <div class="col-auto text-weight-bold">€ {{ accompanyingPersonsFee }}</div>
            </div>

            <q-separator class="q-my-sm" />

            <div class="row items-center">
              <div class="col text-weight-bold">Total</div>
              <div class="col-auto text-h6 text-weight-bold text-ugent">€ {{ totalFee }}</div>
            </div>
          </div>

          <div v-if="registration" class="q-mt-xl">
            <q-separator class="q-my-md" />
            <div class="text-caption text-grey-7">Registration code</div>
            <div class="text-mono text-caption q-mt-sm">{{ registration.uuid }}</div>
            <div class="text-caption text-grey-7 q-mt-md">Updated</div>
            <div class="text-caption">{{ formatDate(registration.updated_at, 'LLL d, yyyy HH:mm') }}</div>
          </div>
        </div>

        <div
          v-if="showPaymentReminderBox"
          class="bg-orange-1 text-dark text-body2 q-pa-md q-mt-md"
          data-testid="payment-reminder-box"
        >
          <div class="text-weight-bold">Payment required</div>
          <div class="q-mt-xs">Your registration is saved, but payment is still pending.</div>
          <div v-if="paymentDueAmount > 0" class="row items-baseline q-gutter-x-xs no-wrap">
            <div class="text-grey-8">Amount due:</div>
            <div class="text-weight-bold text-no-wrap">€ {{ paymentDueAmount }}</div>
          </div>
          <div class="q-mt-md">
            <q-btn
              v-if="registration && !registration.invoice_requested"
              :href="registration.payment_url"
              color="primary"
              unelevated
              no-caps
              label="Complete payment"
            />
            <q-btn
              v-else-if="paymentReminderDemo"
              color="primary"
              unelevated
              no-caps
              label="Complete payment"
              disable
            />
            <div v-else class="text-caption text-grey-8 q-mt-xs">
              Invoice requested. We will process your invoice request as soon as possible.
            </div>
          </div>
        </div>
      </div>
    </div>
  </q-page>
</template>

<script setup lang="ts">
import { computed, ref, watch, triggerRef } from 'vue';
import { storeToRefs } from 'pinia';
import { usePage } from '@inertiajs/vue3';
import { useI18n } from 'vue-i18n';

import { useUserStore } from '@/stores/user';
import { formatDate } from '@/utils/dates';
import { normalizeNameIfAllCaps } from '@/utils/nameNormalization';
import { useStore } from '../store';

import DietarySelect from '@/components/DietarySelect.vue';
import AccompanyingPersons from '../components/AccompanyingPersons.vue';
import FeeFormComponent from '../components/FeeFormComponent.vue';
import ProfileInfoFields from '../components/ProfileInfoFields.vue';
import RegistrationFormFields from '../components/RegistrationFormFields.vue';

const { t } = useI18n();

const defaultUserExtraData = (): UserExtraData => ({
  gender: '',
  dietary: 'none',
  special_needs: null,
  connect: false,
});

const page = usePage();
const userStore = useUserStore();
const store = useStore();

const { user } = storeToRefs(userStore);
const { loading, evanEvent, registration } = storeToRefs(store);

const preview = computed<boolean>(() => (page.props.preview as boolean) ?? false);
const paymentReminderDemo = computed<boolean>(() => {
  if (typeof window === 'undefined') {
    return false;
  }

  const query = new URLSearchParams(window.location.search);
  const value = query.get('paymentReminderDemo')?.toLowerCase();

  return value === '1' || value === 'true' || value === 'yes';
});

const sessions = computed<Session[]>(() => page.props.sessions as Session[]);

const isEarly = computed<boolean>(() => {
  const deadline = registration.value ? new Date(registration.value.created_at) : new Date();
  return new Date(evanEvent.value?.registration_early_deadline || '') > deadline;
});
const socialEvents = computed<Session[]>(() => sessions.value?.filter((s: Session) => s.is_social_event) || []);
const includedSocialEvents = computed<number[]>(() => selectedFee.value?.config.included_social_events || []);

const mutableRegistration = ref<RegistrationData | undefined>(undefined);
const saving = ref<boolean>(false);
const selectedFee = computed<Fee | undefined>(() => {
  return evanEvent.value?.fees.find((f: Fee) => f.type == mutableRegistration.value?.fee_type) || undefined;
});
const isOnlineAttendee = computed<boolean>(() => !!(evanEvent.value?.is_virtual || selectedFee.value?.online_only));
const selectedSocialEvents = ref<number[]>([]);
const accompaningPersons = ref<AccompanyingPerson[]>([]);

const sponsorEmailConsent = computed<boolean>({
  get: () => mutableRegistration.value?.extra_data?._internal?.share_email_with_sponsors ?? false,
  set: (value: boolean) => {
    if (mutableRegistration.value) {
      mutableRegistration.value.extra_data._internal = {
        ...mutableRegistration.value.extra_data._internal,
        share_email_with_sponsors: value,
      };
    }
  },
});

const photoConsent = computed<boolean>({
  get: () => !(mutableRegistration.value?.extra_data?._internal?.allow_photo_sharing ?? true),
  set: (value: boolean) => {
    if (mutableRegistration.value) {
      mutableRegistration.value.extra_data._internal = {
        ...mutableRegistration.value.extra_data._internal,
        allow_photo_sharing: !value,
      };
    }
  },
});

const allowContact = computed<boolean>({
  get: () => user.value?.extra_data?.connect ?? false,
  set: (value: boolean) => {
    if (user.value) {
      const extraData = user.value.extra_data ? { ...user.value.extra_data } : defaultUserExtraData();
      extraData.connect = value;
      user.value = {
        ...user.value,
        extra_data: extraData,
      };
      triggerRef(user);
    }
  },
});

const socialEventFee = computed<number>(() => {
  return selectedSocialEvents.value.reduce((acc, id) => {
    const session = socialEvents.value.find((s) => s.id === id);
    if (session && !includedSocialEvents.value.includes(session.id)) {
      return acc + session.extra_attendees_fee;
    }
    return acc;
  }, 0);
});

const accompanyingPersonsFee = computed<number>(() => {
  return accompaningPersons.value.reduce((acc, person) => {
    const selectedSessionIds = person.selected_social_events || [];

    return (
      acc +
      selectedSessionIds.reduce((personTotal, id) => {
        const session = socialEvents.value.find((socialEvent) => socialEvent.id === id);
        return personTotal + (session?.extra_attendees_fee || 0);
      }, 0)
    );
  }, 0);
});

const totalFee = computed<number>(() => {
  if (!selectedFee.value) return 0;
  const baseFee =
    isEarly.value && selectedFee.value.early_value ? selectedFee.value.early_value : selectedFee.value.value;
  return baseFee + socialEventFee.value + accompanyingPersonsFee.value;
});

const paymentDueAmount = computed<number>(() => {
  if (!registration.value) {
    return paymentReminderDemo.value ? 250 : 0;
  }

  return Math.max(-registration.value.saldo, 0);
});

const showPaymentReminderBox = computed<boolean>(() => {
  if (registration.value && !registration.value.is_paid) {
    return true;
  }

  return paymentReminderDemo.value;
});

const currentFeeType = computed<string>(() => registration.value?.fee_type || '');

const feeOptions = computed<QuasarSelectOption[]>(() => {
  return (
    evanEvent.value?.fees.map((f: Fee) => ({
      value: f.type,
      label: feeLabel(f),
      disable: f.is_sold_out && f.type !== currentFeeType.value,
    })) || []
  );
});

const validFees = computed<string[]>(() => {
  return (
    evanEvent.value?.fees
      .filter((f: Fee) => !f.is_sold_out || f.type === currentFeeType.value)
      .map((f: Fee) => f.type) || []
  );
});

function feeLabel(f: Fee): string {
  const remaining = f.remaining_capacity;
  if (f.is_sold_out) {
    return `${f.notes} — ${t('fee.sold_out')}`;
  }
  if (remaining !== null && remaining <= 5) {
    const key = remaining === 1 ? 'fee.remaining_one' : 'fee.remaining';
    return `${f.notes} — ${t(key, { n: remaining })}`;
  }
  return f.notes;
}

const registrationFormFields = computed<ExtraDataField[]>(() => {
  return evanEvent.value?.registration_configuration?.form_fields || [];
});

function hasFieldValue(value: unknown): boolean {
  if (value === null || value === undefined) {
    return false;
  }

  if (typeof value === 'string') {
    return value.trim().length > 0;
  }

  if (Array.isArray(value)) {
    return value.length > 0;
  }

  return true;
}

const profileIsValid = computed<boolean>(() => {
  if (!user.value) {
    return true;
  }

  return !!(
    user.value.first_name?.trim() &&
    user.value.last_name?.trim() &&
    user.value.affiliation?.trim() &&
    user.value.country
  );
});

async function saveRegistration() {
  if (!mutableRegistration.value || saving.value) {
    return;
  }

  saving.value = true;

  try {
    // TODO: consolidate sessions
    mutableRegistration.value.sessions = selectedSocialEvents.value;

    // Add accompanying persons data to registration
    // only if name is provided
    accompaningPersons.value = accompaningPersons.value.filter((p) => p.name);

    mutableRegistration.value.extra_data = {
      ...mutableRegistration.value.extra_data,
      accompanying_persons: accompaningPersons.value,
    };

    if (user.value) {
      const firstName = normalizeNameIfAllCaps(user.value.first_name || '');
      const lastName = normalizeNameIfAllCaps(user.value.last_name || '');
      const extraData = user.value.extra_data ? { ...user.value.extra_data } : defaultUserExtraData();

      user.value = {
        ...user.value,
        first_name: firstName,
        last_name: lastName,
        extra_data: extraData,
      };

      await userStore.updateUser({
        first_name: firstName,
        last_name: lastName,
        affiliation: user.value.affiliation,
        country: user.value.country,
        extra_data: extraData,
      });
    }

    if (registration.value) {
      await store.updateRegistration(mutableRegistration.value);
    } else {
      await store.createRegistration(mutableRegistration.value);
    }

    window.scrollTo({ top: 0 });
  } finally {
    saving.value = false;
  }
}

const feeExtraDataIsValid = computed<boolean>(() => {
  if (!evanEvent.value?.registration_configuration?.fee_selection) {
    return true;
  }

  const feeConfig = evanEvent.value.registration_configuration.fee_selection;

  if (!feeConfig || !feeConfig.criteria) {
    return true;
  }

  for (const criteria of feeConfig.criteria) {
    if (criteria.extra_data_fields) {
      const criteriaIndex = feeConfig.criteria.findIndex((c) => c.code === criteria.code);
      const selectedValue = mutableRegistration.value?.fee_type?.split('__')[criteriaIndex];

      for (const field of criteria.extra_data_fields) {
        const shouldShow =
          !field.show_for || field.show_for.length === 0 || field.show_for.includes(selectedValue as string);

        if (shouldShow && field.required && !hasFieldValue(mutableRegistration.value?.extra_data?.[field.code])) {
          return false;
        }
      }
    }
  }

  return true;
});

const registrationFormFieldsAreValid = computed<boolean>(() => {
  if (!registrationFormFields.value.length) {
    return true;
  }

  const feeType = mutableRegistration.value?.fee_type;

  for (const field of registrationFormFields.value) {
    const shouldShow =
      !field.show_for || field.show_for.length === 0 || (!!feeType && field.show_for.includes(feeType));

    if (shouldShow && field.required && !hasFieldValue(mutableRegistration.value?.extra_data?.[field.code])) {
      return false;
    }
  }

  return true;
});

const formIsValid = computed<boolean>(() => {
  if (!mutableRegistration.value || !selectedFee.value) {
    return false;
  }

  return profileIsValid.value && feeExtraDataIsValid.value && registrationFormFieldsAreValid.value;
});

watch(
  () => mutableRegistration.value?.fee_type,
  () => {
    if (!mutableRegistration.value || !registrationFormFields.value.length) {
      return;
    }

    const feeType = mutableRegistration.value.fee_type;
    const nextExtraData = { ...mutableRegistration.value.extra_data };
    let changed = false;

    registrationFormFields.value.forEach((field) => {
      const shouldShow =
        !field.show_for || field.show_for.length === 0 || (!!feeType && field.show_for.includes(feeType));
      if (!shouldShow && Object.prototype.hasOwnProperty.call(nextExtraData, field.code)) {
        delete nextExtraData[field.code];
        changed = true;
      }
    });

    if (changed) {
      mutableRegistration.value.extra_data = nextExtraData;
    }
  },
);

watch(
  () => registration.value,
  (val) => {
    if (val) {
      mutableRegistration.value = val;
      selectedSocialEvents.value = val.sessions;
      accompaningPersons.value = val.extra_data.accompanying_persons || [];
    } else {
      mutableRegistration.value = {
        fee_type: '',
        sessions: [],
        extra_data: {
          _internal: {
            share_email_with_sponsors: false,
            allow_photo_sharing: true,
          },
        },
        visa_requested: false,
      };
      selectedSocialEvents.value = [];
      accompaningPersons.value = [];
    }
  },
  { immediate: true },
);
</script>
