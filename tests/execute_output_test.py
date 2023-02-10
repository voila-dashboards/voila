import os

import pytest

from voila.execute import executenb

from nbformat import read, NO_CONVERT

from copy import deepcopy


BASE_DIR = os.path.dirname(__file__)
WIDGET_MIME_TYPE_VIEW = 'application/vnd.jupyter.widget-view+json'
WIDGET_MIME_TYPE_STATE = 'application/vnd.jupyter.widget-state+json'


# based on nbconvert.preprocessors.tests.test_execute.TestExecute
# we cannot import it because pytest would then also execute those tests
def normalize_output(output):
    """
    Normalizes outputs for comparison.
    """
    output = dict(output)
    if 'metadata' in output:
        del output['metadata']
    # tracebacks can be different per installation/python version
    if 'traceback' in output:
        del output['traceback']
    if 'application/vnd.jupyter.widget-view+json' in output.get('data', {}):
        output['data']['application/vnd.jupyter.widget-view+json'][
            'model_id'
        ] = '<MODEL_ID>'


def normalize_outputs(outputs):
    for output in outputs:
        normalize_output(output)


@pytest.mark.xfail(reason='TODO: investigate this failing test')
def test_execute_output():
    path = os.path.join(BASE_DIR, 'notebooks/output.ipynb')
    nb = read(path, NO_CONVERT)
    nb_voila = deepcopy(nb)
    """executenb(nb_voila)

    widget_states = nb.metadata.widgets[WIDGET_MIME_TYPE_STATE]['state']
    widget_states_voila = nb_voila.metadata.widgets[WIDGET_MIME_TYPE_STATE][
        'state'
    ]

    for cell_voila, cell in zip(nb_voila.cells, nb.cells):
        for output_voila, output in zip(cell_voila.outputs, cell.outputs):
            if 'data' in output and WIDGET_MIME_TYPE_VIEW in output['data']:
                widget_id = output['data'][WIDGET_MIME_TYPE_VIEW]['model_id']
                widget_id_voila = output_voila['data'][WIDGET_MIME_TYPE_VIEW][
                    'model_id'
                ]
                widget_state = widget_states[widget_id]
                widget_state_voila = widget_states_voila[widget_id_voila]
                # if the widget is an output widget, it has the outputs, which we also check
                assert normalize_outputs(
                    widget_state.state.get('outputs', [])
                ) == normalize_outputs(
                    widget_state_voila.state.get('outputs', [])
                )
            normalize_output(output_voila)
            normalize_output(output)
            assert output_voila == output
"""