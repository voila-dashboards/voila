define(['jquery', 'base/js/namespace'], function($, Jupyter) {
    "use strict";
    var open_voila = function() {
        let notebook_path =  Jupyter.notebook.notebook_path;
        let voila_path = notebook_path.slice(0, notebook_path.length-6);  // without .ipynb
        let voila_url = Jupyter.notebook.base_url + "voila/render/" + voila_path;
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
