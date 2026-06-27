// 拦截fetch + clipboard
(function() {
    var origFetch = window.fetch;
    window.fetch = function() {
        return origFetch.apply(this, arguments).then(function(r) {
            var clone = r.clone();
            clone.text().then(function(t) {
                if (t.length < 2000 && (t.indexOf('subscribe') > -1 || t.indexOf('token') > -1)) {
                    window.__api_result = t;
                }
            });
            return r;
        });
    };

    // 拦截clipboard
    if (!navigator.clipboard) {
        Object.defineProperty(navigator, 'clipboard', {value: {}, configurable: true});
    }
    var origWrite = navigator.clipboard.writeText;
    navigator.clipboard.writeText = function(text) {
        window.__captured_clipboard = text;
        if (origWrite) return origWrite.call(navigator.clipboard, text);
        return Promise.resolve();
    };
})();
