// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.


import { PageConfig, URLExt } from '@jupyterlab/coreutils';
__webpack_public_path__ = URLExt.join(PageConfig.getBaseUrl(), 'voila/static/');

import { JupyterLab } from '@jupyterlab/application';

import {
  IRenderMimeRegistry,
  RenderMimeRegistry,
  standardRendererFactories,
  ILatexTypesetter
} from '@jupyterlab/rendermime';

import { PromiseDelegate } from '@phosphor/coreutils';

import { WidgetRenderer } from '@jupyter-widgets/jupyterlab-manager';

import * as base from '@jupyter-widgets/base';

export { connectKernel } from './kernel';

import { VoilaManager } from './labmanager';

export { VoilaManager } from './labmanager';


const WIDGET_VIEW_MIMETYPE = 'application/vnd.jupyter.widget-view+json';


/**
 * Activate the rendermine plugin.
 */
function activateRenderMime(app, latexTypesetter) {
    return new RenderMimeRegistry({
        initialFactories: standardRendererFactories,
        latexTypesetter
    });
}


export async function createWidgetManager(kernel, extensions) {

    import('font-awesome/css/font-awesome.min.css');

    const managerPromise = new PromiseDelegate();

    /**
     * The widget manager provider.
     */
    const plugin = {
        id: 'voila:widget-manager-plugin',
        requires: [IRenderMimeRegistry],
        provides: base.IJupyterWidgetRegistry,
        activate: (app, rendermime) => {

            const wManager = new VoilaManager(kernel, rendermime);

            // Add a placeholder widget renderer.
            rendermime.addFactory({
                safe: false,
                mimeTypes: [WIDGET_VIEW_MIMETYPE],
                createRenderer: options => new WidgetRenderer(options, wManager)
            }, 0);

            wManager.restored.connect(() => {
                managerPromise.resolve(wManager);
            });

            return {
                registerWidget(data) {
                    wManager.register(data);
                }
            };
        },
        autoStart: true
    };


    /**
     * A plugin providing a rendermime registry.
     */
    const renderMimePluign = {
        id: 'voila:rendermime-plugin',
        requires: [],
        optional: [ILatexTypesetter],
        provides: IRenderMimeRegistry,
        activate: activateRenderMime,
        autoStart: true
    };

    let mods = [
        import('@jupyterlab/application-extension'),
        import('@jupyterlab/apputils-extension'),
        import('@jupyterlab/codemirror-extension'),
        import('@jupyterlab/markdownviewer-extension'),
        import('@jupyterlab/mathjax2-extension'),
        import('@jupyterlab/rendermime-extension'),
        import('@jupyterlab/shortcuts-extension'),
        import('@jupyterlab/theme-dark-extension'),
        import('@jupyterlab/theme-light-extension'),
        renderMimePluign,
        plugin
    ];
    if (extensions) {
        mods = mods.concat(extensions);
    }
    const lab = new JupyterLab({
        name: 'JupyterLab Voila App',
        namespace: 'voila-lab-manager',
        version: require('../package.json').version
    });
    lab.registerPluginModules(mods);
    lab.start().then(() => {
        // eslint-disable-next-line
        console.log('Voila lab app started!');
    });

    return managerPromise.promise;
}
