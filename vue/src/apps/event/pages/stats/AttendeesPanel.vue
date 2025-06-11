<template>
  <div class="row q-col-gutter-md">
    <div class="col-12 col-md-3">
      <stats-card title="Total attendees" :value="totalRegistrations.toString()" :items="[]" />
    </div>
    <div class="col-12 col-md-3">
      <stats-card
        title="Gender balance"
        :value="genderBalance.displayRatio || '-'"
        :value-color="genderBalance.isBalanced ? 'text-positive' : undefined"
        :items="genderStatsItems"
      />
    </div>
    <div class="col-12 col-md-3">
      <stats-card title="Countries" :value="totalCountries.toString()" :items="topCountriesStats" />
    </div>
    <div class="col-12 col-md-3">
      <stats-card
        title="Visa status"
        :value="
          visaPendingCount > 0 ? `${visaPendingCount} pending` : visaRequestedCount > 0 ? `All sent` : `No requests`
        "
        :value-color="visaPendingCount > 0 ? 'text-orange' : visaRequestedCount > 0 ? 'text-positive' : undefined"
        :items="[
          {
            label: 'Requested',
            value: visaRequestedCount.toString(),
          },
          {
            label: 'Sent',
            value: visaSentCount.toString(),
          },
        ]"
      />
    </div>
  </div>
  <div class="row q-col-gutter-md">
    <div class="col-12 col-md-6">
      <h4 class="q-mt-xl q-mb-md">Top countries</h4>
      <q-table
        class="ugent__data-table"
        :rows="topCountries"
        :columns="countryColumns"
        row-key="code"
        flat
        dense
        :pagination="{ rowsPerPage: 0 }"
        hide-bottom
      >
        <template v-slot:body-cell-flag="props">
          <q-td :props="props" auto-width>
            <country-flag :code="props.row.code" />
          </q-td>
        </template>
      </q-table>
    </div>
    <div class="col-12 col-md-6">
      <h4 class="q-mt-xl q-mb-md">Top institutions</h4>
      <q-table
        class="ugent__data-table"
        :rows="topInstitutions"
        :columns="institutionColumns"
        row-key="name"
        flat
        dense
        :pagination="{ rowsPerPage: 0 }"
        hide-bottom
      >
        <template v-slot:body-cell-country="props">
          <q-td :props="props" auto-width>
            <country-flag :code="props.row.primaryCountry" />
          </q-td>
        </template>
      </q-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { storeToRefs } from 'pinia';

import { useStore } from '../../store';
import { useCommonStore } from '@/stores/common';
import { getGenderLabel } from '@/utils/gender';
import StatsCard from '../../components/StatsCard.vue';
import CountryFlag from '@/components/CountryFlag.vue';

const { registrations } = storeToRefs(useStore());
const { countries } = storeToRefs(useCommonStore());

const totalRegistrations = computed(() => registrations.value.length);

const genderStatsItems = computed(() => {
  if (genderBalance.value.totalWithGender === 0) {
    return [{ label: 'No gender data', value: '-' }];
  }

  const items = [];

  if (genderBalance.value.maleCount > 0) {
    items.push({
      label: 'Male',
      value: genderBalance.value.maleCount.toString(),
    });
  }

  if (genderBalance.value.femaleCount > 0) {
    items.push({
      label: 'Female',
      value: genderBalance.value.femaleCount.toString(),
    });
  }

  if (genderBalance.value.nonBinaryCount && genderBalance.value.nonBinaryCount > 0) {
    items.push({
      label: 'Non-binary',
      value: genderBalance.value.nonBinaryCount.toString(),
    });
  }

  return items.slice(0, 3);
});

const countryStats = computed(() => {
  const countMap = new Map<string, number>();

  registrations.value.forEach((registration) => {
    const countryCode = (registration.user as unknown as { country?: string }).country;
    if (countryCode) {
      countMap.set(countryCode, (countMap.get(countryCode) || 0) + 1);
    } else {
      countMap.set('zz', (countMap.get('zz') || 0) + 1);
    }
  });

  return Array.from(countMap.entries())
    .map(([code, count]) => ({
      code,
      name: code === 'zz' ? '(Not set)' : countries.value?.[code] || code,
      count,
      percentage: Math.round((count / totalRegistrations.value) * 100),
    }))
    .sort((a, b) => {
      if (a.count !== b.count) {
        return b.count - a.count;
      }
      if (a.code === 'zz') return 1;
      if (b.code === 'zz') return -1;
      return a.name.localeCompare(b.name);
    });
});

const topCountries = computed(() => countryStats.value.slice(0, 10));

const totalCountries = computed(() => countryStats.value.filter((country) => country.code !== 'zz').length);

const topCountriesStats = computed(() => {
  const top3 = topCountries.value.slice(0, 3);
  return top3.map((country) => ({
    label: country.name,
    value: `${country.percentage} %`,
  }));
});
const institutionStats = computed(() => {
  const instMap = new Map<string, { count: number; countries: Map<string, number> }>();

  registrations.value.forEach((registration) => {
    const affiliation = registration.user.affiliation?.trim();
    const countryCode = (registration.user as unknown as { country?: string }).country || 'zz';

    if (affiliation) {
      if (!instMap.has(affiliation)) {
        instMap.set(affiliation, { count: 0, countries: new Map() });
      }

      const instData = instMap.get(affiliation)!;
      instData.count++;
      instData.countries.set(countryCode, (instData.countries.get(countryCode) || 0) + 1);
    }
  });

  return Array.from(instMap.entries())
    .map(([name, data]) => {
      let primaryCountry = '';
      let maxCount = 0;

      data.countries.forEach((count, country) => {
        if (count > maxCount) {
          maxCount = count;
          primaryCountry = country;
        }
      });

      return {
        name,
        count: data.count,
        percentage: Math.round((data.count / totalRegistrations.value) * 100),
        primaryCountry,
        primaryCountryName: primaryCountry ? countries.value?.[primaryCountry] || primaryCountry : '',
        countryDistribution: data.countries,
      };
    })
    .sort((a, b) => {
      if (a.count !== b.count) {
        return b.count - a.count;
      }
      return a.name.localeCompare(b.name);
    });
});

const topInstitutions = computed(() => institutionStats.value.slice(0, 10));

const visaRequestedCount = computed(() => registrations.value.filter((r) => r.visa_requested).length);
const visaSentCount = computed(() => registrations.value.filter((r) => r.visa_sent).length);
const visaPendingCount = computed(() => registrations.value.filter((r) => r.visa_requested && !r.visa_sent).length);

const genderBreakdown = computed(() => {
  const genderMap = new Map<string, number>();

  registrations.value.forEach((registration) => {
    let gender: string | undefined;

    if (registration.extra_data?.gender) {
      gender = String(registration.extra_data.gender).toLowerCase().trim();
    }

    if (!gender) {
      const userWithExtraData = registration.user as unknown as { extra_data?: { gender?: string } };
      if (userWithExtraData?.extra_data?.gender) {
        gender = String(userWithExtraData.extra_data.gender).toLowerCase().trim();
      }
    }

    if (gender && gender !== 'none' && gender !== '' && gender !== 'null' && gender !== 'undefined') {
      genderMap.set(gender, (genderMap.get(gender) || 0) + 1);
    }
  });

  if (genderMap.size === 0) return [];

  return Array.from(genderMap.entries())
    .map(([gender, count]) => ({
      gender: getGenderLabel(gender),
      rawGender: gender,
      count,
      percentage: Math.round((count / totalRegistrations.value) * 100),
    }))
    .sort((a, b) => {
      if (a.count !== b.count) {
        return b.count - a.count;
      }
      return a.gender.localeCompare(b.gender);
    });
});

const genderBalance = computed(() => {
  if (genderBreakdown.value.length === 0) {
    return {
      totalWithGender: 0,
      maleCount: 0,
      femaleCount: 0,
      nonBinaryCount: 0,
      isBalanced: false,
      displayRatio: '-',
    };
  }

  const totalWithGender = genderBreakdown.value.reduce((sum, item) => sum + item.count, 0);
  const maleCount = genderBreakdown.value.find((item) => item.rawGender === 'male')?.count || 0;
  const femaleCount = genderBreakdown.value.find((item) => item.rawGender === 'female')?.count || 0;
  const nonBinaryCount = genderBreakdown.value
    .filter((item) => !['male', 'female'].includes(item.rawGender))
    .reduce((sum, item) => sum + item.count, 0);

  const femalePercentage = totalWithGender > 0 ? (femaleCount / totalWithGender) * 100 : 0;
  const isBalanced = femalePercentage >= 45 && femalePercentage <= 55;

  let displayRatio = '';
  if (totalWithGender === 0) {
    displayRatio = '-';
  } else if (nonBinaryCount > 0 && (maleCount === 0 || femaleCount === 0)) {
    displayRatio = 'Mixed';
  } else if (femalePercentage === 0) {
    displayRatio = '100% male';
  } else if (femalePercentage === 100) {
    displayRatio = '100% female';
  } else {
    displayRatio = `${Math.round(femalePercentage)}% female`;
  }

  return {
    totalWithGender,
    maleCount,
    femaleCount,
    nonBinaryCount,
    isBalanced,
    displayRatio,
  };
});

const countryColumns = [
  {
    name: 'flag',
    label: '',
    field: 'code',
    align: 'center' as const,
  },
  {
    name: 'name',
    label: 'Country',
    field: 'name',
    align: 'left' as const,
  },
  {
    name: 'count',
    label: 'Count',
    field: 'count',
    align: 'center' as const,
    classes: 'panno-mono-number',
    headerStyle: 'width: 50px',
  },
  {
    name: 'percentage',
    label: '%',
    field: (row: { percentage: number }) => `${row.percentage} %`,
    align: 'right' as const,
    classes: 'panno-mono-number',
    headerStyle: 'width: 50px',
  },
];

const institutionColumns = [
  {
    name: 'country',
    label: '',
    field: 'primaryCountry',
    align: 'center' as const,
  },
  {
    name: 'name',
    label: 'Institution',
    field: 'name',
    align: 'left' as const,
  },
  {
    name: 'count',
    label: 'Count',
    field: 'count',
    align: 'center' as const,
    classes: 'panno-mono-number',
    headerStyle: 'width: 50px',
  },
  {
    name: 'percentage',
    label: '%',
    field: (row: { percentage: number }) => `${row.percentage} %`,
    align: 'right' as const,
    classes: 'panno-mono-number',
    headerStyle: 'width: 50px',
  },
];
</script>
