import asyncio
import os

import pytest
import pyppeteer


@pytest.fixture(params=[True, False])
def show_tracebacks(request):
    return request.param


@pytest.fixture
def voila_args(notebook_directory, voila_args_extra, show_tracebacks):
    return ['--VoilaTest.root_dir=%r' % notebook_directory, f'--VoilaConfiguration.show_tracebacks={show_tracebacks}'] + voila_args_extra


async def test_syntax_error(http_server_client, syntax_error_notebook_url, show_tracebacks):
    response = await http_server_client.fetch(syntax_error_notebook_url)
    assert response.code == 200
    output = response.body.decode('utf-8')
    if show_tracebacks:
        assert 'this is a syntax error' in output, 'should show the "code"'
        assert 'SyntaxError' in output and 'invalid syntax' in output, "should show the error"
    else:
        assert 'There was an error when executing cell' in output
        assert 'This should not be executed' not in output


async def test_output_widget_traceback(http_server_client, exception_runtime_notebook_url, show_tracebacks):
    options = dict(headless=False, devtools=True) if os.environ.get('VOILA_TEST_DEBUG_VISUAL', False) else {}
    # with headless and gpu enabled, we get slightly different results on the same OS
    # we can enable it if we need to, since we allow for a tolerance
    launcher = pyppeteer.launcher.Launcher(options=options, autoClose=False, args=['--font-render-hinting=none', '--disable-gpu'])
    browser = await launcher.launch()
    page = await browser.newPage()
    try:
        await page.goto(http_server_client.get_url(exception_runtime_notebook_url), waitUntil='networkidle2')
        await page.evaluate('async () => await window.VoilaDebug.widgetManagerPromise')
        await page.evaluate('async () => await window.VoilaDebug.waitForAllViews()')
        await page.evaluate("document.querySelector('.button2').click()")
        for i in range(20):
            await asyncio.sleep(0.05)
            output_text = await page.evaluate("document.querySelector('.output_exception').innerText")
            if output_text:
                break
        else:
            assert False, f"Never received output"
        if show_tracebacks:
            assert 'this happens after the notebook is executed' in output_text
        else:
            assert 'this happens after the notebook is executed' not in output_text
    except Exception as e:  # noqa
        if os.environ.get('VOILA_TEST_DEBUG_VISUAL', False):
            import traceback
            traceback.print_exc()
            # may want to add --async-test-timeout=60 to pytest arguments
            print("Waiting for 60 second for visual inspection (hit ctrl-c to break)")
            import sys
            sys.stdout.flush()
            sys.stderr.flush()
            try:
                await asyncio.sleep(60)
            except:  # noqa ignore ctrl-c
                pass
        raise e
    finally:
        await browser.close()
        await launcher.killChrome()
