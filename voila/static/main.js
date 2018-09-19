
// Initialize requirejs (for dynamically loading widgets)
// and render widgets on page.

var kernel_id = null;
var scripts = document.getElementsByTagName('script');
Array.prototype.forEach.call(scripts, (script) => {
    kernel_id = script.getAttribute('data-jupyter-kernel-id') || kernel_id;
})

requirejs.config({
    baseUrl: '/voila/static/dist'
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

    var path = window.location.pathname.substr(14);
    var wsWatchdog = new WebSocket(WSURL + '/voila/watchdog/' + path);
    wsWatchdog.onmessage = (evt) => {
        var msg = JSON.parse(evt.data)
        console.log('msg', msg)
        if(msg.type == 'reload') {
            var timeout = 0;
            if(msg.delay == 'long')
                timeout = 1000;
            setTimeout(() => {
                location.href = location.href;
            }, timeout)
        }
    }

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
