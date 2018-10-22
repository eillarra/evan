var DELAY = 1000;

var textSort = function (key) {
    return function (a, b) {
        if (a[key].toLowerCase() < b[key].toLowerCase()) return -1;
        if (a[key].toLowerCase() > b[key].toLowerCase()) return 1;
        return 0;
    }
}

var getParsedErrors = function (err) {
    var errors = _.map(err.responseJSON, function(msg, key) {
        return '"' + key.replace(/_/g, ' ') + '": ' + JSON.stringify(msg);
    });
    return errors.join(' ');
}
