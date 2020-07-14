#############################################################################
# Copyright (c) 2018, Voila Contributors                                    #
# Copyright (c) 2018, QuantStack                                            #
#                                                                           #
# Distributed under the terms of the BSD 3-Clause License.                  #
#                                                                           #
# The full license is in the file LICENSE, distributed with this software.  #
#############################################################################
import logging

from nbconvert.preprocessors import ClearOutputPreprocessor
from nbclient.exceptions import CellExecutionError
from nbclient import NotebookClient

from traitlets import Unicode


def strip_code_cell_warnings(cell):
    """Strip any warning outputs and traceback from a code cell."""
    if cell['cell_type'] != 'code':
        return cell

    outputs = cell['outputs']

    cell['outputs'] = [
        output for output in outputs
        if output['output_type'] != 'stream' or output['name'] != 'stderr'
    ]

    return cell


def should_strip_error(config):
    """Return True if errors should be stripped from the Notebook, False otherwise, depending on the current config."""
    return 'Voila' not in config or 'log_level' not in config['Voila'] or config['Voila']['log_level'] != logging.DEBUG


class VoilaExecutor(NotebookClient):
    """Execute, but respect the output widget behaviour"""
    cell_error_instruction = Unicode(
        'Please run Voila with --debug to see the error message.',
        config=True,
        help=(
            'instruction given to user to debug cell errors'
        )
    )

    cell_timeout_instruction = Unicode(
        'Please run Voila with --VoilaExecutor.interrupt_on_timeout=True to continue executing the rest of the notebook.',
        config=True,
        help=(
            'instruction given to user to continue execution on timeout'
        )
    )

    def __init__(self, nb, km=None, **kwargs):
        super(VoilaExecutor, self).__init__(nb, km=km, **kwargs)

    def execute(self, nb, resources, km=None):
        try:
            result = super(VoilaExecutor, self).execute()
        except CellExecutionError as e:
            self.log.error(e)
            result = (nb, resources)

        # Strip errors and traceback if not in debug mode
        if should_strip_error(self.config):
            self.strip_notebook_errors(nb)

        return result

    async def execute_cell(self, cell, resources, cell_index, store_history=True):
        try:
            result = await super(VoilaExecutor, self).async_execute_cell(cell, cell_index, store_history)
        except TimeoutError as e:
            self.log.error(e)
            self.show_code_cell_timeout(cell)
            raise e
        except CellExecutionError as e:
            self.log.error(e)
            result = cell

        # Strip errors and traceback if not in debug mode
        if should_strip_error(self.config):
            strip_code_cell_warnings(cell)
            self.strip_code_cell_errors(cell)

        return result

    def strip_notebook_errors(self, nb):
        """Strip error messages and traceback from a Notebook."""
        cells = nb['cells']

        code_cells = [cell for cell in cells if cell['cell_type'] == 'code']

        for cell in code_cells:
            strip_code_cell_warnings(cell)
            self.strip_code_cell_errors(cell)

        return nb

    def strip_code_cell_errors(self, cell):
        """Strip any error outputs and traceback from a code cell."""
        # There is no 'outputs' key for markdown cells
        if cell['cell_type'] != 'code':
            return cell

        outputs = cell['outputs']

        error_outputs = [output for output in outputs if output['output_type'] == 'error']

        error_message = f'There was an error when executing cell [{cell["execution_count"]}]. {self.cell_error_instruction}'

        for output in error_outputs:
            output['ename'] = 'ExecutionError'
            output['evalue'] = 'Execution error'
            output['traceback'] = [error_message]

        return cell

    def show_code_cell_timeout(self, cell):
        """Show a timeout error output in a code cell."""

        timeout_message = f'Cell execution timed out, aborting notebook execution. {self.cell_timeout_instruction}'

        output = {'output_type': 'error',
                  'ename': 'TimeoutError',
                  'evalue': 'Timeout error',
                  'traceback': [timeout_message]}

        cell['outputs'] = [output]


def executenb(nb, cwd=None, km=None, **kwargs):
    resources = {}
    if cwd is not None:
        resources['metadata'] = {'path': cwd}  # pragma: no cover
    # Clear any stale output, in case of exception
    nb, resources = ClearOutputPreprocessor().preprocess(nb, resources)
    executor = VoilaExecutor(nb, km=km, **kwargs)
    return executor.execute(nb, resources, km=km)
