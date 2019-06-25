/***************************************************************************
* Copyright (c) 2018, Voila contributors                                   *
*                                                                          *
* Distributed under the terms of the BSD 3-Clause License.                 *
*                                                                          *
* The full license is in the file LICENSE, distributed with this software. *
****************************************************************************/

// NOTE: this file is not transpiled, async/await is the only modern feature we use here
require(['voila'], function(voila) {
    // requirejs doesn't like to be passed an async function, so create one inside
    (async function() {
        var kernel = await voila.connectKernel()

        const context = { 
            session: {
                kernel,
                kernelChanged: {
                    connect: () => {}
                },
                statusChanged: {
                    connect: () => {}
                },
            },
            saveState: {
                connect: () => {}
            },
        };

        const settings = {
            saveState: false
        };

        const rendermime = new voila.RenderMimeRegistry({
            initialFactories: voila.standardRendererFactories
        });

        var widgetManager = new voila.WidgetManager(context, rendermime, settings);

        function init() {
            widgetManager.build_widgets();
            // it seems if we attach this to early, it will not be called
            window.addEventListener('beforeunload', function (e) {
                kernel.shutdown()
            });
        }

        if (document.readyState === 'complete') {
            init()
        } else {
            window.addEventListener('load', init);
        }
    })()
});

