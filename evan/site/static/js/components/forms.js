var EvanFormComponents = {

  'evan-editor': {
    data: function () {
      return {
        dialogVisible: false,
      };
    },
    props: {
      saveEventName: {
        type: String,
        default: null
      },
      obj: {
        type: Object,
        default: null
      },
      objKey: {
        type: String,
        default: 'id'
      },
      position: {
        type: String,
        default: 'top'
      },
      size: {
        type: String,
        default: 'sm'
      }
    },
    template: `
      <q-dialog :position="position" v-model="showDialog" @show="dialogVisible = true">
        <q-card v-if="obj" style="max-width: 95vw;" :style="{'width': sizePx}">
          <q-card-section class="scroll q-px-lg q-py-xl" style="min-height: 250px; max-height: 75vh;">
            <slot></slot>
          </q-card-section>
          <q-separator />
          <q-card-actions align="right" class="q-py-md q-px-lg">
            <q-btn flat v-close-popup label="Close" color="grey-8" />
            <q-space />
            <q-btn v-if="saveEventName" unelevated v-close-popup @click="save" :label="(objKey in obj) ? 'Update' : 'Create'" color="primary" class="q-px-md" />
          </q-card-actions>
        </q-card>
      </q-dialog>
    `,
    computed: {
      sizePx: function () {
        return {
          'sm': '400px',
          'md': '550px',
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
            EventEmitter.emit('evan-editor-hide');
          }
        }
      }
    },
    methods: {
      save: function () {
        EventEmitter.emit(this.saveEventName, this.obj);
      }
    }
  },

  'evan-text-list': {
    emits: ['update:modelValue'],
    data: function () {
      return {
        stack: []
      };
    },
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
      modelValue: {
        type: Array,
        default: function () {
          return [];
        }
      }
    },
    template: `
      <div class="q-mb-lg">
        <input v-model="mutable" type="hidden" />
        <div v-for="el in stack" class="row q-col-gutter-xs q-mb-sm items-center">
          <div v-for="field in fields" class="col">
            <q-input filled dense v-model="el[field.id]" :label="field.label"></q-input>
          </div>
          <div class="col-1 text-center">
            <evan-remove-icon @click.prevent="removeFromStack(el)" />
          </div>
        </div>
        <q-btn outline @click="addToStack" size="sm" color="green" icon="add" :label="addText"></q-btn>
      </div>
    `,
    computed: {
      mutable: {
        get: function () {
          return this.modelValue;
        },
        set: function (val) {
          this.$emit('update:modelValue', val);
        }
      }
    },
    methods: {
      addToStack: function () {
        this.stack.push({
          'id': '',
          'title': '',
        });
        this.$emit('update:modelValue', this.stack);
      },
      removeFromStack: function (item) {
        this.stack = _.without(this.stack, item);
        this.$emit('update:modelValue', this.stack);
      }
    },
    created: function () {
      this.stack = this.modelValue;
    }
  },

  'evan-datepicker': {
    emits: ['update:modelValue'],
    data: function () {
      return {
        mutable: null
      };
    },
    props: {
      modelValue: {
        type: String
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
            <q-icon v-if="withTime" name="access_time" class="cursor-pointer q-ml-sm" size="xs">
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
        this.$emit('update:modelValue', val);
      }
    },
    created: function () {
      this.mutable = this.modelValue;
    }
  },

  'evan-markdown': {
    emits: ['update:modelValue'],
    data: function () {
      return {
        split: 50,
        mutable: null
      };
    },
    props: {
      modelValue: {
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
        this.$emit('update:modelValue', val);
      }
    },
    created: function () {
      this.mutable = this.modelValue;
    }
  },

  'evan-country-select': {
    emits: ['update:modelValue'],
    data: function () {
      return {
        storageKey: 'evan_countries',
        countries: null,
        mutable: null
      };
    },
    props: {
      modelValue: {
        type: Object
      }
    },
    template: `
      <q-select dense filled v-model="mutable" :options="options" label="Country" option-value="code"
        option-label="name" />
    `,
    computed: {
      options: function () {
        var c = [];
        if (!this.countries) return c;

        _.each(this.countries, function (val, key) {
          c.push({
            code: key,
            name: val
          });
        });

        return c;
      }
    },
    methods: {
      getCountries: function () {
        var self = this;

        Evan.api.request('get', '/api/countries/').then(function (res) {
          self.countries = res.data;
          Quasar.SessionStorage.set(self.storageKey, res.data);
        });
      }
    },
    watch: {
      'mutable': function (val) {
        this.$emit('update:modelValue', val);
      }
    },
    created: function () {
      this.mutable = this.modelValue;
      this.countries = Quasar.SessionStorage.getItem(this.storageKey);

      if (!this.countries) this.getCountries();
    }
  }

};
