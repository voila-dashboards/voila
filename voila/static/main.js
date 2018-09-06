
// Initialize requirejs (for dynamically loading widgets)
// and render widgets on page.

var kernel_id = null;
var scripts = document.getElementsByTagName('script');
Array.prototype.forEach.call(scripts, (script) => {
    kernel_id = script.getAttribute('data-jupyter-kernel-id') || kernel_id;
})

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

    var widgetApp = new lib.WidgetApplication(BASEURL, WSURL, lib.requireLoader, kernel_id);

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
