require(['libwidgets'], function(lib) {
    var widgetApp = new lib.WidgetApplication(lib.requireLoader);

    window.addEventListener('beforeunload', function (e) {
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
