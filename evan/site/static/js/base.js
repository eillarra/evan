var DJANGO_VARS = document.querySelector('html').dataset;


function modelFromUrl(url) {
  var m = url.split('/api/v1/')[1].split('/')[0];
  m = m.substring(0, 1).toUpperCase() + m.substring(1);
  m = (m.substring(m.length - 1) == 's') ? m.slice(0, -1) : m;
  return m;
}


var Evan = {
  csrf: {
    getToken: function () {
      return DJANGO_VARS.csrfToken;
    }
  },
  utils: {
    registerComponents: function (app, collectionList) {
      _.each(collectionList, function (componentCollection) {
        _.each(componentCollection, function (config, componentName) {
          app.component(componentName, config);
        });
      });
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
