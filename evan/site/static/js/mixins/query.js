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
