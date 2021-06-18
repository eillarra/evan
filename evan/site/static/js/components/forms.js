Vue.component('evan-editor', {
  props: {
    autoUpdate: {
      type: Boolean,
      default: false
    },
    saveEventName: {
      type: String,
      default: 'evan-editor-save-obj'
    },
    obj: {
      type: Object,
      default: null
    },
    size: {
      type: String,
      default: 'sm'
    }
  },
  data: function () {
    return {
      dialogVisible: false,
    };
  },
  template: `
    <q-dialog v-model="showDialog" @show="dialogVisible = true">
      <q-layout view="Lhh lpR fff" container class="bg-white" style="max-width: 95vw;" :style="{'width': sizePx}">
        <q-footer bordered class="bg-white text-dark">
          <q-card-actions align="right" class="q-py-md q-px-lg">
            <q-btn flat v-close-popup label="Close" color="grey-8" />
            <q-space />
            <q-btn unelevated v-close-popup @click="save" label="Save" color="primary" class="q-px-md" />
          </q-card-actions>
        </q-footer>
        <q-page-container>
          <q-page>
            <q-card-section v-if="obj" class="q-pa-lg">
              <slot></slot>
            </q-card-section>
          </q-page>
        </q-page-container>
      </q-layout>
    </q-dialog>
  `,
  computed: {
    sizePx: function () {
      return {
        'sm': '400px',
        'md': '650px',
        'lg': '900px'
      }[this.size] || '400px';
    },
    showDialog: {
      get: function () {
        return this.obj != null;
      },
      set: function (val) {
        if (this.dialogVisible) {
          this.dialogVisible = false;
          this.$root.$emit('evan-editor-hide');
        }
      }
    }
  },
  methods: {
    save: function () {
      if (this.autoUpdate && this.obj.url) {
        Evan.api.update(this.obj);
      }
      this.$root.$emit(this.saveEventName, this.obj);
    }
  }
});

Vue.component('evan-text-list', {
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
  template: `
    <div class="q-mb-lg">
      <input v-model="mutable" type="hidden" />
      <div v-for="el in value" class="row q-col-gutter-xs q-mb-sm items-center">
        <div v-for="field in fields" class="col">
          <q-input filled dense v-model="el[field.id]" :label="field.label"></q-input>
        </div>
        <div class="col-1 text-center">
          <a href @click.prevent="removeFromStack(el)" class="text-pink"><q-icon name="close"></q-icon></a>
        </div>
      </div>
      <q-btn outline @click="addToStack" size="sm" color="green" icon="add" :label="addText"></q-btn>
    </div>
  `,
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

Vue.component('evan-datepicker', {
  data: function () {
    return {
      mutable: null
    }
  },
  props: {
    value: {
      type: String,
      required: false
    },
    label: {
      type: String,
      required: true
    },
    hint: {
      type: [String, Boolean],
      default: false
    },
    hintClass: {
      type: [String],
      default: ''
    },
    withTime: {
      type: Boolean,
      default: false
    },
    allowNull: {
      type: Boolean,
      default: false
    }
  },
  template: `
    <div>
      <input v-model="mutable" type="hidden" />
      <q-input filled dense :bottom-slots="hint !== false" v-model="mutable" :label="label">
        <template v-slot:append>
          <q-icon name="event" class="cursor-pointer" size="xs">
            <q-popup-proxy ref="qDateProxy" transition-show="scale" transition-hide="scale">
              <q-date v-model="mutable" :mask="mask">
                <div class="row items-center justify-end">
                  <q-btn v-close-popup label="Close" color="primary" flat />
                </div>
              </q-date>
            </q-popup-proxy>
          </q-icon>
          <q-icon v-if="withTime" name="access_time" class="cursor-pointer" size="xs">
            <q-popup-proxy transition-show="scale" transition-hide="scale">
              <q-time v-model="mutable" :mask="mask" format24h>
                <div class="row items-center justify-end">
                  <q-btn v-close-popup label="Close" color="primary" flat />
                </div>
              </q-time>
            </q-popup-proxy>
          </q-icon>
          <q-icon v-if="allowNull" name="cancel" @click="mutable = null" class="cursor-pointer q-ml-sm" size="xs" />
        </template>
        <template v-if="hint" v-slot:hint>
          <div :class="hintClass">{{ hint }}</div>
        </template>
      </q-input>
    </div>
  `,
  computed: {
    mask: function () {
      return (this.withTime)
        ? 'YYYY-MM-DDTHH:mm'
        : 'YYYY-MM-DD';
    }
  },
  watch: {
    'mutable': function (val) {
      this.$emit('input', val);
    }
  },
  created: function () {
    this.mutable = this.value;
  }
});

Vue.component('evan-markdown', {
  data: function () {
    return {
      split: 50,
      mutable: null
    }
  },
  props: {
    value: {
      type: String
    },
    label: {
      type: String,
      default: 'Text'
    }
  },
  template: `
    <div>
      <q-splitter v-model="split" :horizontal="$q.screen.lt.md" :limits="[40, 80]">
        <template v-slot:before>
          <div class="q-pb-lg" :class="{'q-pr-md': !$q.screen.lt.md, 'q-pb-md': $q.screen.lt.md}">
            <q-input filled dense v-model="mutable" :label="label" type="textarea" autogrow bottom-slots>
              <template v-slot:hint>
                <div>You can use Markdown to format your text; you can find more information about the <a href="https://commonmark.org/help/" target="_blank" rel="noopener">Markdown syntax here</a>.</div>
              </template>
            </q-input>
          </div>
        </template>
        <template v-slot:after>
          <div :class="{'q-pl-md': !$q.screen.lt.md, 'q-pt-md': $q.screen.lt.md}">
            <marked :text="mutable" class="text-body2"></marked>
          </div>
        </template>
      </q-splitter>
    </div>
  `,
  watch: {
    'mutable': function (val) {
      this.$emit('input', val);
    }
  },
  created: function () {
    this.mutable = this.value;
  }
});
