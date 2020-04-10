# test if it renders in chromium
import asyncio
import pytest
from pathlib import Path
import shutil
import os
import numpy as np

from PIL import Image, ImageDraw
import pyppeteer

artifact_path = Path('artifacts')
artifact_path.mkdir(exist_ok=True)


@pytest.fixture
def voila_notebook(notebook_directory):
    return os.path.join(notebook_directory, 'slider.ipynb')


async def compare(element, name, tolerance=0.01):
    base_dir = Path('tests/notebooks/screenshots/')
    base_dir.mkdir(exist_ok=True)
    test_path = base_dir / f'{name}_testrun.png'
    truth_path = base_dir / f'{name}_truth.png'
    if not truth_path.exists():
        # on initial run, we just save it
        await element.screenshot({'path': str(truth_path)})
    else:
        await element.screenshot({'path': str(test_path)})
        truth = Image.open(truth_path)
        test = Image.open(test_path)
        try:
            diff = None
            assert truth.size == test.size
            delta = np.array(truth)/255. - np.array(test)/255.
            delta_abs = abs(delta)
            delta_rel = delta_abs#/truth
            significant_difference = delta_rel.max() > tolerance
            diff_float = delta_rel > tolerance
            diff_bytes = (diff_float*255).astype(np.uint8)
            diff = Image.frombuffer(truth.mode, truth.size, diff_bytes)

            assert not significant_difference, f'Relative pixel difference > {tolerance}'
        except:  # noqa
            # in case of a failure, we store as much as possible to analyse the failure
            if diff:
                diff.save(artifact_path / f'{name}_diff.png')
                # with alpha, it is difficult to see the difference
                diff.convert('RGB').save(artifact_path / f'{name}_diff_non_alpha.png')
            shutil.copy(test_path, artifact_path)
            shutil.copy(truth_path, artifact_path)
            if diff and diff.getbbox():
                # a visual guide where the difference is
                marked_path = artifact_path / f'{name}_marked.png'
                marked = truth.copy()
                draw = ImageDraw.Draw(marked)
                draw.rectangle(diff.getbbox(), outline='red')
                marked.convert('RGB').save(marked_path)
            raise  # reraises the AssertionError


@pytest.mark.gen_test
async def test_render(http_client, base_url, voila_app):
    options = dict(headless=False, devtools=True) if os.environ.get('VOILA_TEST_DEBUG_VISUAL', False) else {}
    # with headless and gpu enabled, we get slightly different results on the same OS
    # we can enable it if we need to, since we allow for a tolerance
    browser = await pyppeteer.launch(options=options, args=['--font-render-hinting=none', '--disable-gpu'])
    page = await browser.newPage()
    await page.goto(base_url, waitUntil='networkidle2')
    result = await page.evaluate('async () => await widgetManagerPromise')
    # take the slider without the text to avoid font issues
    el = await page.querySelector('.slider-container')
    assert el is not None
    try:
        await compare(el, 'slider', tolerance=0.1)
    except Exception as e:  # noqa
        if os.environ.get('VOILA_TEST_DEBUG_VISUAL', False):
            import traceback
            traceback.print_exc()
            # may want to add --async-test-timeout=60 to pytest arguments
            print("Waiting for 60 second for visual inspection (hit ctrl-c to break)")
            try:
                await asyncio.sleep(60)
            except:  # noqa ignore ctrl-c
                pass
        raise e
    finally:
        await browser.close()
