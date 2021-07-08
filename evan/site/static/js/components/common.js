var CommonMarkReader = new commonmark.Parser({safe: true, smart: true});
var CommonMarkWriter = new commonmark.HtmlRenderer();


var EvanCommonComponents = {

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
      Quasar.Notify.create({
        message: this.message,
        type: {
          10: 'info',
          20: 'info',
          25: 'positive',
          30: 'warning',
          40: 'negative'
        }[+this.level] || 'info',
        actions: [
          {
            label: 'Dismiss',
            color: (+this.level == 30) ? 'dark' : 'white',
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
    template: '<h5 class="q-mt-none q-mb-lg text-weight-bold"><slot></slot></h5>'
  },

  'display-5': {
    template: '<h6 class="q-mt-sm q-mb-lg text-weight-bold"><slot></slot></h6>'
  },

  'marked': {
    props: {
      text: {
        type: String,
        default: ''
      }
    },
    template: '<div class="marked" v-html="compiledText"></div>',
    computed: {
      compiledText: function () {
        if (!this.text || this.text == '') return this.text;
        return CommonMarkWriter.render(CommonMarkReader.parse(this.text));
      }
    }
  },

  'evan-user-menu': {
    data: function () {
      return {
        userId: +(document.querySelector('html').dataset.user)
      };
    },
    props: {
      username: {
        type: String
      }
    },
    template: `
      <q-btn v-if="userId > 0" no-caps flat icon-right="account_circle" color="grey-8" :label="username">
        <q-menu>
          <q-list style="min-width: 140px">
            <q-item clickable tag="a" href="/u/dashboard/">
              <q-item-section>Dashboard</q-item-section>
            </q-item>
            <q-separator />
            <q-item clickable tag="a" href="/u/logout/">
              <q-item-section>Log out</q-item-section>
              <q-item-section side><q-icon name="logout" size="xs" /></q-item-section>
            </q-item>
          </q-list>
        </q-menu>
      </q-btn>
    `
  },

  'evan-no-data': {
    props: {
      message: {
        type: String,
        required: true
      },
      filter: {
        type: String,
        default: ''
      }
    },
    template: `
      <div class="full-width text-center q-pa-xl text-grey-6">
        <q-icon size="6em" :name="filter ? 'search_off' : 'layers_clear'" />
        <h5>{{ message }}</h5>
      </div>
    `
  },

  'evan-edit-icon': {
    template: `
      <q-icon name="drive_file_rename_outline" color="primary" class="cursor-pointer" />
    `
  },

  'evan-remove-icon': {
    props: {
      size: {
        type: String,
        default: null
      }
    },
    template: `
      <q-icon name="backspace" color="red-12" class="cursor-pointer" :size="size" />
    `
  },

  'evan-yes-chip': {
    props: {
      color: {
        type: String,
        default: 'positive'
      },
      icon: {
        type: String,
        default: 'check'
      }
    },
    template: '<q-chip :color="color" text-color="white" size="xs" :icon="icon" class="evan-chip">Yes</q-chip>'
  },

  'evan-no-chip': {
    props: {
      color: {
        type: String,
        default: 'grey-6'
      },
      icon: {
        type: String,
        default: 'close'
      }
    },
    template: '<q-chip outline :color="color" size="xs" :icon="icon" class="evan-chip">No</q-chip>'
  },

  'evan-logo': {
    props: {
      fill: {
        type: String,
        default: '#1e64c8'
      },
      width: {
        type: Number,
        default: 120
      }
    },
    template: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 88.72 24.03" :width="width"><defs/><g :fill="fill" aria-label="evan" font-family="Pacifico" font-size="192" font-weight="400" letter-spacing="0" style="line-height:1.25" word-spacing="0"><path d="M23.42 12.45q.66 0 1.01.6.41.62.41 1.68 0 2.03-.96 3.15-1.88 2.29-5.34 4.22-3.4 1.93-7.31 1.93-5.34 0-8.28-2.9Q0 18.23 0 13.21q0-3.5 1.47-6.5 1.48-3.05 4.07-4.83Q8.18.1 11.48.1q2.95 0 4.72 1.78 1.78 1.73 1.78 4.72 0 3.5-2.54 6.05-2.49 2.49-8.48 3.96 1.27 2.34 4.83 2.34 2.28 0 5.18-1.58 2.94-1.62 5.08-4.21.6-.71 1.37-.71zm-12.8-7.37q-1.88 0-3.2 2.18-1.27 2.19-1.27 5.29v.1q3-.71 4.72-2.13 1.73-1.43 1.73-3.3 0-.97-.56-1.53-.5-.61-1.42-.61z" style="-inkscape-font-specification:Pacifico"/><path d="M46.15 8.33q.15-.05.5-.05.77 0 1.18.5.4.52.4 1.38 0 1.57-.6 2.49-.62.86-1.84 1.27-2.33.76-4.97.76-2.24 0-4.22-.6-1.48 2.38-3.25 4.92-2.04 2.9-3.5 3.96-1.48 1.07-3.36 1.07-2.08 0-3.3-1.63-1.17-1.62-1.48-5.13-.6-7.1-.6-12.44V3.05q.05-1.68.9-2.34.87-.66 2.6-.66 1.32 0 1.93.61.66.56.66 1.93 0 5.84.71 15.19 3.05-4.52 4.57-7.21-.76-1.48-.76-3.5 0-1.74.76-3.36.77-1.63 2.09-2.64 1.32-1.02 3-1.02 1.47 0 2.38 1.07.91 1.01.91 3 0 2.28-1.21 5.23 1.93-.1 5.13-.77z" style="-inkscape-font-specification:Pacifico"/><path d="M50.07 24.03q-3.15 0-5.03-2.29-1.88-2.28-1.88-6 0-4.06 1.88-7.66 1.88-3.66 4.98-5.85Q53.17 0 56.67 0q1.12 0 1.48.46.4.4.66 1.52 1.07-.2 2.23-.2 2.5 0 2.5 1.78 0 1.06-.77 5.08-1.17 5.84-1.17 8.12 0 .77.36 1.22.4.46 1.01.46.97 0 2.34-1.22 1.37-1.27 3.71-4.06.61-.71 1.37-.71.66 0 1.02.6.4.62.4 1.68 0 2.03-.96 3.15-2.08 2.6-4.42 4.37-2.34 1.78-4.52 1.78-1.68 0-3.1-1.12-1.37-1.17-2.08-3.15-2.65 4.27-6.66 4.27zm1.83-5.13q1.12 0 2.13-1.32t1.48-3.5l1.88-9.36q-2.14.05-3.97 1.63-1.77 1.52-2.84 4.06-1.07 2.54-1.07 5.39 0 1.57.61 2.34.66.76 1.78.76z" style="-inkscape-font-specification:Pacifico"/><path d="M71.34 24.03q-1.93 0-2.74-2.03-.76-2.04-.76-6.5 0-6.61 1.88-12.55.45-1.48 1.47-2.14 1.07-.7 2.94-.7 1.02 0 1.43.25.4.25.4.96 0 .81-.76 3.66-.5 2.03-.81 3.55-.3 1.53-.5 3.76 1.67-4.37 3.75-7.1 2.08-2.75 4.07-3.92Q83.74.1 85.4.1q1.63 0 2.44.87.87.8.87 2.43 0 1.32-.56 4.98-.51 3.1-.82 5.9-.3 2.74-.3 6.14 0 1.93-.81 2.8-.77.8-2.54.8-1.68 0-2.44-.86-.77-.86-.77-2.59 0-2.03.72-6.7.6-4.07.6-5.18 0-.82-.55-.82-.66 0-1.88 1.73-1.17 1.68-2.44 4.47-1.22 2.8-1.98 5.9-.56 2.38-1.32 3.25-.71.8-2.29.8z" style="-inkscape-font-specification:Pacifico"/></g></svg>
    `
  },

  'github-logo': {
    template: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 180.442 175.988"><defs><clipPath id="a"><path d="M0 140.868h595v560.264H0z"/></clipPath></defs><g fill="#1b1817" clip-path="url(#a)" transform="matrix(1.33333 0 0 -1.33333 -433.6 925.213)"><path fill-rule="evenodd" d="M392.867 693.91c-37.366 0-67.666-30.294-67.666-67.666 0-29.897 19.388-55.261 46.274-64.209 3.382-.626 4.623 1.468 4.623 3.255 0 1.614-.063 6.944-.092 12.598-18.824-4.093-22.797 7.984-22.797 7.984-3.078 7.821-7.513 9.901-7.513 9.901-6.14 4.2.463 4.114.463 4.114 6.795-.478 10.373-6.973 10.373-6.973 6.035-10.345 15.83-7.354 19.69-5.625.608 4.373 2.362 7.358 4.297 9.048-15.03 1.71-30.83 7.513-30.83 33.44 0 7.388 2.644 13.425 6.973 18.163-.703 1.705-3.02 8.587.655 17.908 0 0 5.682 1.818 18.613-6.936 5.398 1.499 11.186 2.25 16.937 2.276 5.75-.025 11.544-.777 16.951-2.276 12.916 8.754 18.59 6.936 18.59 6.936 3.683-9.321 1.366-16.203.663-17.908 4.339-4.738 6.964-10.775 6.964-18.162 0-25.99-15.83-31.712-30.897-33.387 2.427-2.1 4.59-6.218 4.59-12.531 0-9.054-.079-16.341-.079-18.57 0-1.8 1.218-3.91 4.648-3.246 26.871 8.958 46.235 34.313 46.235 64.2 0 37.371-30.295 67.666-67.665 67.666"/><path d="M350.83 596.756c-.15-.336-.679-.437-1.16-.206-.491.22-.767.679-.608 1.016.146.346.676.443 1.165.21.492-.22.773-.683.602-1.02M353.57 593.699c-.323-.3-.953-.16-1.381.313-.443.471-.526 1.102-.199 1.406.333.3.945.159 1.389-.313.442-.477.528-1.103.191-1.406M356.238 589.802c-.415-.288-1.093-.018-1.512.584-.414.601-.414 1.323.01 1.612.42.29 1.088.03 1.512-.568.414-.612.414-1.333-.01-1.628M359.893 586.037c-.37-.41-1.16-.3-1.739.259-.592.545-.756 1.32-.384 1.729.375.41 1.17.294 1.752-.26.587-.544.767-1.324.371-1.728M364.936 583.85c-.164-.53-.925-.77-1.691-.545-.766.232-1.266.853-1.112 1.388.16.534.924.785 1.696.544.764-.231 1.266-.847 1.107-1.386M370.473 583.445c.02-.558-.63-1.02-1.435-1.03-.81-.019-1.464.433-1.473.982 0 .564.636 1.022 1.445 1.035.804.016 1.463-.432 1.463-.987M375.627 584.322c.096-.544-.463-1.103-1.262-1.252-.786-.144-1.513.192-1.613.732-.097.559.472 1.118 1.257 1.262.8.14 1.516-.188 1.618-.741"/></g></svg>
    `
  },

  'google-logo': {
    template: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512"><path d="M113.47 309.408L95.648 375.94l-65.139 1.378C11.042 341.211 0 299.9 0 256c0-42.451 10.324-82.483 28.624-117.732h.014L86.63 148.9l25.404 57.644c-5.317 15.501-8.215 32.141-8.215 49.456.002 18.792 3.406 36.797 9.651 53.408z" fill="#fbbb00"/><path d="M507.527 208.176C510.467 223.662 512 239.655 512 256c0 18.328-1.927 36.206-5.598 53.451-12.462 58.683-45.025 109.925-90.134 146.187l-.014-.014-73.044-3.727-10.338-64.535c29.932-17.554 53.324-45.025 65.646-77.911h-136.89V208.176h245.899z" fill="#518ef8"/><path d="M416.253 455.624l.014.014C372.396 490.901 316.666 512 256 512c-97.491 0-182.252-54.491-225.491-134.681l82.961-67.91c21.619 57.698 77.278 98.771 142.53 98.771 28.047 0 54.323-7.582 76.87-20.818l83.383 68.262z" fill="#28b446"/><path d="M419.404 58.936l-82.933 67.896C313.136 112.246 285.552 103.82 256 103.82c-66.729 0-123.429 42.957-143.965 102.724l-83.397-68.276h-.014C71.23 56.123 157.06 0 256 0c62.115 0 119.068 22.126 163.404 58.936z" fill="#f14336"/></svg>
    `
  },

  'linkedin-logo': {
    template: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 75.77 76.25"><path fill="#0077b5" d="M0 5.47C0 2.45 2.51 0 5.6 0h64.57c3.1 0 5.6 2.45 5.6 5.46v65.33c0 3.02-2.5 5.46-5.6 5.46H5.6c-3.09 0-5.6-2.44-5.6-5.46z"/><path fill="#fff" fill-rule="evenodd" d="M22.97 63.83V29.4H11.53v34.43zM17.25 24.7c3.99 0 6.47-2.64 6.47-5.95-.07-3.38-2.48-5.95-6.4-5.95-3.91 0-6.47 2.57-6.47 5.95 0 3.3 2.48 5.95 6.32 5.95zM29.3 63.83h11.45V44.6c0-1.03.07-2.05.37-2.79.83-2.05 2.71-4.18 5.87-4.18 4.15 0 5.8 3.15 5.8 7.78v18.42h11.45V44.09c0-10.58-5.65-15.5-13.18-15.5-6.17 0-8.88 3.45-10.39 5.8h.08V29.4H29.3c.15 3.23 0 34.43 0 34.43z"/></svg>
    `
  },

  'ugent-logo': {
    template: `
      <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 75.77 76.25"><path fill="#0077b5" d="M0 5.47C0 2.45 2.51 0 5.6 0h64.57c3.1 0 5.6 2.45 5.6 5.46v65.33c0 3.02-2.5 5.46-5.6 5.46H5.6c-3.09 0-5.6-2.44-5.6-5.46z"/><path fill="#fff" fill-rule="evenodd" d="M22.97 63.83V29.4H11.53v34.43zM17.25 24.7c3.99 0 6.47-2.64 6.47-5.95-.07-3.38-2.48-5.95-6.4-5.95-3.91 0-6.47 2.57-6.47 5.95 0 3.3 2.48 5.95 6.32 5.95zM29.3 63.83h11.45V44.6c0-1.03.07-2.05.37-2.79.83-2.05 2.71-4.18 5.87-4.18 4.15 0 5.8 3.15 5.8 7.78v18.42h11.45V44.09c0-10.58-5.65-15.5-13.18-15.5-6.17 0-8.88 3.45-10.39 5.8h.08V29.4H29.3c.15 3.23 0 34.43 0 34.43z"/></svg>
    `
  },

  'socialaccount-provider': {
    props: {
      provider: {
        type: String,
        required: true
      },
      height: {
        type: String,
        default: '32px'
      }
    },
    template: `
      <component :is="comp" :style="{'height': height}"></component>
    `,
    computed: {
      comp: function () {
        return this.provider.toLowerCase() + '-logo';
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
        Evan.api.request('post', this.eventUrl + 'contact/', {
          user_id: this.user.id,
          message: this.msg
        }).then(function (res) {
          Evan.utils.notifySuccess('Message sent.');
        }).catch(function (error) {
          Evan.utils.notifyApiError(error);
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
        <q-input filled dense v-model="q" :placeholder="placeholder" type="search" class="text-mono q-mb-md">
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
                  <q-icon name="clear" @click.stop="delete filterData[filter.name]" class="cursor-pointer" size="14px" />
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
          if (k != 'text') q.push(k + ':' + val[k]);
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
