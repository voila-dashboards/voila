/***************************************************************************
* Copyright (c) 2018, Voilà contributors                                   *
*                                                                          *
* Distributed under the terms of the BSD 3-Clause License.                 *
*                                                                          *
* The full license is in the file LICENSE, distributed with this software. *
****************************************************************************/

window.VoilaDebug = VoilaDebug = {
    _widgetManagerPromiseResolve: null,
    _widgetManagerPromise: null,
    async waitForWidgetManager() {
        await _widgetManagerPromise;
    },
    async waitForViews(modelId) {
        const widgetManager = await window.VoilaDebug._widgetManagerPromise;
        const model = await widgetManager._models[modelId];
        await Promise.all(Object.values(model.views))
    },
    async waitForAllViews() {
        const widgetManager = await window.VoilaDebug._widgetManagerPromise;
        for(const modelId in widgetManager._models) {
            await window.VoilaDebug.waitForViews(modelId);
        }
    }
}

window.VoilaDebug._widgetManagerPromise = new Promise((resolve) => window.VoilaDebug._widgetManagerPromiseResolve = resolve),

// NOTE: this file is not transpiled, async/await is the only modern feature we use here
require([window.voila_js_url || 'static/voila'], function(voila) {
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

        async function init() {
            // it seems if we attach this to early, it will not be called
            window.addEventListener('beforeunload', function (e) {
                kernel.shutdown();
                kernel.dispose();
            });
            await widgetManager.build_widgets();
            voila.renderMathJax();
            window.VoilaDebug._widgetManagerPromiseResolve(widgetManager);
        }

        if (document.readyState === 'complete') {
            init()
        } else {
            window.addEventListener('load', init);
        }
    })()
});

