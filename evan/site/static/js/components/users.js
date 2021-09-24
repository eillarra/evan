var EvanUserComponents = {

  'evan-user-selector': {
    emits: ['update:modelValue'],
    data: function () {
      return {
        selection: [],
        options: []
      };
    },
    props: {
      modelValue: {
        type: Array,
        default: function () {
          return [];
        }
      },
      label: {
        type: String,
        default: 'Users'
      },
      hint: {
        type: String,
        default: null
      }
    },
    template: `
      <q-select
        v-model="selection"
        :options="options"
        option-value="id"
        option-label="name"
        :label="label"
        :hint="hint"
        dense
        filled
        multiple
        counter
        input-debounce="200"
        use-chips
        use-input
        fill-input
        @filter="search"
        class="evan__autocomplete"
      >
        <template v-slot:no-option>
          <q-item>
            <q-item-section class="text-grey">
              No results
            </q-item-section>
          </q-item>
        </template>
        <template v-slot:option="scope">
          <q-item v-bind="scope.itemProps">
            <q-item-section>
              <q-item-label>{{ scope.opt.name }}</q-item-label>
              <q-item-label caption>{{ scope.opt.username }} &lt;{{ scope.opt.email }}&gt;</q-item-label>
            </q-item-section>
          </q-item>
        </template>
      </q-select>
    `,
    methods: {
      search: function (q, update, abort) {
        if (q == '' || q.length < 3) {
          this.options = [];
          abort();
          return;
        }

        var self = this;

        axios.get('/api/v1/search/users/?search=' + q).then(function (res) {
          update(function () {
            self.options = res.data.results.map(function (obj) {
              return {
                id: obj.id,
                username: obj.username,
                name: obj.first_name + ' ' + obj.last_name,
                email: obj.email
              };
            });
          });
        });
      }
    },
    watch: {
      'selection': function (arr) {
        this.$emit('update:modelValue', arr.map(function (obj) {
          return {
            id: obj.id,
            name: obj.name
          };
        }));
      }
    },
    created: function () {
      this.selection = this.modelValue;
    }
  }

};
