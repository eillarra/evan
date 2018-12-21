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
    data: function () {
        return {
            invalid: false,
            mutableHelpText: null,
        }
    },
    props: ['field', 'value', 'default'],
    computed: _.extend(
        Vuex.mapGetters(['fields']), {
        f: function () {
            if (!this.fields || !this.field) return null;
            return getDescendantProp(this.fields, this.field);
        }
    }),
    methods: {
        transformValue: function (value) {
            if (!value && this.default) return this.default;
            return value;
        },
        updateValue: function (event) {
            value = this.transformValue(event.target.value);
            this.$refs.el.value = value;
            this.$emit('input', value);
        }
    },
    mounted: function () {
        if (!this.value && this.default) this.$refs.el.value = this.default;
    }
});

var SelectElement = FormElement.extend({
    props: {
        forceChoices: {
            type: Array,
            default: function () {
                return [];
            }
        },
        selectProperty: {
            type: String
        },
        sm: {
            type: Boolean,
            default: false
        }
    },
    template: '' +
        '<div ref="el" :value="value">' +
            '<select @change="updateValue" class="form-control" :class="{\'is-invalid\': invalid, \'form-control-sm\': sm}">' +
                '<option v-for="choice in choices" :key="choice.value" :value="choice.value" :selected="choice.value == compareValue">{{ choice.display_name }}</option>' +
            '</select>' +
        '</div>' +
    '',
    computed: {
        choices: function () {
            if (this.forceChoices.length > 0) return this.forceChoices;
            if (!this.f) return [];
            return this.f.choices;
        },
        compareValue: function () {
            if (this.selectProperty) return this.value[this.selectProperty];
            return this.value;
        }
    }
});

Vue.component('simple-select', SelectElement.extend({

}));

Vue.component('country-select', SelectElement.extend({
    props: {
        force: {
            type: Boolean,
            default: false
        }
    },
    methods: {
        transformValue: function (value) {
            var obj = _.findWhere(this.choices, {value: value});
            return {
                code: obj.value,
                name: obj.display_name,
            }
        },
        forceCountry: function (code) {
            value = this.transformValue(code);
            this.mutableHelpText = null;
            this.$refs.el.value = value;
            this.$emit('input', value);
        }
    },
    created: function () {
        EventHub.$on('force-country', this.forceCountry);
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
    methods: {
        transformValue: function (value) {
            return _.pick(_.findWhere(this.metadata, {id: +value}), 'id', 'value');
        }
    },
    created: function () {
        this.$store.commit('fetchMetadata');
    }
});

Vue.component('metadata-select', MetadataElement.extend({
    props: {
        sm: {
            type: Boolean,
            default: false
        }
    },
    template: '' +
        '<div ref="el" :value="value">' +
            '<select @change="updateValue" class="form-control" :class="{\'form-control-sm\': sm}">' +
                '<option v-for="o in options" :key="o.id" :value="o.id" :selected="value && o.id == value.id">{{ o.value }}</option>' +
            '</select>' +
        '</div>' +
    ''
}));
