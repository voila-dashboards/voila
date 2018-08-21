
import { RenderMimeRegistry, standardRendererFactories } from '@jupyterlab/rendermime';

import { WIDGET_MIMETYPE, WidgetRenderer } from '@jupyter-widgets/html-manager/lib/output_renderers';

export function createSimpleRenderMimeRegistry() {
    const renderMime = new RenderMimeRegistry({
        initialFactories: standardRendererFactories
    });
    return renderMime
}

export function createRenderMimeRegistryWithWidgets(manager) {
    const renderMime = createSimpleRenderMimeRegistry()

    renderMime.addFactory({
        safe: false,
        mimeTypes: [WIDGET_MIMETYPE],
        createRenderer: options => new WidgetRenderer(options, manager)
    }, 1)

    return renderMime;
}
