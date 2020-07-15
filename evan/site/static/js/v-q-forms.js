var FormStore = new Vuex.Store({
  state: {
    options: null,
    metadata: []
  },
  mutations: {
    setOptions: function (state, options) {
      state.options = options;
    },
    fetchMetadata: _.debounce(function (state) {
      if (!state.metadata.length) {
        api().getMetadata().then(function (res) {
          state.metadata = res;
        });
      }
    }, 150)
  },
  getters: {
    requiredFields: function (state) {
      if (!state.options) return null;
      if (_.has(state.options.actions, 'POST')) return _.keys(state.options.actions.POST);
      if (_.has(state.options.actions, 'PUT')) return _.keys(state.options.actions.PUT);
      return null;
    },
    fields: function (state) {
      if (!state.options) return null;
      if (_.has(state.options.actions, 'POST')) return state.options.actions.POST;
      if (_.has(state.options.actions, 'PUT')) return state.options.actions.PUT;
      return null;
    },
    metadataDict: function (state) {
      return _.indexBy(state.metadata, 'id');
    }
  }
});

var FormElement = Vue.extend({
  store: FormStore,
  props: ['field', 'value', 'default'],
  computed: _.extend(
    Vuex.mapGetters(['fields']), {
    f: function () {
      if (!this.fields || !this.field) return null;
      return getDescendantProp(this.fields, this.field);
    }
  }),
  mounted: function () {
    if (!this.value && this.default) this.$refs.el.value = this.default;
  }
});

var SelectElement = FormElement.extend({
  props: {
    optionValue: {
      type: String,
      default: 'value'
    },
    optionLabel: {
      type: String,
      default: 'display_name'
    },
    label: {
      type: String,
      default: 'Label'
    }
  },
  template: '' +
    '<div>' +
      '<q-select dense options-dense filled v-model="mutable" :options="options" :option-value="optionValue" :option-label="optionLabel" :label="label"></q-select>' +
    '</div>' +
  '',
  computed: {
    mutable: {
      get: function () {
        return this.value;
      },
      set: function (val) {
        this.$emit('input', val);
      }
    },
    options: function () {
      return this.f.choices;
    }
  }
});

Vue.component('simple-select', SelectElement.extend({

}));

Vue.component('country-select', SelectElement.extend({
  props: {
    optionValue: {
      type: String,
      default: 'code'
    },
    optionLabel: {
      type: String,
      default: 'name'
    },
    label: {
      type: String,
      default: 'Country'
    }
  },
  computed: {
    options: function () {
      return this.f.choices.map(function (obj) {
        return {
          code: obj.value,
          name: obj.display_name
        };
      });
    }
  }
}));

var MetadataElement = FormElement.extend({
  props: {
    type: {
      type: String
    },
    sorting: {
      type: String,
      default: 'position'
    }
  },
  computed: _.extend(
    Vuex.mapState(['metadata']),
    Vuex.mapGetters(['metadataDict']), {
    options: function () {
      if (!this.metadata) return [];
      var type = this.type;
      var sortingFunc = (this.sorting == 'position')
        ? function (a, b) { return a.position - b.position; }
        : function (a, b) { return textSort(a.value, b.value); };

      return this.metadata.filter(function (obj) {
        return obj.type == type;
      }).sort(sortingFunc);
    }
  }),
  created: function () {
    this.$store.commit('fetchMetadata');
  }
});

Vue.component('metadata-select', MetadataElement.extend({
  props: {
    label: {
      type: String,
      default: 'Country'
    }
  },
  template: '' +
    '<div>' +
      '<q-select dense options-dense filled v-model="mutable" :options="options" option-value="id" option-label="value" :label="label"></q-select>' +
    '</div>' +
  '',
  computed: {
    mutable: {
      get: function () {
        return this.value;
      },
      set: function (val) {
        this.$emit('input', val);
      }
    }
  }
}));
