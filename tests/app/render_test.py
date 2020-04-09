# test if it renders in chromium
import asyncio
import pytest
from pathlib import Path
import shutil
import os

from PIL import Image, ImageDraw, ImageChops
import pyppeteer

artifact_path = Path('artifacts')
artifact_path.mkdir(exist_ok=True)


async def compare(element, name):
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
        diff = ImageChops.difference(truth, test)
        try:
            assert truth.size == test.size
            assert not diff.getbbox(), 'Visual difference'
        except:  # noqa
            diff_path = artifact_path / f'{name}_diff.png'
            diff.convert('RGB').save(diff_path)
            shutil.copy(test_path, artifact_path)
            shutil.copy(truth_path, artifact_path)
            if diff.getbbox():
                marked_path = artifact_path / f'{name}_marked.png'
                marked = truth.copy()
                draw = ImageDraw.Draw(marked)
                draw.rectangle(diff.getbbox(), outline='red')
                marked.convert('RGB').save(marked_path)
            raise


@pytest.mark.gen_test
async def test_render(http_client, base_url, voila_app):
    options = dict(headless=False, devtools=True) if os.environ.get('VOILA_TEST_DEBUG_VISUAL', False) else {}
    browser = await pyppeteer.launch(options=options)
    page = await browser.newPage()
    await page.goto(base_url)
    el = await page.querySelector('.jp-OutputArea-output')
    try:
        await compare(el, 'print')
    except:  # noqa
        if os.environ.get('VOILA_TEST_DEBUG_VISUAL', False):
            # may want to add --async-test-timeout=60 to pytest arguments
            print("Waiting for 60 second for visual inspection (hit ctrl-c to break)")
            await asyncio.sleep(60)
    finally:
        await browser.close()
