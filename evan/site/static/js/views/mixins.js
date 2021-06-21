
var QueryMixin = {
  props: ['q'],
  data: function () {
    return {
      query: this.q || ''
    }
  },
  watch: {
    query: function (val, oldVal) {
      if (val != '') this.$router.replace({query: {q: val}});
      else this.$router.replace({query: {q: undefined}});
    }
  }
};

var EventRelatedMixin = {
  data: function () {
    return {
      tmpObj: null,
      createUrl: null,
      stateVar: null,
      saveEventName: null,
      confirmRemoveMsg: 'Are you sure you want to delete this item?'
    }
  },
  methods: {
    clearObj: function () {
      this.tmpObj = null;
    },
    cloneObj: function (obj) {
      this.tmpObj = _.clone(obj);
    },
    createOrUpdate: function (obj) {
      var self = this;

      if (_.has(obj, 'url')) {
        Evan.api.update(obj, function (res) {
          self.$store.commit('update', {var: self.stateVar, action: 'update', obj: res.data});
        });
      } else {
        Evan.api.create(this.createUrl, obj, function (res) {
          self.$store.commit('update', {var: self.stateVar, action: 'add', obj: res.data});
        });
      }
    },
    remove: function (obj) {
      var self = this;
      Evan.utils.confirmAction(this.confirmRemoveMsg, function () {
        Evan.api.remove(obj, function (res) {
          self.$store.commit('update', {var: self.stateVar, action: 'remove', obj: obj});
        });
      });
    }
  },
  created: function () {
    this.$root.$on(this.saveEventName, this.createOrUpdate);
    this.$root.$on('evan-editor-hide', this.clearObj);
  },
  beforeDestroy: function () {
    this.$root.$off(this.saveEventName);
    this.$root.$off('evan-editor-hide', this.clearObj);
  }
};
