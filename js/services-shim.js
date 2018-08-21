// Copyright (c) Jupyter Development Team.
// Distributed under the terms of the Modified BSD License.

// Copied from https://github.com/jupyter-widgets/ipywidgets/blob/master/packages/base/src/services-shim.ts

/**
 * This module defines shims for @jupyterlab/services that allows you to use the
 * old comm API.  Use this, @jupyterlab/services, and the widget base manager to
 * embed live widgets in a context outside of the notebook.
 */

// Modified this slightly to also intercept error messages from the
// kernel so they can be displayed in the error area.

import { Kernel } from '@jupyterlab/services';


export class ShimmedComm  {
    constructor(jsServicesComm) {
        this.jsServicesComm = jsServicesComm;
        this.comm_id = this.jsServicesComm.commId
        this.target_name = this.jsServicesComm.targetName
    }


    /**
    * Opens a sibling comm in the backend
    */
    open(data, callbacks, metadata, buffers) {
        const future = this.jsServicesComm.open(data, metadata, buffers);
        this._hookupCallbacks(future, callbacks);
        return future.msg.header.msg_id;
    }

    /**
    * Sends a message to the sibling comm in the backend
    */
    send(data, callbacks, metadata, buffers) {
        let future = this.jsServicesComm.send(data, metadata, buffers);
        this._hookupCallbacks(future, callbacks);
        return future.msg.header.msg_id;
    }

    /**
    * Closes the sibling comm in the backend
    */
    close(data, callbacks, metadata, buffers) {
        let future = this.jsServicesComm.close(data, metadata, buffers);
        this._hookupCallbacks(future, callbacks);
        return future.msg.header.msg_id;
    }

    /**
    * Register a message handler
    */
    on_msg(callback) {
        this.jsServicesComm.onMsg = callback.bind(this);
    }

    /**
    * Register a handler for when the comm is closed by the backend
    */
    on_close(callback) {
        this.jsServicesComm.onClose = callback.bind(this);
    }

    /**
    * Hooks callback object up with @jupyterlab/services IKernelFuture
    */
    _hookupCallbacks(future, callbacks) {
        if (callbacks) {
            future.onReply = function(msg) {
                if (callbacks.shell && callbacks.shell.reply) {
                    callbacks.shell.reply(msg);
                }
                // TODO: Handle payloads.  See https://github.com/jupyter/notebook/blob/master/notebook/static/services/kernels/kernel.js#L923-L947
            };

            future.onStdin = function(msg) {
                if (callbacks.input) {
                    callbacks.input(msg);
                }
            };

            future.onIOPub = function(msg) {
                if (callbacks.iopub) {
                    if (callbacks.iopub.status && msg.header.msg_type === 'status') {
                        callbacks.iopub.status(msg);
                    } else if (callbacks.iopub.clear_output && msg.header.msg_type === 'clear_output') {
                        callbacks.iopub.clear_output(msg);
                    } else if (callbacks.iopub.output) {
                        switch (msg.header.msg_type) {
                            case 'display_data':
                            case 'execute_result':
                            case 'error':
                                callbacks.iopub.output(msg);
                                break;
                        }
                    }
                }
            };
        }
    }
}
