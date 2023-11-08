var EvanCommonComponents = {

    'version-hash': {
    data: function () {
      return {
        rev: document.querySelector('html').dataset.rev || 'revhash'
      };
    },
    props: {
      size: {
        type: Number,
        default: 7
      }
    },
    template: '<span>{{ hash }}</span>',
    computed: {
      hash: function () {
        return this.rev.slice(0, this.size);
      }
    }
  },

  'django-form-error': {
    props: {
      field: {
        type: String,
        default: null
      },
      error: {
        type: String,
        required: true
      }
    },
    template: '<em class="hidden"></em>',
    created: function () {
      Quasar.Notify.create({
        timeout: 10000,
        progress: true,
        html: true,
        message: (this.field)
          ? '<strong>' + this.field + '</strong>: ' + this.error
          : this.error,
        type: 'negative',
        actions: [
          { label: 'Dismiss', color: 'white', handler: function () {} }
        ],
        attrs: {
          role: 'alert'
        }
      });
    }
  },

  'django-message': {
    props: {
      message: {
        type: String
      },
      level: {
        type: String
      },
      tags: {
        type: String
      }
    },
    template: '<em class="hidden"></em>',
    created: function () {
      /*
      DEBUG = 10
      INFO = 20
      SUCCESS = 25
      WARNING = 30
      ERROR = 40
      */
      var level = +this.level;
      Quasar.Notify.create({
        timeout: (level > 25) ? 10000 : 5000,
        message: this.message,
        type: {
          10: 'info',
          20: 'info',
          25: 'positive',
          30: 'warning',
          40: 'negative'
        }[level] || 'info',
        actions: [
          {
            label: 'Dismiss',
            color: (level == 30) ? 'dark' : 'white',
            handler: function () {}
          }
        ],
        attrs: {
          role: 'alert'
        }
      });
    }
  },

  'country-flag': {
    props: {
      code: {
        type: String
      }
    },
    template: '<i :class="css"></i>',
    computed: {
      css: function () {
        if (!this.code) return '';
        return [
          "flag-sprite",
          "flag-" + this.code[0],
          "flag-_" + this.code[1],
        ].join(' ').toLowerCase()
      }
    }
  },

  'display-3': {
    template: '<h5 class="q-mt-none q-mb-md text-weight-light"><slot></slot></h5>'
  },

  'display-5': {
    template: '<h6 class="q-mt-sm q-mb-lg text-weight-bold"><slot></slot></h6>'
  },

  'evan-copy-icon': {
    props: {
      text: {
        type: String,
        required: true
      }
    },
    template: '<q-icon name="copy_all" @click.stop="copyToClipboard" class="cursor-pointer" />',
    methods: {
      copyToClipboard: function () {
        Quasar.copyToClipboard(this.text).then(function () {
          evan.utils.notify('Copied to clipboard', 'none');
        }).catch(function () {
          evan.utils.notify('Could not copy to clipboard', 'warning');
        });
      }
    }
  },

  'evan-contact-dialog': {
    data: function () {
      return {
        dialogVisible: false,
        user: null,
        msg: null
      };
    },
    props: {
      eventUrl: {
        type: String,
        required: true
      }
    },
    template: `
      <q-dialog v-model="showDialog" @show="dialogVisible = true">
        <q-card v-if="user" class="q-pa-sm" style="width: 500px">
          <q-toolbar>
            <q-toolbar-title class="q-ml-xs">Contact form</q-toolbar-title>
            <q-space />
            <q-btn v-close-popup flat round icon="close" />
          </q-toolbar>
          <q-card-section class="text-body2">
            <p>For privacy reasons we cannot share other users' emails. Please use this form to send a message to <strong>{{ user.name }}</strong><span v-if="user.affiliation"> ({{ user.affiliation }})</span>: we will share your email address with {{ user.name }} so you can get a direct response.</p>
            <q-input v-model="msg" filled type="textarea" class="q-mb-md"></q-input>
            <q-btn v-close-popup @click="sendMessage" outline color="primary" label="Send message" :disable="!msg" />
          </q-card-section>
          <q-card-section class="text-caption q-pb-lg">
            <span>Please note that {{ user.name }} can choose to discard your message.</span>
          </q-card-section>
        </q-card>
      </q-dialog>
    `,
    computed: {
      showDialog: {
        get: function () {
          return this.user != null;
        },
        set: function (val) {
          if (this.dialogVisible) {
            this.dialogVisible = false;
            this.msg = null;
            this.user = null;
          }
        }
      }
    },
    methods: {
      updateUser: function (user) {
        this.user = user;
      },
      sendMessage: function () {
        evan.api.request('post', this.eventUrl + 'contact/', {
          user_id: this.user.id,
          message: this.msg
        }).then(function (res) {
          evan.utils.notify('Message sent.');
        }).catch(function (error) {
          evan.utils.notifyApiError(error);
        });
      }
    },
    created: function () {
      EventEmitter.on('show-contact-dialog', this.updateUser);
    },
    beforeDestroy: function () {
      EventEmitter.off('show-contact-dialog');
    }
  },

  'evan-search-bar': {
    emits: ['update:modelValue'],
    data: function () {
      return {
        dialogVisible: false,
        filterData: {}
      };
    },
    props: {
      modelValue: {
        type: String,
        default: ''
      },
      placeholder: {
        type: String,
        default: 'Search...'
      },
      filters: {
        type: Array,
        default: function () {
          return [];
        }
      }
    },
    template: `
      <div>
        <q-input filled :dense="$q.screen.gt.sm" v-model="q" :placeholder="placeholder" type="search" class="text-mono q-mb-md">
          <template v-slot:prepend>
            <q-icon name="search" />
          </template>
          <template v-slot:append>
            <q-icon v-show="q !== ''" @click="q = ''" name="close" class="cursor-pointer" />
            <q-icon v-if="filters.length" @click="dialogVisible = true" name="tune" class="cursor-pointer q-ml-sm" />
          </template>
        </q-input>
        <q-dialog v-model="dialogVisible" position="right" @before-show="updateFilters" @before-hide="updateQuery">
          <q-card v-if="filters.length" style="width: 280px; height: 100%" class="q-pa-lg">
            <display-5 class="text-grey-8">Search builder</display-5>
            <div class="q-gutter-md q-mt-md">
              <q-input dense filled v-model="filterData.text" @keyup.enter="dialogVisible = false" type="text" label="Text" />
              <q-separator />
              <q-select v-for="filter in filters" dense filled v-model="filterData[filter.name]" :options="filter.options" :label="filter.name">
                <template v-if="filterData[filter.name]" v-slot:append>
                  <q-icon name="clear" @click.stop="filterData[filter.name] = null" class="cursor-pointer" size="14px" />
                </template>
              </q-select>
            </div>
          </q-card>
        </q-dialog>
      </div>
    `,
    computed: {
      q: {
        get: function () {
          return this.modelValue;
        },
        set: function (val) {
          this.$emit('update:modelValue', val);
        }
      }
    },
    methods: {
      updateQuery: function () {
        var val = this.filterData;
        var q = [val.text];
        _.each(_.keys(val), function (k) {
          if (k != 'text' && val[k]) q.push(k + ':' + val[k]);
        });
        this.$emit('update:modelValue', q.join(' ').trim());
      },
      updateFilters: function () {
        var q = this.q.replace(/\s+/g,' ').trim();

        if (q == '') {
          this.filterData = {};
          return;
        };

        var filterParts = {};
        var textParts = [];

        _.each(q.split(' '), function (word) {
          if (word.indexOf(':') > -1) {
            var s = word.split(':');
            filterParts[s[0]] = s[1];
          } else {
            textParts.push(word);
          }
        });

        filterParts['text'] = textParts.join(' ');

        this.filterData = filterParts;
      }
    }
  },

  'stats-progress': {
    props: {
      size: {
        type: String,
        default: 'lg'
      },
      fontSize: {
        type: String,
        default: '12px'
      },
      value: {
        type: Number,
        required: true
      }
    },
    template: `
      <q-circular-progress show-value :size="size" :font-size="fontSize" :value="value" :color="color" track-color="grey-3">
        <samp><strong><slot></slot></strong></samp>
      </q-circular-progress>
    `,
    computed: {
      color: function () {
        if (this.value == 100) return 'positive';
        if (this.value >= 50) return 'blue';
        if (this.value >= 25) return 'light-blue';
        if (this.value >= 10) return 'cyan';
        return 'blue-grey';
      }
    }
  }

};
