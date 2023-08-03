/***************************************************************************
 * Copyright (c) 2018, Voilà contributors                                   *
 * Copyright (c) 2018, QuantStack                                           *
 *                                                                          *
 * Distributed under the terms of the BSD 3-Clause License.                 *
 *                                                                          *
 * The full license is in the file LICENSE, distributed with this software. *
 ****************************************************************************/
import { JupyterFrontEnd } from '@jupyterlab/application';
import { DocumentRegistry } from '@jupyterlab/docregistry';
import { ArrayExt } from '@lumino/algorithm';
import { IMessageHandler, Message, MessageLoop } from '@lumino/messaging';
import { Debouncer } from '@lumino/polling';
import { Signal } from '@lumino/signaling';
import { BoxLayout, BoxPanel, Panel, Widget } from '@lumino/widgets';

export type IShell = VoilaShell;

/**
 * A namespace for Shell statics
 */
export namespace IShell {
  /**
   * The areas of the application shell where widgets can reside.
   */
  export type Area =
    | 'main'
    | 'header'
    | 'top'
    | 'menu'
    | 'left'
    | 'right'
    | 'bottom'
    | 'down';
}

/**
 * The class name added to AppShell instances.
 */
const APPLICATION_SHELL_CLASS = 'jp-LabShell';

/**
 * The default rank of items added to a sidebar.
 */
const DEFAULT_RANK = 900;

/**
 * The application shell.
 */
export class VoilaShell extends Widget implements JupyterFrontEnd.IShell {
  constructor() {
    super();
    this.id = 'main';
    const rootLayout = new BoxLayout();
    rootLayout.alignment = 'start';
    rootLayout.spacing = 0;
    this.addClass(APPLICATION_SHELL_CLASS);

    const topHandler = (this._topHandler = new Private.PanelHandler());
    topHandler.panel.id = 'voila-top-panel';
    topHandler.panel.node.setAttribute('role', 'banner');
    BoxLayout.setStretch(topHandler.panel, 0);
    topHandler.panel.hide();
    rootLayout.addWidget(topHandler.panel);

    const hboxPanel = (this._mainPanel = new BoxPanel());
    hboxPanel.id = 'jp-main-content-panel';
    hboxPanel.direction = 'top-to-bottom';
    BoxLayout.setStretch(hboxPanel, 1);
    rootLayout.addWidget(hboxPanel);

    const bottomPanel = (this._bottomPanel = new Panel());
    bottomPanel.node.setAttribute('role', 'contentinfo');
    bottomPanel.id = 'voila-bottom-panel';
    BoxLayout.setStretch(bottomPanel, 0);
    rootLayout.addWidget(bottomPanel);
    bottomPanel.hide();

    this.layout = rootLayout;
  }

  /**
   * The current widget in the shell's main area.
   */
  get currentWidget(): Widget | null {
    return this._mainPanel.widgets[0];
  }

  activateById(id: string): void {
    // no-op
  }

  /**
   * Add a widget to the application shell.
   *
   * @param widget - The widget being added.
   *
   * @param area - Optional region in the shell into which the widget should
   * be added.
   *
   */
  add(
    widget: Widget,
    area?: IShell.Area,
    options?: DocumentRegistry.IOpenOptions
  ): void {
    switch (area) {
      case 'top':
        this._addToTopArea(widget, options);
        break;
      case 'bottom':
        this._addToBottomArea(widget, options);
        break;
      case 'main':
        this._mainPanel.addWidget(widget);
        break;
      default:
        console.warn(`Area ${area} is not implemented yet!`);
        break;
    }
  }

  widgets(area: IShell.Area): IterableIterator<Widget> {
    switch (area) {
      case 'top':
        return this._topHandler.panel.children();
      case 'bottom':
        return this._bottomPanel.children();
      case 'main':
        this._mainPanel.children();
        break;
      default:
        return [][Symbol.iterator]();
    }
    return [][Symbol.iterator]();
  }

  /**
   * Add a widget to the top content area.
   *
   * #### Notes
   * Widgets must have a unique `id` property, which will be used as the DOM id.
   */
  private _addToTopArea(
    widget: Widget,
    options?: DocumentRegistry.IOpenOptions
  ): void {
    if (!widget.id) {
      console.error('Widgets added to app shell must have unique id property.');
      return;
    }
    options = options || {};
    const rank = options.rank ?? DEFAULT_RANK;
    this._topHandler.addWidget(widget, rank);
    this._onLayoutModified();
    if (this._topHandler.panel.isHidden) {
      this._topHandler.panel.show();
    }
  }

  /**
   * Add a widget to the bottom content area.
   *
   * #### Notes
   * Widgets must have a unique `id` property, which will be used as the DOM id.
   */
  private _addToBottomArea(
    widget: Widget,
    options?: DocumentRegistry.IOpenOptions
  ): void {
    if (!widget.id) {
      console.error('Widgets added to app shell must have unique id property.');
      return;
    }
    this._bottomPanel.addWidget(widget);
    this._onLayoutModified();

    if (this._bottomPanel.isHidden) {
      this._bottomPanel.show();
    }
  }

  /**
   * Handle a change to the layout.
   */
  private _onLayoutModified(): void {
    void this._layoutDebouncer.invoke();
  }

  private _topHandler: Private.PanelHandler;
  private _mainPanel: BoxPanel;
  private _bottomPanel: Panel;
  private _layoutDebouncer = new Debouncer(() => {
    this._layoutModified.emit(undefined);
  }, 0);
  private _layoutModified = new Signal<this, void>(this);
}

namespace Private {
  /**
   * An object which holds a widget and its sort rank.
   */
  export interface IRankItem {
    /**
     * The widget for the item.
     */
    widget: Widget;

    /**
     * The sort rank of the widget.
     */
    rank: number;
  }

  /**
   * A less-than comparison function for side bar rank items.
   */
  export function itemCmp(first: IRankItem, second: IRankItem): number {
    return first.rank - second.rank;
  }

  /**
   * A class which manages a panel and sorts its widgets by rank.
   */
  export class PanelHandler {
    constructor() {
      MessageLoop.installMessageHook(this._panel, this._panelChildHook);
    }

    /**
     * Get the panel managed by the handler.
     */
    get panel(): Panel {
      return this._panel;
    }

    /**
     * Add a widget to the panel.
     *
     * If the widget is already added, it will be moved.
     */
    addWidget(widget: Widget, rank: number): void {
      widget.parent = null;
      const item = { widget, rank };
      const index = ArrayExt.upperBound(this._items, item, Private.itemCmp);
      ArrayExt.insert(this._items, index, item);
      this._panel.insertWidget(index, widget);
    }

    /**
     * A message hook for child add/remove messages on the main area dock panel.
     */
    private _panelChildHook = (
      handler: IMessageHandler,
      msg: Message
    ): boolean => {
      switch (msg.type) {
        case 'child-added':
          {
            const widget = (msg as Widget.ChildMessage).child;
            // If we already know about this widget, we're done
            if (this._items.find((v) => v.widget === widget)) {
              break;
            }

            // Otherwise, add to the end by default
            const rank = this._items[this._items.length - 1].rank;
            this._items.push({ widget, rank });
          }
          break;
        case 'child-removed':
          {
            const widget = (msg as Widget.ChildMessage).child;
            ArrayExt.removeFirstWhere(this._items, (v) => v.widget === widget);
          }
          break;
        default:
          break;
      }
      return true;
    };

    private _items = new Array<Private.IRankItem>();
    private _panel = new Panel();
  }
}
