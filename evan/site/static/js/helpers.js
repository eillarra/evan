var CommonMarkReader = new commonmark.Parser({safe: true, smart: true});
var CommonMarkWriter = new commonmark.HtmlRenderer();

var EventEmitter = new TinyEmitter();
