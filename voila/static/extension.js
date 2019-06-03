define(['jquery', 'base/js/namespace'], function($, Jupyter) {
    "use strict";
    var open_voila = function() {
        let voila_url = Jupyter.notebook.base_url + "voila/render/" + Jupyter.notebook.notebook_path;
        window.open(voila_url)

    }
    var load_ipython_extension = function() {
        Jupyter.toolbar.add_buttons_group([{
            id : 'toggle_codecells',
            label : 'Voila',
            icon : 'fa-desktop',
            callback : open_voila
        }]);
    };
    return {
        load_ipython_extension : load_ipython_extension
    };
});
