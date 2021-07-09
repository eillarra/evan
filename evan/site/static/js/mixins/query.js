var QueryMixin = {
  props: ['q'],
  data: function () {
    return {
      query: this.q || ''
    }
  },
  methods: {
    customFilter: function (rows, terms, cols, getCellValue) {
      return Evan.utils.filter(rows, terms);
    }
  },
  watch: {
    query: function (val, oldVal) {
      if (val != '') this.$router.replace({query: {q: val}});
      else this.$router.replace({query: {q: undefined}});
    }
  },
  created: function () {
    if (this.$route.query.q) {
      this.query = this.$route.query.q;
    }
  }
};
