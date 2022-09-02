var DJANGO_VARS = document.querySelector('html').dataset;


function modelFromUrl(url) {
  var m = url.split('/api/v1/')[1].split('/')[0];
  m = m.substring(0, 1).toUpperCase() + m.substring(1);
  m = (m.substring(m.length - 1) == 's') ? m.slice(0, -1) : m;
  return m;
}


var EventEmitter = new TinyEmitter();
window['moment-range'].extendMoment(moment);

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
    create: function (url, obj, callbackFn, customMsg) {
      this.request('post', url, obj).then(function (res) {
        if (callbackFn) callbackFn(res);
        Evan.utils.notify((customMsg) ? customMsg : modelFromUrl(res.data.self || url) + ' created.');
      }).catch(function (error) {
        Evan.utils.notifyApiError(error);
      });
    },
    update: function (obj, callbackFn, customMsg) {
      this.request('put', obj.self, obj).then(function (res) {
        if (callbackFn) callbackFn(res);
        Evan.utils.notify((customMsg) ? customMsg : modelFromUrl(obj.self) + ' updated.');
      }).catch(function (error) {
        console.log(error);
        Evan.utils.notifyApiError(error);
      });
    },
    remove: function (obj, callbackFn, customMsg) {
      this.request('delete', obj.self).then(function (res) {
        if (callbackFn) callbackFn(res);
        Evan.utils.notify((customMsg) ? customMsg : modelFromUrl(obj.self) + ' deleted.');
      }).catch(function (error) {
        Evan.utils.notifyApiError(error);
      });
    }
  },
  map: {
    none: function (obj) {
      return obj;
    },
    abstract: function (obj) {
      obj.user_name = [obj.user.first_name, obj.user.last_name].join(' ');
      obj.user_affiliation = (obj.user.profile.affiliation) ? obj.user.profile.affiliation : '-';
      obj.date = moment(obj.created_at).format('lll');

      if (obj.reviews) {
        obj.reviewers = obj.reviews.length;
        obj.reviews.map(function (r) {
          try {
            r.score = _.values(r.custom_data.reviews).reduce(function (a, b) { return a + b; }, null);
          } catch (e) {
            r.score = null;
          }
          return r;
        });
        obj.reviews_with_score = obj.reviews.filter(function (r) { return r.score != null; });
        obj.score = _.pluck(obj.reviews_with_score, 'score').reduce(function (a, b) { return a + b; }, null);

        if (obj.reviews_with_score.length > 0) {
          obj.score = Math.round((obj.score / obj.reviews_with_score.length) * 10) / 10;
        }
      } else {
        obj.reviewers = 0;
        obj.score = null;
      }

      obj._q = [
        obj.uuid,
        obj.user_name,
        obj.user_affiliation,
        obj.title.replace(':', ' '),
        obj.authors
      ].join(' ').toLowerCase();

      Evan.map.qBooleans(obj, [
        ['accepted', 'is_accepted'],
      ]);

      Evan.map.qCustomData(obj);

      obj._tags = _.clone(obj._q.split(' ')).filter(function (w) {
        return w.indexOf(':') > -1;
      });

      return obj;
    },
    event: function (obj) {
      var sessionMap = this.session;

      if (!_.has(obj.custom_data, 'dates')) obj.custom_data.dates = [];
      else obj.custom_data.dates.sort(function (a, b) {
        return moment(a.start_date) - moment(b.start_date);
      });

      _.each(obj.sessions, function (s) {
        sessionMap(s);
      });

      obj.start = moment(obj.start_date);
      obj.end = moment(obj.end_date);
      obj.date_range = moment.range(obj.start, obj.end);
      obj.registrationDeadline = moment(obj.registration_deadline);
      obj.registrationEarlyDeadline = moment(obj.registration_early_deadline);

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
        obj.user_name,
        obj.user_affiliation,
        (obj.user.profile.country)
          ? 'country:' + slugify(obj.user.profile.country.name)
          : 'country:unknown',
        (obj.user.profile.custom_data.gender)
          ? 'gender:' + obj.user.profile.custom_data.gender
          : 'gender:unknown',
        (obj.coupon)
          ? 'coupon:' + obj.coupon.code
          : ''
      ].join(' ').toLowerCase();

      Evan.map.qBooleans(obj, [
        ['paid', 'is_paid'],
        ['coupon', 'coupon'],
        ['invoice.requested', 'invoice_requested'],
        ['invoice.sent', 'invoice_sent'],
        ['visa.requested', 'visa_requested'],
        ['visa.sent', 'visa_sent'],
      ]);

      return obj;
    },
    session: function (obj) {
      obj.start = moment(obj.start_at);
      obj.end = moment(obj.end_at);
      obj._q = '';

      return obj;
    },
    qBooleans: function (obj, fields) {
      if (!obj._q) obj._q = '';
      var qs = [];
      _.each(fields, function (f) {
        qs.push(f[0] + ':' + (obj[f[1]] ? 'yes' : 'no'));
      });
      obj._q += ' ' + qs.join(' ').toLowerCase();
    },
    qCustomData: function (obj) {
      if (!obj._q) obj._q = '';
      var qs = [];
      _.each(obj.custom_data, function (value, key) {
        if (_.isString(value)) qs.push(key + ':' + value);
        if (_.isBoolean(value)) qs.push(key + ':' + ((value) ? 'yes' : 'no'));
      });
      obj._q += ' ' + qs.join(' ');
    }
  },
  utils: {
    filter: function (data, q) {
      if (q == '') return data;
      var queries = q.toLowerCase().split(' ');

      return data.filter(function (obj) {
        var matches = 0;
        var _q = obj._q.slice().toLowerCase();
        _.each(queries, function (q) {
          if (_q.indexOf(q) !== -1) matches++;
        });
        return matches == queries.length;
      });
    },
    getFilters: function (data) {
      var filter_collection = {};
      var filters = [];

      if (data.length) {
        _.each(data, function (obj) {
          _.each(obj._q.split(' '), function (w) {
            if (w.indexOf(':') > -1) {
              var f = w.split(':');
              if (!_.has(filter_collection, f[0])) filter_collection[f[0]] = [f[1]];
              else filter_collection[f[0]].push(f[1]);
            }
          });
        });

        _.each(filter_collection, function (values, key) {
          filters.push({
            name: key,
            options: _.uniq(values).sort()
          });
        });
      }

      return filters;
    },
    confirmAction: function (msg, okCallbackFn, cancelCallbackFn) {
      Quasar.Dialog.create({
        message: msg,
        class: 'evan-confirm-dialog q-pa-sm',
        focus: 'none',
        cancel: {
          'flat': true,
          'color': 'grey-8'
        },
        ok: {
          'unelevated': true,
          'color': 'primary'
        }
      }).onOk(okCallbackFn || function () {}).onCancel(cancelCallbackFn || function () {});
    },
    notifyApiError: function (error) {
      var types = {
        400: 'warning',
        401: 'warning',
        403: 'warning',
        500: 'negative'
      }

      var textColors = {
        400: 'grey-8',
        401: 'grey-8',
        403: 'grey-8',
        500: 'white'
      }

      var caption = [error.response.status, ' ', error.response.statusText].join('').toUpperCase() || null;
      var msg = null;

      // 400 Bad Request
      if (error.response.status == 400) {
        var errors = [];
        _.each(_.keys(error.response.data), function (k) {
          errors.push('<strong>' + k + '</strong>: ' + error.response.data[k].join(' '))
        });
        msg = errors.join('<br>') || null;
      }

      // 403 Forbidden || 500 Internal Server Error
      if (error.response.status == 403 || error.response.status == 500) {
        msg = error.response.data.message || null;
      }

      Quasar.Notify.create({
        timeout: 10000,
        progress: true,
        html: true,
        message: msg,
        caption: caption,
        type: types[error.response.status] || 'warning',
        actions: [
          { label: 'Dismiss', color: 'white', handler: function () {} }
        ],
        actions: [
          {
            label: 'Dismiss',
            color: textColors[error.response.status] || 'grey-8',
            handler: function () {}
          }
        ],
        attrs: {
          role: 'alert'
        }
      });
    },
    notify: function (msg, type) {
      Quasar.Notify.create({
        timeout: 2000,
        message: msg,
        type: type || 'positive'
      });
    },
    registerComponents: function (app, collectionList) {
      _.each(collectionList, function (componentCollection) {
        _.each(componentCollection, function (config, componentName) {
          app.component(componentName, config);
        });
      });
    },
    sortText: function (a, b) {
      var a = a.toLowerCase();
      var b = b.toLowerCase();
      if (a < b) return -1;
      if (a > b) return 1;
      return 0;
    }
  },
  cookies: {
    consent: function (msg, acceptBtnText, privacyBtnText, privacyUrl) {
      var cookie = 'cookieconsent';
      if (!Quasar.Cookies.has(cookie)) {
        Quasar.Notify.create({
          timeout: 0,
          message: msg || 'We use cookies to ensure you get the best experience on our website.',
          position: 'bottom-right',
          color: 'primary',
          classes: 'evan-cookies-notify',
          multiLine: true,
          actions: [
            {
              label: acceptBtnText || 'Accept',
              color: 'yellow-7',
              handler: function () {
                Quasar.Cookies.set(cookie, true, {
                  path: '/'
                });
              }
            },
            {
              label: privacyBtnText || 'Learn more',
              color: 'white',
              handler: function () {
                Quasar.openURL(privacyUrl || '/privacy/');
              }
            }
          ]
        });
      }
    }
  }
};
