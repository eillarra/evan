var DELAY = 1000;

function textSort(a, b) {
    var a = a.toLowerCase();
    var b = b.toLowerCase();
    if (a < b) return -1;
    if (a > b) return 1;
    return 0;
}

var getParsedErrors = function (err) {
    var errors = _.map(err.responseJSON, function(msg, key) {
        return '"' + key.replace(/_/g, ' ') + '": ' + JSON.stringify(msg);
    });
    return errors.join(' ');
}

function getDescendantProp(obj, desc) {
    var arr = desc.split('.');
    while(arr.length && (obj = obj[arr.shift()]));
    return obj;
}
