/*eslint no-var: 0*/

declare function __webpack_init_sharing__(arg: any);
declare var _JUPYTERLAB;
declare var __webpack_share_scopes__: any;
declare var jupyterapp: any;
interface ICellData {
  cell_count: number;
  cell_type: string;
  cell_source: string;
}

declare function update_loading_text(
  cell_index: number,
  cell_count: number,
  text: string | null
);
declare function display_cells();
