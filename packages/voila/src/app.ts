import { PromiseDelegate } from '@lumino/coreutils';

import {
  JupyterFrontEnd,
  JupyterFrontEndPlugin,
  createRendermimePlugins
} from '@jupyterlab/application';

import { PageConfig } from '@jupyterlab/coreutils';

import { IRenderMime } from '@jupyterlab/rendermime';

import { IShell, VoilaShell } from './shell';

const PACKAGE = require('../package.json');

/**
 * App is the main application class. It is instantiated once and shared.
 */
export class VoilaApp extends JupyterFrontEnd<IShell> {
  /**
   * Construct a new App object.
   *
   * @param options The instantiation options for an application.
   */
  constructor(options: App.IOptions) {
    super({
      ...options,
      shell: options.shell ?? new VoilaShell()
    });
    if (options.mimeExtensions) {
      for (const plugin of createRendermimePlugins(options.mimeExtensions)) {
        this.registerPlugin(plugin);
      }
    }
  }

  /**
   * The name of the application.
   */
  readonly name: string = 'Voila';

  /**
   * A namespace/prefix plugins may use to denote their provenance.
   */
  readonly namespace = this.name;

  /**
   * The version of the application.
   */
  readonly version = PACKAGE['version'];

  /**
   * The JupyterLab application paths dictionary.
   */
  get paths(): JupyterFrontEnd.IPaths {
    return {
      urls: {
        base: PageConfig.getOption('baseUrl'),
        notFound: PageConfig.getOption('notFoundUrl'),
        app: PageConfig.getOption('appUrl'),
        static: PageConfig.getOption('staticUrl'),
        settings: PageConfig.getOption('settingsUrl'),
        themes: PageConfig.getOption('themesUrl'),
        doc: PageConfig.getOption('docUrl'),
        translations: PageConfig.getOption('translationsApiUrl'),
        hubHost: PageConfig.getOption('hubHost') || undefined,
        hubPrefix: PageConfig.getOption('hubPrefix') || undefined,
        hubUser: PageConfig.getOption('hubUser') || undefined,
        hubServerName: PageConfig.getOption('hubServerName') || undefined
      },
      directories: {
        appSettings: PageConfig.getOption('appSettingsDir'),
        schemas: PageConfig.getOption('schemasDir'),
        static: PageConfig.getOption('staticDir'),
        templates: PageConfig.getOption('templatesDir'),
        themes: PageConfig.getOption('themesDir'),
        userSettings: PageConfig.getOption('userSettingsDir'),
        serverRoot: PageConfig.getOption('serverRoot'),
        workspaces: PageConfig.getOption('workspacesDir')
      }
    };
  }

  /**
   * Register plugins from a plugin module.
   *
   * @param mod - The plugin module to register.
   */
  registerPluginModule(mod: App.IPluginModule): void {
    let data = mod.default;
    // Handle commonjs exports.
    if (!Object.prototype.hasOwnProperty.call(mod, '__esModule')) {
      data = mod as any;
    }
    if (!Array.isArray(data)) {
      data = [data];
    }
    data.forEach((item) => {
      try {
        this.registerPlugin(item);
      } catch (error) {
        console.error(error);
      }
    });
  }

  /**
   * Register the plugins from multiple plugin modules.
   *
   * @param mods - The plugin modules to register.
   */
  registerPluginModules(mods: App.IPluginModule[]): void {
    mods.forEach((mod) => {
      this.registerPluginModule(mod);
    });
  }

  /**
   * A promise that resolves when the Voila Widget Manager is created
   */
  get widgetManagerPromise(): PromiseDelegate<any> {
    return this._widgetManagerPromise;
  }

  set widgetManager(manager: any) {
    this._widgetManager = manager;
    if (this._widgetManager) {
      this._widgetManagerPromise.resolve(this._widgetManager);
    }
  }

  get widgetManager(): any {
    return this._widgetManager;
  }

  protected _widgetManager: any = null;
  protected _widgetManagerPromise = new PromiseDelegate<any>();
}

/**
 * A namespace for App statics.
 */
export namespace App {
  /**
   * The instantiation options for an App application.
   */
  export interface IOptions
    extends JupyterFrontEnd.IOptions<IShell>,
      Partial<IInfo> {
    paths?: Partial<JupyterFrontEnd.IPaths>;
  }

  /**
   * The information about a Voila application.
   */
  export interface IInfo {
    /**
     * The mime renderer extensions.
     */
    readonly mimeExtensions: IRenderMime.IExtensionModule[];
  }

  /**
   * The interface for a module that exports a plugin or plugins as
   * the default value.
   */
  export interface IPluginModule {
    /**
     * The default export.
     */
    default: JupyterFrontEndPlugin<any> | JupyterFrontEndPlugin<any>[];
  }
}
