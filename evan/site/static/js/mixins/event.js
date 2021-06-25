var EventDatesMixin = {
  computed: {
    dates: function () {
      if (!this.event.custom_data.dates || !this.event.custom_data.dates.length) return [];

      return this.event.custom_data.dates.map(function (d) {
        d.startDate = moment(d.start_date);
        if (d.format == 'range' && d.end_date) {
          d.formatted = d.startDate.format('MMM D') + '-' + moment(d.end_date).format('D, Y');
        } else {
          d.formatted = d.startDate.format({
            'date': 'MMM D, Y',
            'month': 'MMM Y'
          }[d.format] || 'MMMM Y');
        }
        return d;
      }).sort(function (a, b) {
        return a.startDate.diff(b.startDate);
      });
    }
  }
};
