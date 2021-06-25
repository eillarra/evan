var CustomFieldsMixin = {
  data: function () {
    return {
      module: 'default',
      createUrl: null,
      useFeeTargets: false,
      obj: null
    };
  },
  computed: _.extend(
    Vuex.mapState(['event']), {
    replaceMainForm: function () {
      if (!this.event || !_.has(this.event.custom_fields, this.module)) return false;
      return this.event.custom_fields[this.module].replace;
    },
    fieldsets: function () {
      if (!this.event || !_.has(this.event.custom_fields, this.module)) return null;
      if (!_.has(this.event.custom_fields[this.module], 'fieldsets')) return [];

      // TODO: ADD FEE FILTER

      return this.event.custom_fields[this.module].fieldsets;
    },
    customFormIsValid: function () {
      var obj = this.obj;
      var errors = [];

      if (!obj) return false;

      _.each(this.fieldsets, function (fieldset) {
        _.each(fieldset.fields, function (f) {
          if (
            (f.mandatory && !_.has(obj.custom_data, f.id))
            || (f.mandatory && _.has(obj.custom_data, f.id) && obj.custom_data[f.id] === false)
            || (f.required && obj.custom_data[f.id] === null)
          ) {
            errors.push(true);
          }
        });
      });

      return !_.contains(errors, true);
    },
    formIsValid: function () {
      return this.customFormIsValid;
    }
  }),
  methods: {
    createOrUpdate: function (obj) {
      var self = this;

      if (_.has(obj, 'url')) {
        Evan.api.update(obj, function (res) {
          self.obj = res.data;
        });
      } else {
        Evan.api.create(this.createUrl, obj, function (res) {
          window.history.pushState('', '', res.data.href + self.$route.href);
          window.scrollTo(0, 0);
          self.obj = res.data;
        });
      }
    },
    fixObj: function () {
      var self = this;

      if (!this.event || !this.obj) {
        setTimeout(function () { self.fixObj(); }, 25);
        return;
      };

      if (this.fieldsets.length) {
        _.each(this.fieldsets, function (fieldset) {
          if (fieldset.taxonomy) {
            if (!_.has(self.obj.custom_data, 'track')) self.obj.custom_data.track = null;
            if (!_.has(self.obj.custom_data, 'topics')) self.obj.custom_data.topics = [];
          }

          _.each(fieldset.fields, function (f) {
            if (!_.has(self.obj.custom_data, f.id)) {
              self.obj.custom_data[f.id] = {
                'text': null,
                'text_list': [],
                'single_choice': null,
                'multiple_choice': [],
                'checkbox': f.default
              }[f.type];
            }
          });
        });
      }
    }
  },
  created: function () {
    this.fixObj();
  }
};
