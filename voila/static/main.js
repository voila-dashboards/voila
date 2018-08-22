
// Initialize requirejs (for dynamically loading widgets)
// and render widgets on page.

requirejs.config({
    baseUrl: 'static/dist'
})

require(['libwidgets'], function(lib) {
    var BASEURL = window.location.href

    var WSURL;
    if (window.location.protocol.startsWith('https')) {
        WSURL = 'wss://' + window.location.host
    }
    else {
        WSURL = 'ws://' + window.location.host
    }

    var widgetApp = new lib.WidgetApplication(BASEURL, WSURL, lib.requireLoader, window.kernel_id);

    window.addEventListener("beforeunload", function (e) {
        widgetApp.cleanWidgets();
    });

    if (document.readyState === 'complete') {
        widgetApp.renderWidgets();
    } else {
        window.addEventListener(
            'load',
            function() {
                widgetApp.renderWidgets();
            }
        );
    }
});
