import subprocess
import time
import os
import shutil
import sys


def get_cell(seconds):
    cell = ', { "cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], ' \
           '"source": [ "time.sleep(' + str(seconds) + ')\\n", "t1 = time.time()\\n", "log += ' \
           'str(t1 - t0) + \'\\\\n\'\\n", "t0 = t1" ] }'
    return cell


def get_ipynb(cell_nb, sleep_per_cell, result_dir):
    ipynb = '{ "cells": [ { "cell_type": "code", "execution_count": null, "metadata": {}, "outputs"' \
            ': [], "source": [ "import uuid\\n", "import time\\n", "fname = str(uuid.uuid4()) + \'' \
            '.log\'\\n", "log = \'\'\\n", "t0 = time.time()" ] }'
    for i in range(cell_nb):
        cell = get_cell(sleep_per_cell)
        ipynb += cell
    ipynb += ', { "cell_type": "code", "execution_count": null, "metadata": {}, "outputs": [], ' \
             '"source": [ "with open(\'' + result_dir + '/\' + fname, \'w\') as f:\\n", "    ' \
             'f.write(log)" ] }'
    ipynb += ' ], "metadata": { "kernelspec": { "display_name": "Python 3", "language": "python", ' \
             '"name": "python3" }, "language_info": { "codemirror_mode": { "name": "ipython", ' \
             '"version": 3 }, "file_extension": ".py", "mimetype": "text/x-python", "name": "python"' \
             ', "nbconvert_exporter": "python", "pygments_lexer": "ipython3", "version": "3.8.1" } }' \
             ', "nbformat": 4, "nbformat_minor": 4 }'
    return ipynb


def test_performance():
    sleep_per_cell = 0.1  # each cell sleeps for that amount of seconds
    cell_nb = 100  # each notebook consists of so many cells
    client_nb = 10  # number of clients (kernels) launched in parallel
    ipynb_path = 'tests/notebooks/sleep.ipynb'  # generated notebook, results are stored in the directory without ".ipynb"

    ipynb_dname, ipynb_fname = os.path.split(ipynb_path)
    os.chdir(ipynb_dname)
    result_dir = ipynb_fname[:-6]

    if os.path.exists(result_dir):
        shutil.rmtree(result_dir)
    os.makedirs(result_dir)

    ipynb = get_ipynb(cell_nb, sleep_per_cell, result_dir)

    # generate notebook
    with open(ipynb_fname, 'w') as f:
        f.write(ipynb)

    # launch voila
    voila = subprocess.Popen(('voila --no-browser ' + ipynb_fname).split())
    time.sleep(1)

    # launch clients
    clients = [subprocess.Popen('wget -O/dev/null -q http://localhost:8866'.split()) for i in range(client_nb)]

    # wait for all notebooks to execute
    t0 = time.time()
    done = False
    timeout = False
    i = 0
    exec_time = cell_nb * sleep_per_cell  # notebook execution time
    launch_time = client_nb * 0.5  # kernel takes about 0.5s to launch
    # min_time = launch_time + exec_time  # theoretical time for all notebooks to execute
    timeout_time = launch_time + 2 * exec_time  # timeout allows slow machines to finish
    while not done:
        time.sleep(1)
        done = True
        i += 1
        # print(i, '/', min_time)
        for client in clients:
            if client.poll() is None:
                done = False
        if not done:
            if time.time() - t0 > timeout_time:
                done = True
                timeout = True

    # stop voila and all clients
    voila.kill()
    [client.kill() for client in clients]

    if timeout:
        raise TimeoutError

    # analyze data
    fnames = os.listdir(result_dir)
    data = []
    for fname in fnames:
        with open(result_dir + '/' + fname) as f:
            data += [float(d) for d in f.read().split()]

    meantime_per_cell = sum(data) / len(data)
    exceed_pct = 50  # allowing for time budget exceedance (%)
    maxtime_per_cell = sleep_per_cell * (exceed_pct / 100 + 1)
    if meantime_per_cell > maxtime_per_cell:
        print('Mean time per cell', meantime_per_cell, '>', sleep_per_cell, '(with', exceed_pct, '% margin)')
        sys.exit(1)
