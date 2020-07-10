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
    '<div>' +
      '<input v-model="inputVal" type="hidden">' +
      '<div v-for="el in value" class="row">' +
        '<div v-for="field in fields" class="col">' +
          '<q-input v-model="el[field.id]" :label="field.label" filled dense></q-input>' +
        '</div>' +
        '<div class="col-1"><a href @click.prevent="removeFromStack(el)">&times;</a></div>' +
      '</div>' +
      '<a href @click.prevent="addToStack">+ {{ addText }}</a></p>' +
    '</div>' +
  '',
  computed: {
    inputVal: {
      get() {
        return this.value;
      },
      set(val) {
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
