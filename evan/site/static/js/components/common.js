var EvanCommonComponents = {

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
    template: '<span></span>',
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
        }[this.level] || 'info',
        actions: [
          { label: 'Dismiss', color: 'white', handler: function () {} }
        ]
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
    template: `
      <q-icon name="backspace" color="red-12" class="cursor-pointer" />
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
    template: '<q-chip square :color="color" text-color="white" size="xs" :icon="icon" class="evan-chip">Yes</q-chip>'
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
    template: '<q-chip square outline :color="color" size="xs" :icon="icon" class="evan-chip">No</q-chip>'
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
  }

};
