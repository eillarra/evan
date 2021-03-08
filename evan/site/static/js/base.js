var NICE_DATE_FORMAT = 'dddd, MMM D';
var DJANGO_VARS = document.querySelector('html').dataset;


function modelFromUrl(url) {
  var m = url.split('/api/v1/')[1].split('/')[0];
  m = m.substring(0, 1).toUpperCase() + m.substring(1);
  m = (m.substring(m.length - 1) == 's') ? m.slice(0, -1) : m;
  return m;
}

var Evan = {
  api: {
    request: function (method, url, data, headers) {
      var headers = headers || {};
      headers["X-CSRFTOKEN"] = DJANGO_VARS.csrfToken;
      return axios({
        method: method,
        url: url,
        data: data,
        headers: headers
      });
    },
    update: function (obj, responseCallback) {
      this.request('put', obj.url, obj).then(function (res) {
        if (responseCallback) responseCallback(res);
        Evan.utils.notifySuccess(modelFromUrl(obj.url) + ' updated.');
      }).catch(function (error) {
        Evan.utils.notifyApiError(error);
      });
    }
  },
  map: {
    coupon: function (obj) {
      obj._q = [
        obj.code,
        obj.notes,
      ].join(' ').toLowerCase();
      return obj;
    },
    event: function (obj) {
      return obj;
    },
    registration: function (obj) {
      obj.user_name = [obj.user.first_name, obj.user.last_name].join(' ');
      obj.user_affiliation = (obj.user.profile.affiliation) ? obj.user.profile.affiliation : '-';
      obj.date = moment(obj.created_at).format('lll');
      obj.total_fees = obj.base_fee + obj.extra_fees + obj.manual_extra_fees;
      obj.total_paid = ((obj.coupon) ? obj.coupon.value : 0) + obj.paid + obj.paid_via_invoice;
      obj.is_paid = obj.total_paid >= obj.total_fees;
      obj._q = [
        obj.uuid,
        obj.user.email,
        obj.user_name,
        obj.user_affiliation,
        (obj.user.profile.country) ? obj.user.profile.country.name : ''
      ].join(' ').toLowerCase();
      return obj;
    }
  },
  utils: {
    notifyApiError: function (error) {
      var types = {
        400: 'warning',
        401: 'warning',
        500: 'negative'
      }

      var caption = [error.response.status, ' ', error.response.statusText].join('').toUpperCase() || null;
      var msg = null;

      // 400 Bad Request
      if (error.response.status == 400) {
        var errors = [];
        _.each(_.keys(error.response.data), function (k) {
          errors.push('`' + k + '`: ' + error.response.data[k].join(' '))
        });
        msg = errors.join('\n') || null;
      }

      // 500 Internal Server Error
      if (error.response.status == 500) {
        msg = error.response.data.message || null;
      }

      Quasar.plugins.Notify.create({
        timeout: 5000,
        type: types[error.response.status] || 'warning',
        message: msg,
        caption: caption,
        icon: null
      })
    },
    notifySuccess: function (msg) {
      Quasar.plugins.Notify.create({
        timeout: 2500,
        message: msg,
        icon: null
      })
    },
    sortText: function (a, b) {
      var a = a.toLowerCase();
      var b = b.toLowerCase();
      if (a < b) return -1;
      if (a > b) return 1;
      return 0;
    }
  }
};
