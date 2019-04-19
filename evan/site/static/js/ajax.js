$.ajaxSetup({
    headers: {
        'Accept-Language': LANGUAGE
    }
});

function ajax() {
    return {
        head: function (url) {
            return $.ajax({
                method: 'HEAD',
                url: url
            });
        },
        options: function (url) {
            return $.ajax({
                method: 'OPTIONS',
                url: url
            });
        },
        get: function (url, data) {
            return $.ajax({
                method: 'GET',
                url: url,
                data: data || {}
            });
        },
        post: function (url, data) {
            return $.ajax({
                method: 'POST',
                url: url,
                data: JSON.stringify(data),
                contentType: 'application/json; charset=utf-8',
                headers: {
                    'X-CSRFTOKEN': CSRF_TOKEN
                }
            });
        },
        put: function (url, data) {
            return $.ajax({
                method: 'PUT',
                url: url,
                data: JSON.stringify(data),
                contentType: 'application/json; charset=utf-8',
                headers: {
                    'X-CSRFTOKEN': CSRF_TOKEN
                }
            });
        },

        deput: function (store, url, data, customMsg) {
            var msg = customMsg || 'Saving changes...';
            store.commit('startSaving', msg);
            this.put(url, data).done(function (res) {
                store.commit('endSaving', 'Saved!');
            }).fail(function (err) {
                store.commit('parseError', err);
            });
        },

        upload: function (url, formData) {
            return $.ajax({
                method: 'POST',
                url: url,
                data: formData,
                cache: false,
                contentType: false,
                enctype: 'multipart/form-data',
                processData: false,
                headers: {
                    'X-CSRFTOKEN': CSRF_TOKEN
                }
            });
        },
        delete: function (url) {
            return $.ajax({
                method: 'DELETE',
                url: url,
                headers: {
                    'X-CSRFTOKEN': CSRF_TOKEN
                }
            });
        }
    }
};

function api() {
    return {
        getMetadata: function () {
            return ajax().get('/api/v1/metadata/');
        },
        getSession: function (id) {
            return ajax().get('/api/v1/events/sessions/' + id + '/');
        }
    };
}
