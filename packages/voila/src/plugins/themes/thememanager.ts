// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.
import { Dialog, IThemeManager, showDialog } from '@jupyterlab/apputils';
import { IChangedArgs, URLExt } from '@jupyterlab/coreutils';
import {
  ITranslator,
  nullTranslator,
  TranslationBundle
} from '@jupyterlab/translation';
import { DisposableDelegate, IDisposable } from '@lumino/disposable';
import { ISignal, Signal } from '@lumino/signaling';
import { Widget } from '@lumino/widgets';

/**
 * The name for the default JupyterLab light theme
 */
const DEFAULT_JUPYTERLAB_LIGHT_THEME = 'JupyterLab Light';

/**
 * The number of milliseconds between theme loading attempts.
 */
const REQUEST_INTERVAL = 75;

/**
 * The number of times to attempt to load a theme before giving up.
 */
const REQUEST_THRESHOLD = 20;

type Dict<T> = { [key: string]: T };

/**
 * A class that provides theme management. This is a simplified
 * version of the same class in JupyterLab without depending
 * on the setting token.
 */
export class ThemeManager implements IThemeManager {
  /**
   * Construct a new theme manager.
   */
  constructor(options: ThemeManager.IOptions) {
    const { host, url } = options;
    this.translator = options.translator || nullTranslator;
    this._trans = this.translator.load('jupyterlab');

    this._base = url;
    this._host = host;
  }

  /**
   * Get the name of the current theme.
   */
  get theme(): string | null {
    return this._current;
  }

  /**
   * The names of the registered themes.
   */
  get themes(): ReadonlyArray<string> {
    return Object.keys(this._themes);
  }

  /**
   * A signal fired when the application theme changes.
   */
  get themeChanged(): ISignal<this, IChangedArgs<string, string | null>> {
    return this._themeChanged;
  }

  /**
   * Get the value of a CSS variable from its key.
   *
   * @param key - A Jupyterlab CSS variable, without the leading '--jp-'.
   *
   * @returns value - The current value of the Jupyterlab CSS variable
   */
  getCSS(key: string): string {
    return (
      this._overrides[key] ??
      getComputedStyle(document.documentElement).getPropertyValue(`--jp-${key}`)
    );
  }

  /**
   * Load a theme CSS file by path.
   *
   * @param path - The path of the file to load.
   */
  loadCSS(path: string): Promise<void> {
    const base = this._base;
    const href = URLExt.isLocal(path) ? URLExt.join(base, path) : path;
    const links = this._links;

    return new Promise((resolve, reject) => {
      const link = document.createElement('link');

      link.setAttribute('rel', 'stylesheet');
      link.setAttribute('type', 'text/css');
      link.setAttribute('href', href);
      link.addEventListener('load', () => {
        resolve(undefined);
      });
      link.addEventListener('error', () => {
        reject(`Stylesheet failed to load: ${href}`);
      });

      document.body.appendChild(link);
      links.push(link);

      // add any css overrides to document
      this.loadCSSOverrides();
    });
  }

  /**
   * Loads all current CSS overrides from settings. If an override has been
   * removed or is invalid, this function unloads it instead.
   */
  loadCSSOverrides(): void {
    this._overrides = {};
  }

  /**
   * Validate a CSS value w.r.t. a key
   *
   * @param key - A Jupyterlab CSS variable, without the leading '--jp-'.
   *
   * @param val - A candidate CSS value
   */
  validateCSS(key: string, val: string): boolean {
    // determine the css property corresponding to the key
    const prop = this._overrideProps[key];

    if (!prop) {
      console.warn(
        'CSS validation failed: could not find property corresponding to key.\n' +
          `key: '${key}', val: '${val}'`
      );
      return false;
    }

    // use built-in validation once we have the corresponding property
    if (CSS.supports(prop, val)) {
      return true;
    } else {
      console.warn(
        'CSS validation failed: invalid value.\n' +
          `key: '${key}', val: '${val}', prop: '${prop}'`
      );
      return false;
    }
  }

  /**
   * Register a theme with the theme manager.
   *
   * @param theme - The theme to register.
   *
   * @returns A disposable that can be used to unregister the theme.
   */
  register(theme: IThemeManager.ITheme): IDisposable {
    const { name } = theme;
    const themes = this._themes;

    if (themes[name]) {
      throw new Error(`Theme already registered for ${name}`);
    }

    themes[name] = theme;
    this._themeChanged.emit({
      name: '',
      oldValue: null,
      newValue: ''
    });
    return new DisposableDelegate(() => {
      delete themes[name];
    });
  }

  /**
   * Set the current theme.
   */
  async setTheme(name: string): Promise<void> {
    this._requestedTheme = name;
    this._loadSettings();
  }

  /**
   * Test whether a given theme is light.
   */
  isLight(name: string): boolean {
    return this._themes[name].isLight;
  }

  /**
   * Test whether a given theme styles scrollbars,
   * and if the user has scrollbar styling enabled.
   */
  themeScrollbars(name: string): boolean {
    return false;
  }

  /**
   * Get the display name of the theme.
   */
  getDisplayName(name: string): string {
    return this._themes[name]?.displayName ?? name;
  }

  /**
   * Handle the current settings.
   */
  private _loadSettings(): void {
    const outstanding = this._outstanding;
    const pending = this._pending;
    const requests = this._requests;

    // If another request is pending, cancel it.
    if (pending) {
      window.clearTimeout(pending);
      this._pending = 0;
    }

    const themes = this._themes;
    const theme = this._requestedTheme;

    // If another promise is outstanding, wait until it finishes before
    // attempting to load the settings. Because outstanding promises cannot
    // be aborted, the order in which they occur must be enforced.
    if (outstanding) {
      outstanding
        .then(() => {
          this._loadSettings();
        })
        .catch(() => {
          this._loadSettings();
        });
      this._outstanding = null;
      return;
    }

    // Increment the request counter.
    requests[theme] = requests[theme] ? requests[theme] + 1 : 1;

    // If the theme exists, load it right away.
    if (themes[theme]) {
      this._outstanding = this._loadTheme(theme);
      delete requests[theme];
      return;
    }

    // If the request has taken too long, give up.
    if (requests[theme] > REQUEST_THRESHOLD) {
      const fallback = DEFAULT_JUPYTERLAB_LIGHT_THEME;

      // Stop tracking the requests for this theme.
      delete requests[theme];

      if (!themes[fallback]) {
        this._onError(
          this._trans.__(
            'Neither theme %1 nor default %2 loaded.',
            theme,
            fallback
          )
        );
        return;
      }

      console.warn(`Could not load theme ${theme}, using default ${fallback}.`);
      this._outstanding = this._loadTheme(fallback);
      return;
    }

    // If the theme does not yet exist, attempt to wait for it.
    this._pending = window.setTimeout(() => {
      this._loadSettings();
    }, REQUEST_INTERVAL);
  }

  /**
   * Load the theme.
   *
   * #### Notes
   * This method assumes that the `theme` exists.
   */
  private _loadTheme(theme: string): Promise<void> {
    const current = this._current;
    const links = this._links;
    const themes = this._themes;
    const splash = new DisposableDelegate(() => undefined);

    // Unload any CSS files that have been loaded.
    links.forEach((link) => {
      if (link.parentElement) {
        link.parentElement.removeChild(link);
      }
    });
    links.length = 0;

    // Unload the previously loaded theme.
    const old = current ? themes[current].unload() : Promise.resolve();

    return Promise.all([old, themes[theme].load()])
      .then(() => {
        this._current = theme;
        this._themeChanged.emit({
          name: 'theme',
          oldValue: current,
          newValue: theme
        });
        if (this._host) {
          // Need to force a redraw of the app here to avoid a Chrome rendering
          // bug that can leave the scrollbars in an invalid state
          this._host.hide();

          // If we hide/show the widget too quickly, no redraw will happen.
          // requestAnimationFrame delays until after the next frame render.
          requestAnimationFrame(() => {
            this._host!.show();
            Private.fitAll(this._host!);
            splash.dispose();
          });
        }
      })
      .catch((reason) => {
        this._onError(reason);
        splash.dispose();
      });
  }

  /**
   * Handle a theme error.
   */
  private _onError(reason: any): void {
    void showDialog({
      title: this._trans.__('Error Loading Theme'),
      body: String(reason),
      buttons: [Dialog.okButton({ label: this._trans.__('OK') })]
    });
  }

  protected translator: ITranslator;
  private _trans: TranslationBundle;
  private _base: string;
  private _current: string | null = null;
  private _host?: Widget;
  private _links: HTMLLinkElement[] = [];
  private _overrides: Dict<string> = {};
  private _overrideProps: Dict<string> = {};
  private _outstanding: Promise<void> | null = null;
  private _pending = 0;
  private _requests: { [theme: string]: number } = {};
  private _themes: { [key: string]: IThemeManager.ITheme } = {};
  private _themeChanged = new Signal<this, IChangedArgs<string, string | null>>(
    this
  );
  private _requestedTheme = DEFAULT_JUPYTERLAB_LIGHT_THEME;
}

export namespace ThemeManager {
  /**
   * The options used to create a theme manager.
   */
  export interface IOptions {
    /**
     * The host widget for the theme manager.
     */
    host?: Widget;

    /**
     * The url for local theme loading.
     */
    url: string;

    /**
     * The application language translator.
     */
    translator?: ITranslator;
  }
}

/**
 * A namespace for module private data.
 */
namespace Private {
  /**
   * Fit a widget and all of its children, recursively.
   */
  export function fitAll(widget: Widget): void {
    for (const child of widget.children()) {
      fitAll(child);
    }
    widget.fit();
  }
}
