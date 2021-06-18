Vue.component('evan-registrations-table', {
  data: function () {
    return {
      dialogVisible: false,
      columns: [
        {
          name: 'href'
        },
        {
          name: 'uuid',
          field: 'uuid',
          sortable: true,
          label: 'ID',
          align: 'left',
        },
        {
          name: 'user_name',
          field: 'user_name',
          sortable: true,
          align: 'left',
          label: 'Attendee'
        },
        {
          name: 'user_affiliation',
          field: 'user_affiliation',
          sortable: true,
          align: 'left',
          label: 'Affiliation'
        },
        {
          name: 'date',
          field: 'created_at',
          sortable: true,
          align: 'left',
          label: 'Date'
        },
        {
          name: 'visa_status',
          align: 'center',
          label: 'Visa'
        },
        {
          name: 'invoice_status',
          align: 'center',
          label: 'Invoice'
        },
        {
          name: 'payment_status',
          align: 'center',
          label: 'Payment'
        }
      ],
      pagination: {
        rowsPerPage: 25
      }
    }
  },
  props: {
    data: {
      type: Array,
      required: true
    },
    uuid: {
      type: String,
      default: null
    },
    showUser: {
      type: Boolean,
      default: true
    }
  },
  template: `
    <div>
      <q-table flat dense row-key="uuid" :data="data" :columns="columns" :pagination.sync="pagination">
        <template v-slot:body="props">
          <q-tr :props="props" class="cursor-pointer" @click="$router.replace({params: {uuid: props.row.uuid}})" :class="{'bg-orange-1': props.row.uuid == uuid}">
            <q-td key="href" :props="props">
              <q-icon name="add_circle" color="primary"></q-icon>
            </q-td>
            <q-td key="uuid" :props="props"><samp><small>{{ props.row.uuid }}</small></samp></q-td>
            <q-td key="user_name" :props="props">{{ props.row.user_name }}</q-td>
            <q-td key="user_affiliation" :props="props" class="full-width">{{ props.row.user_affiliation }}</q-td>
            <q-td key="date" :props="props">{{ props.row.date }}</q-td>
            <q-td key="visa_status" :props="props">
              <span v-if="props.row.visa_requested">
                <q-badge v-if="props.row.visa_sent" color="positive">
                  <q-icon name="done" class="q-mr-xs"></q-icon>Yes</q-badge>
                <q-badge v-else color="orange-5">
                  <q-icon name="radio_button_unchecked" class="q-mr-xs"></q-icon>Yes</q-badge>
              </span>
              <q-badge v-else outline color="grey">
                <q-icon name="close" class="q-mr-xs"></q-icon>No</q-badge>
            </q-td>
            <q-td key="invoice_status" :props="props">
              <span v-if="props.row.invoice_requested">
                <q-badge v-if="props.row.invoice_sent" color="positive">
                  <q-icon name="done" class="q-mr-xs"></q-icon>Yes</q-badge>
                <q-badge v-else color="orange-5">
                  <q-icon name="radio_button_unchecked" class="q-mr-xs" />Yes</q-badge>
              </span>
              <q-badge v-else outline color="grey">
                <q-icon name="close" class="q-mr-xs"></q-icon>No</q-badge>
            </q-td>
            <q-td key="payment_status" :props="props">
              <q-badge v-if="props.row.is_paid" color="positive"><q-icon name="done" class="q-mr-xs" />Paid</q-badge>
              <q-badge v-else color="orange-5">
                <q-icon name="radio_button_unchecked" class="q-mr-xs" />Pending</q-badge>
            </q-td>
          </q-tr>
        </template>
      </q-table>
      <q-dialog v-model="showDialog" @show="dialogVisible = true">
        <q-card flat v-if="registration" style="width: 500px">
          <q-card-section>
            <display-5 class="evan-ma-none">Registration</display-5>
            <p><samp>{{ registration.uuid }}</samp></p>
            <q-list dense>
              <q-item>
                <q-item-section avatar><q-icon name="schedule"></q-icon></q-item-section>
                <q-item-section>{{ registration.date }}</q-item-section>
              </q-item>
              <q-separator inset="item"></q-separator>
              <q-item>
                <q-item-section avatar><q-icon name="accessibility_new"></q-icon></q-item-section>
                <q-item-section>{{ registration.user_name }}</q-item-section>
              </q-item>
              <q-separator inset="item"></q-separator>
              <q-item>
                <q-item-section avatar><q-icon name="email"></q-icon></q-item-section>
                <q-item-section>{{ registration.user.email }}</q-item-section>
              </q-item>
              <q-separator inset="item"></q-separator>
              <q-item>
                <q-item-section avatar><q-icon name="business"></q-icon></q-item-section>
                <q-item-section>{{ registration.user_affiliation }}</q-item-section>
              </q-item>
              <q-separator v-if="registration.user.profile.country" inset="item" />
              <q-item v-if="registration.user.profile.country">
                <q-item-section avatar>
                  <country-flag :code="registration.user.profile.country.code"></country-flag>
                </q-item-section>
                <q-item-section>{{ registration.user.profile.country.name }}</q-item-section>
              </q-item>
              <q-separator v-if="registration.invoice_requested" inset="item"></q-separator>
              <q-item v-if="registration.invoice_requested">
                <q-item-section avatar><q-icon name="grading" :color="(registration.invoice_sent) ? 'positive' : 'orange-7'"></q-icon></q-item-section>
                <q-item-section v-if="registration.invoice_sent" class="text-positive text-bold">Invoice sent</q-item-section>
                <q-item-section v-else class="text-orange-7 text-bold">Invoice requested (not sent)</q-item-section>
              </q-item>
              <q-separator inset="item"></q-separator>
              <q-item v-if="registration.is_paid">
                <q-item-section avatar><q-icon name="done_outline" color="positive"></q-icon></q-item-section>
                <q-item-section class="text-positive text-bold">Paid</q-item-section>
              </q-item>
              <q-item v-else>
                <q-item-section avatar><q-icon name="radio_button_unchecked" color="orange-7"></q-icon></q-item-section>
                <q-item-section class="text-orange-7 text-bold">Pending payment</q-item-section>
              </q-item>
            </q-list>
          </q-card-section>
          <q-card-actions align="right" class="q-pa-md">
            <q-btn flat label="Close" color="grey" v-close-popup></q-btn>
          </q-card-actions>
        </q-card>
      </q-dialog>
    </div>
  `,
  computed: {
    registration: function () {
      if (this.data.length && this.uuid) {
        return _.findWhere(this.data, {uuid: this.uuid});
      } else return null;
    },
    showDialog: {
      get: function () {
        return this.registration != null;
      },
      set: function (val) {
        if (this.dialogVisible) {
          this.$router.replace({params: {uuid: undefined}});
          this.dialogVisible = false;
        }
      }
    }
  }
});
