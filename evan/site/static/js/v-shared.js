var CommonMarkReader = new commonmark.Parser({safe: true, smart: true});
var CommonMarkWriter = new commonmark.HtmlRenderer();

var EventHub = new Vue();

Vue.filter('moment', function (date, format) {
  return moment(date).format(format || 'll');
});

Vue.filter('markdown', function (text) {
  return CommonMarkWriter.render(CommonMarkReader.parse(text));
});

Vue.component('marked', {
  props: {
    text: {
      type: String,
      default: ''
    }
  },
  template: '' +
    '<div class="marked" v-html="compiledMarkdown"></div>' +
  '',
  computed: {
    compiledMarkdown: function () {
      if (!this.text || this.text == '') return this.text;
      return CommonMarkWriter.render(CommonMarkReader.parse(this.text));
    }
  }
});

Vue.directive('tooltip', function (el, binding) {
    var val = binding.value;

    $(el).tooltip({
        title: (val) ? val : '',
        placement: 'bottom',
        trigger: 'hover',
        delay: {show: 400, hide: 0}
    });
});

Vue.component('a-div', {
    props: ['href'],
    template: '<div @click="goTo" class="pointer"><slot></slot></div>',
    methods: {
        goTo: function () {
            var w = window.open(this.href, '_self');
            w.focus();
        }
    },
});

Vue.component('time-to', {
    data: function () {
        return {
            currentTime: moment()
        };
    },
    props: ['time'],
    template: '<span>{{ display }}</span>',
    computed: {
        display: function () {
            return this.currentTime.to(this.time);
        }
    },
    created: function () {
        var self = this;
        setInterval(function () {
            self.currentTime = moment();
        }, 1000);
    }
});

Vue.component('loading', {
    data: function () {
        return {
            visible: false
        };
    },
    template: '' +
        '<span v-show="visible" class="shadow badge badge-pill badge-primary badge-loading px-2">' +
            '<i class="material-icons">autorenew</i> Loading...' +
        '</span>' +
    '',
    methods: {
        show: function (val) {
            var self = this;
            setTimeout(function () {
                self.visible = val;
            }, (val) ? 0 : 250);
        }
    },
    created: function () {
        EventHub.$on('loading', this.show);
    },
    beforeDestroy: function () {
        EventHub.$off('loading');
    }
});

Vue.component('country-flag', {
    props: ['country'],
    template: '<i v-tooltip="title" class="help" :class="css"></i>',
    computed: {
        title: function () {
            return (this.country) ? this.country.name : null;
        },
        css: function () {
            var code = (this.country) ? this.country.code : 'ZZ';
            try {
                var c = code.toLowerCase().split('');
                return 'flag-sprite flag-' + c[0] + ' flag-_' + c[1];
            } catch (err) {
                return '';
            }
        }
    }
});

Vue.component('saving-bar', {
    data: function () {
        return {
            saving: false
        }
    },
    props: {
        text: {
            type: String,
            default: 'All information is up to date'
        }
    },
    template: '' +
        '<div class="sticky-top msg-bar">' +
            '<div v-if="saving" class="bg-light-blue py-1 px-4 text-info">' +
                '<i class="material-icons mt-1 float-right">&#xE837;</i>' +
                '<small>Saving...</small>' +
            '</div>' +
            '<div v-else class="bg-light py-1 px-4 text-secondary">' +
                '<i class="material-icons mt-1 float-right">&#xE86C;</i>' +
                '<small>{{ text }}</small>' +
            '</div>' +
        '</div>' +
    '',
    methods: {
        savingStatus: function (val) {
            var self = this;
            if (val === false) {
                setTimeout(function () {
                    self.saving = false;
                }, 300);
            } else this.saving = val;
        }
    },
    created: function () {
        EventHub.$on('saving', this.savingStatus);
    },
    beforeDestroy: function () {
        EventHub.$off('saving');
    }
});

Vue.component('search-box', {
    data: function () {
        return {
            q: ''
        }
    },
    props: {
        eventName: {
            type: String,
            default: 'query-changed'
        },
        placeholder: {
            type: String,
            default: 'Search...'
        },
        examples: {
            type: Array,
            default: function () {
                return [];
            }
        },
    },
    template: '' +
        '<div>' +
            '<div class="input-group">' +
                '<input v-model="q" type="text" class="form-control" :placeholder="placeholder">' +
                '<div class="input-group-append dropdown pointer">' +
                    '<span v-show="q" class="input-group-text">' +
                        '<i @click="q = \'\'" class="material-icons text-secondary">&#xE5CD;</i>' +
                    '</span>' +
                    '<slot></slot>' +
                '</div>' +
            '</div>' +
            '<p v-if="examples.length" class="d-none d-md-block text-secondary mt-1">' +
                '<small>{{ \'searchExamples\' | trans }}</small>' +
                '<a v-for="example in examples" @click.prevent="q = example" class="ml-3" href="#">' +
                    '<small>{{ example }}</small>' +
                '</a>' +
            '</p>' +
        '</div>' +
    '',
    watch: {
        'q': _.debounce(function (val, oldVal) {
            if (val != oldVal) {
                if (this.$route) {
                    if (val != '') this.$router.replace({query: {q: val}});
                    else this.$router.replace({name: this.$route.name});
                }
                EventHub.$emit(this.eventName, val);
            }
        }, 200)
    },
    created: function () {
        if (this.$route && this.$route.query.q) {
            this.q = this.$route.query.q;
            EventHub.$emit(this.eventName, this.q);
        }
    }
});

Vue.component('box-skeleton', {
    props: ['height'],
    template: '' +
        '<div class="box-skeleton" :style="{height: height}"></div>' +
    ''
});

Vue.component('table-skeleton', {
    props: ['items'],
    template: '' +
        '<table class="table table-sm table-skeleton">' +
            '<tr v-for="n in _.range(items)">' +
                '<td><span></span></td>' +
            '</tr>' +
        '</table>' +
    ''
});
