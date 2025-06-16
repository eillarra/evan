<template>
  <div class="row q-col-gutter-md">
    <div class="col-12 col-md-3">
      <stats-card
        title="Total revenue"
        :value="formatCurrency(revenueStats.totalReceived)"
        value-color="text-positive"
        :items="[
          { label: 'Expected', value: formatCurrency(revenueStats.totalExpected) },
          ...(revenueStats.couponDiscounts > 0
            ? [
                {
                  label: 'Coupon discounts',
                  value: formatCurrency(revenueStats.couponDiscounts),
                  color: 'text-orange-8',
                },
              ]
            : []),
          {
            label: 'Outstanding amount',
            value: formatCurrency(revenueStats.outstandingAmount),
            color: revenueStats.outstandingAmount > 0 ? 'text-red-8' : undefined,
          },
        ]"
      />
    </div>
    <div class="col-12 col-md-3">
      <stats-card
        title="Payment overview"
        :value="`${Math.round((paymentStats.fullyPaid / totalRegistrations) * 100)}% paid`"
        :value-color="
          Math.round((paymentStats.fullyPaid / totalRegistrations) * 100) >= 80
            ? 'text-positive'
            : Math.round((paymentStats.fullyPaid / totalRegistrations) * 100) >= 50
              ? 'text-orange-8'
              : 'text-red-8'
        "
        :items="[
          {
            label: 'Fully paid',
            value: paymentStats.fullyPaid.toString(),
          },
          {
            label: 'Partially paid',
            value: paymentStats.partiallyPaid.toString(),
            color: paymentStats.partiallyPaid > 0 ? 'text-orange-8' : undefined,
          },
          {
            label: 'Not paid',
            value: paymentStats.unpaid.toString(),
            color: paymentStats.unpaid > 0 ? 'text-red-8' : undefined,
          },
        ]"
      />
    </div>
    <div class="col-12 col-md-3">
      <stats-card
        title="Early bird registrations"
        :value="`${earlyBirdStats.earlyRate}% early`"
        :items="[
          { label: 'Total registrations', value: totalRegistrations.toString() },
          { label: 'Early count', value: earlyBirdStats.earlyCount.toString() },
          ...(earlyBirdStats.savings > 0
            ? [
                {
                  label: 'Early bird discounts',
                  value: formatCurrency(earlyBirdStats.savings),
                },
              ]
            : []),
        ]"
      />
    </div>
    <div class="col-12 col-md-3">
      <stats-card
        title="Registration trends"
        :value="`${registrationTrends.todayRegistrations} today`"
        :items="[
          { label: 'This week', value: registrationTrends.thisWeekRegistrations.toString() },
          { label: 'Peak day', value: registrationTrends.peakDayCount.toString() },
          { label: 'Avg. per day', value: formatDecimal(registrationTrends.avgPerDay) },
        ]"
      />
    </div>
    <div class="col-12 col-md-3">
      <stats-card
        title="Invoice status"
        :value="
          invoiceStats.totalRequested === 0
            ? 'None requested'
            : invoiceStats.pendingInvoices > 0
              ? `${invoiceStats.pendingInvoices} pending`
              : 'All sent'
        "
        :value-color="
          invoiceStats.totalRequested === 0
            ? 'text-grey-6'
            : invoiceStats.pendingInvoices > 0
              ? 'text-orange-8'
              : 'text-positive'
        "
        :items="[
          {
            label: 'Requested',
            value: invoiceStats.totalRequested.toString(),
          },
          { label: 'Sent', value: invoiceStats.sentInvoices.toString() },
          {
            label: invoiceStats.pendingInvoices > 0 ? 'Processing invoices' : 'Pending consolidation',
            value: formatCurrency(invoiceStats.outstandingInvoiceAmount),
            color: invoiceStats.outstandingInvoiceAmount > 0 ? 'text-orange-8' : undefined,
          },
          ...(invoiceStats.needsConsolidationCount > 0
            ? [
                {
                  label: 'Need SAP check',
                  value: invoiceStats.needsConsolidationCount.toString(),
                  color: 'text-orange-8',
                },
              ]
            : []),
        ]"
      />
    </div>
    <div class="col-12 col-md-3">
      <stats-card
        title="Coupon status"
        :value="`${couponStats.totalUsed} used`"
        :items="[
          {
            label: 'Regs using coupon',
            value: `${formatDecimal(couponStats.usageRate)} %`,
          },
          {
            label: 'Impact on revenue',
            value: `${formatDecimal(couponStats.revenueImpact)} %`,
            color: 'text-orange-8',
          },
          ...(couponStats.totalUsed > 0
            ? [
                {
                  label: 'Avg. discount',
                  value: formatCurrency(Math.round(revenueStats.couponDiscounts / couponStats.totalUsed)),
                },
              ]
            : []),
        ]"
      />
    </div>
    <div class="col-12 col-md-3">
      <stats-card
        title="Revenue analytics"
        :value="`${formatCurrency(Math.round(revenueAnalytics.avgRevenuePerRegistration))} per reg`"
        :items="[
          {
            label: 'Avg. transaction',
            value: formatCurrency(Math.round(revenueAnalytics.avgTransactionValue)),
          },
        ]"
      />
    </div>
  </div>
  <h4 class="q-mt-xl q-mb-md">Registration fee types</h4>
  <div class="row q-col-gutter-md">
    <div class="col-12">
      <q-table
        class="ugent__data-table q-mb-xl"
        :rows="feeTypeStats"
        :columns="feeTypeColumns"
        row-key="feeType"
        flat
        dense
        :pagination="{ rowsPerPage: 0, sortBy: 'total', descending: true }"
        hide-bottom
      >
        <template v-slot:body-cell-paymentRate="props">
          <q-td :props="props">
            <div class="row items-center no-wrap">
              <div class="col-8">
                <q-linear-progress
                  :value="props.row.paymentRate / 100"
                  size="4px"
                  :color="props.row.paymentRate >= 80 ? 'positive' : props.row.paymentRate >= 50 ? 'orange-8' : 'red-8'"
                />
              </div>
              <div class="col text-right text-caption panno-mono-number">{{ props.row.paymentRate }} %</div>
            </div>
          </q-td>
        </template>
        <template v-slot:body-cell-couponUsageRate="props">
          <q-td :props="props">
            <div class="row items-center no-wrap">
              <div class="col-8">
                <q-linear-progress :value="props.row.couponUsageRate / 100" size="4px" color="grey-7" />
              </div>
              <div class="col text-right text-caption panno-mono-number">{{ props.row.couponUsageRate }} %</div>
            </div>
          </q-td>
        </template>
      </q-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue';
import { storeToRefs } from 'pinia';

import { formatCurrency, formatDecimal } from '@/utils/numbers';
import { useStore } from '../../store';

import StatsCard from '../../components/StatsCard.vue';

const { evanEvent, registrations } = storeToRefs(useStore());

const calculateCouponDiscount = (registration: Registration) => {
  if (!registration.coupon) return 0;

  const { coupon } = registration;
  if (coupon.coverage === 'base_fee') {
    return Math.min(coupon.value, registration.base_fee || 0);
  } else {
    return Math.min(coupon.value, registration.total_fee || 0);
  }
};

const totalRegistrations = computed(() => registrations.value.length);

// Payment status statistics
const paymentStats = computed(() => {
  let fullyPaid = 0;
  let partiallyPaid = 0;
  let unpaid = 0;
  let invoiceRequested = 0;

  registrations.value.forEach((reg) => {
    if (reg.invoice_requested) {
      invoiceRequested++;
    }

    const saldo = reg.saldo || 0;
    const totalPaid = (reg.paid || 0) + (reg.paid_via_invoice || 0);
    const hasCoupon = !!reg.coupon;

    if (saldo >= 0) {
      fullyPaid++;
    } else if (totalPaid > 0 || hasCoupon) {
      partiallyPaid++;
    } else {
      unpaid++;
    }
  });

  return {
    fullyPaid,
    partiallyPaid,
    unpaid,
    invoiceRequested,
  };
});

const revenueStats = computed(() => {
  let totalReceived = 0;
  let totalExpected = 0;
  let onlinePayments = 0;
  let invoicePayments = 0;
  let couponDiscounts = 0;
  let outstandingAmount = 0;

  registrations.value.forEach((reg) => {
    const totalFee = reg.total_fee || 0;
    const paidAmount = reg.paid || 0;
    const invoicePaid = reg.paid_via_invoice || 0;
    const saldo = reg.saldo || 0;

    const actualCouponDiscount = calculateCouponDiscount(reg);

    totalExpected += totalFee;
    totalReceived += paidAmount + invoicePaid;
    onlinePayments += paidAmount;
    invoicePayments += invoicePaid;
    couponDiscounts += actualCouponDiscount;

    if (saldo < 0) {
      outstandingAmount += Math.abs(saldo);
    }
  });

  return {
    totalReceived,
    totalExpected,
    outstandingAmount,
    onlinePayments,
    invoicePayments,
    couponDiscounts,
  };
});

const couponStats = computed(() => {
  const totalUsed = registrations.value.filter((reg) => reg.coupon).length;

  const revenueImpact =
    revenueStats.value.totalExpected > 0
      ? (revenueStats.value.couponDiscounts / revenueStats.value.totalExpected) * 100
      : 0;

  const usageRate = totalRegistrations.value > 0 ? (totalUsed / totalRegistrations.value) * 100 : 0;

  return {
    totalUsed,
    usageRate,
    revenueImpact,
  };
});

const earlyBirdStats = computed(() => {
  const earlyCount = registrations.value.filter((reg) => reg.is_early).length;
  const earlyRate =
    totalRegistrations.value > 0 ? Math.round((earlyCount / totalRegistrations.value) * 100).toString() : '0';

  let totalSavings = 0;
  if (evanEvent.value) {
    registrations.value.forEach((reg) => {
      if (reg.is_early && reg.fee_type) {
        const fee = evanEvent.value?.fees.find((f) => f.type === reg.fee_type);
        if (fee && fee.early_value && fee.value > fee.early_value) {
          totalSavings += fee.value - fee.early_value;
        }
      }
    });
  }

  return {
    earlyCount,
    earlyRate,
    savings: totalSavings,
  };
});

const registrationTrends = computed(() => {
  const now = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const oneWeekAgo = new Date(today.getTime() - 7 * 24 * 60 * 60 * 1000);

  const dailyCount: Record<string, number> = {};
  let todayCount = 0;
  let thisWeekCount = 0;

  registrations.value.forEach((reg) => {
    const regDate = new Date(reg.created_at);
    const regDateKey = regDate.toISOString().split('T')[0];

    if (regDate >= today) {
      todayCount++;
    }

    if (regDate >= oneWeekAgo) {
      thisWeekCount++;
    }

    dailyCount[regDateKey] = (dailyCount[regDateKey] || 0) + 1;
  });

  const peakDayCount = Math.max(...Object.values(dailyCount), 0);

  let avgPerDay = 0;
  if (evanEvent.value?.registration_start_date && registrations.value.length > 0) {
    const registrationStartDate = new Date(evanEvent.value.registration_start_date);
    const registrationDeadline = evanEvent.value.registration_deadline
      ? new Date(evanEvent.value.registration_deadline)
      : now;

    const calculationEndDate =
      evanEvent.value.registration_deadline && registrationDeadline < now ? registrationDeadline : now;

    const daysSinceStart = Math.max(
      Math.floor((calculationEndDate.getTime() - registrationStartDate.getTime()) / (1000 * 60 * 60 * 24)),
      1,
    );
    avgPerDay = registrations.value.length / daysSinceStart;
  }

  return {
    todayRegistrations: todayCount,
    thisWeekRegistrations: thisWeekCount,
    peakDayCount,
    avgPerDay,
  };
});

const invoiceStats = computed(() => {
  let sentInvoices = 0;
  let paidInvoices = 0;
  let pendingInvoices = 0;
  let totalRequested = 0;
  let totalInvoiceRevenue = 0;
  let outstandingInvoiceAmount = 0;
  let needsConsolidationCount = 0;

  registrations.value.forEach((reg) => {
    if (reg.invoice_requested) {
      totalRequested++;
      const totalFee = reg.total_fee || 0;
      const couponDiscount = reg.coupon?.value ? Math.min(reg.coupon.value, totalFee) : 0;
      const invoiceAmount = totalFee - couponDiscount;

      if (reg.invoice_sent) {
        sentInvoices++;
        totalInvoiceRevenue += invoiceAmount;

        if (reg.paid_via_invoice && reg.paid_via_invoice > 0) {
          paidInvoices++;
          if (Math.abs((reg.paid_via_invoice || 0) - invoiceAmount) > 0.01) {
            needsConsolidationCount++;
          }
        } else {
          outstandingInvoiceAmount += invoiceAmount;
        }
      } else {
        pendingInvoices++;
        outstandingInvoiceAmount += invoiceAmount;
      }
    }
  });

  return {
    sentInvoices,
    paidInvoices,
    pendingInvoices,
    totalRequested,
    totalInvoiceRevenue,
    outstandingInvoiceAmount,
    needsConsolidationCount,
  };
});

const feeTypeStats = computed(() => {
  const feeTypeMap = new Map();
  const hasEarlyRegistrations = registrations.value.some((reg) => reg.is_early);

  registrations.value.forEach((reg) => {
    const baseFeeType = reg.fee_type || 'Unknown';

    let feeTypeKey;
    if (hasEarlyRegistrations) {
      feeTypeKey = reg.is_early ? `${baseFeeType} (early)` : baseFeeType;
    } else {
      feeTypeKey = baseFeeType;
    }

    const actualCouponDiscount = calculateCouponDiscount(reg);

    if (!feeTypeMap.has(feeTypeKey)) {
      feeTypeMap.set(feeTypeKey, {
        feeType: feeTypeKey,
        total: 0,
        paid: 0,
        revenue: 0,
        expectedRevenue: 0,
        couponsUsed: 0,
        couponDiscounts: 0,
      });
    }

    const stats = feeTypeMap.get(feeTypeKey);
    stats.total++;
    stats.expectedRevenue += reg.total_fee || 0;

    if (reg.coupon) {
      stats.couponsUsed++;
      stats.couponDiscounts += actualCouponDiscount;
    }

    if (reg.is_paid) {
      stats.paid++;
      stats.revenue += (reg.paid || 0) + (reg.paid_via_invoice || 0);
    }
  });

  return Array.from(feeTypeMap.values())
    .map((stats) => ({
      ...stats,
      paymentRate: stats.total > 0 ? Math.round((stats.paid / stats.total) * 100) : 0,
      couponUsageRate: stats.total > 0 ? Math.round((stats.couponsUsed / stats.total) * 100) : 0,
    }))
    .sort((a, b) => {
      const aIsEarly = a.feeType.includes('(early)');
      const bIsEarly = b.feeType.includes('(early)');
      const aBaseName = a.feeType.replace(' (early)', '');
      const bBaseName = b.feeType.replace(' (early)', '');

      if (aBaseName === bBaseName) {
        return aIsEarly && !bIsEarly ? -1 : !aIsEarly && bIsEarly ? 1 : 0;
      }

      return b.total - a.total;
    });
});

const revenueAnalytics = computed(() => {
  const totalPaidRegistrations = paymentStats.value.fullyPaid + paymentStats.value.partiallyPaid;
  const totalRevenue = revenueStats.value.totalReceived;

  const avgRevenuePerRegistration = totalRegistrations.value > 0 ? totalRevenue / totalRegistrations.value : 0;
  const avgTransactionValue = totalPaidRegistrations > 0 ? totalRevenue / totalPaidRegistrations : 0;

  const feeTypesByRevenue = [...feeTypeStats.value].sort((a, b) => b.revenue - a.revenue);
  const topFeeType = feeTypesByRevenue.length > 0 ? feeTypesByRevenue[0].feeType : 'N/A';
  const topFeeTypeRevenue = feeTypesByRevenue.length > 0 ? feeTypesByRevenue[0].revenue : 0;
  const topFeeTypePercentage = totalRevenue > 0 ? (topFeeTypeRevenue / totalRevenue) * 100 : 0;

  return {
    avgRevenuePerRegistration,
    avgTransactionValue,
    topFeeType,
    topFeeTypePercentage,
  };
});

const feeTypeColumns = [
  {
    name: 'feeType',
    label: 'Fee type',
    field: 'feeType',
    align: 'left' as const,
    sortable: true,
  },
  {
    name: 'total',
    label: 'Total',
    field: 'total',
    align: 'center' as const,
    sortable: true,
    classes: 'panno-mono-number',
  },
  {
    name: 'paid',
    label: 'Paid',
    field: 'paid',
    align: 'center' as const,
    classes: 'panno-mono-number',
  },
  {
    name: 'paymentRate',
    label: 'Payment rate',
    field: 'paymentRate',
    align: 'center' as const,
  },
  {
    name: 'couponsUsed',
    label: 'Coupons',
    field: 'couponsUsed',
    align: 'center' as const,
    classes: 'panno-mono-number',
  },
  {
    name: 'couponUsageRate',
    label: 'Coupon usage',
    field: 'couponUsageRate',
    align: 'center' as const,
  },
  {
    name: 'revenue',
    label: 'Revenue',
    field: (row: { revenue: number }) => formatCurrency(row.revenue),
    align: 'right' as const,
    classes: 'panno-mono-number',
  },
  {
    name: 'expectedRevenue',
    label: 'Expected',
    field: (row: { expectedRevenue: number }) => formatCurrency(row.expectedRevenue),
    align: 'right' as const,
    classes: 'panno-mono-number',
  },
  {
    name: 'couponDiscounts',
    label: 'Discounts',
    field: (row: { couponDiscounts: number }) => formatCurrency(row.couponDiscounts),
    align: 'right' as const,
    classes: 'panno-mono-number',
  },
];
</script>
