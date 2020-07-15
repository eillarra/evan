Vue.component('text-list', {
  props: {
    addText: {
      type: String,
      default: 'Add'
    },
    fields: {
      type: Array,
      default: function () {
        return [];
      }
    },
    value: {
      type: Array,
      default: function () {
        return [];
      }
    }
  },
  data: function () {
    return {
      stack: []
    };
  },
  template: '' +
    '<div class="q-mb-lg">' +
      '<input v-model="mutable" type="hidden" />' +
      '<div v-for="el in value" class="row q-col-gutter-xs q-mb-sm items-center">' +
        '<div v-for="field in fields" class="col">' +
          '<q-input v-model="el[field.id]" :label="field.label" filled dense></q-input>' +
        '</div>' +
        '<div class="col-1 text-center">' +
          '<a href @click.prevent="removeFromStack(el)" class="text-pink"><q-icon name="close"></q-icon></a>' +
        '</div>' +
      '</div>' +
      '<q-btn outline @click="addToStack" size="sm" color="green" icon="add" :label="addText"></q-btn>' +
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
  },
  methods: {
    addToStack: function () {
      this.stack.push({
        'id': '',
        'title': '',
      });
      this.$emit('input', this.stack);
    },
    removeFromStack: function (item) {
      this.stack = _.without(this.stack, item);
      this.$emit('input', this.stack);
    }
  },
  mounted: function () {
    this.stack = this.value;
  }
});
