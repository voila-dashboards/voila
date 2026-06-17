import subprocess
import threading
import time
import os
import shutil
import sys
import nbformat


def get_lines(std_pipe):
    '''Generator that yields lines from a standard pipe as there are printed.'''
    for line in iter(std_pipe.readline, ''):
        yield line
    std_pipe.close()


def get_cell(seconds):
    '''Return a cell that waits for seconds and logs its execution time (from the end of the previous cell).'''
    cell = ["time.sleep(" + str(seconds) + ")\n",
            "t1 = time.time()\n",
            "log += str(t1 - t0) + '\\n'\n",
            "t0 = t1"]
    return cell


def get_ipynb(cell_nb, sleep_per_cell, result_dir):
    '''Return a notebook which consists of all the sleeping cells and the creation of a log file.'''
    cells = []
    cell = ["import uuid\n",
            "import time\n",
            "fname = str(uuid.uuid4()) + '.log'\n",
            "log = ''\n",
            "t0 = time.time()"]
    cells.append(cell)
    for i in range(cell_nb):
        cell = get_cell(sleep_per_cell)
        cells.append(cell)
    cell = ["with open('" + result_dir + "/' + fname, 'w') as f:\n",
            "    f.write(log)"]
    cells.append(cell)
    ipynb = nbformat.v4.new_notebook(
        metadata={
            'kernelspec': {
                'display_name': 'Python 3',
                'language': 'python',
                'name': 'python3'
            }
        },
        cells=[nbformat.v4.new_code_cell(cell) for cell in cells],
    )
    return ipynb


def test_performance(sleep_per_cell=0.1, cell_nb=100, kernel_nb=10, max_meantime_per_cell=0.5, ipynb_path='tests/notebooks/sleep.ipynb'):
    '''Test for Voila serving several clients concurrently.
    Several clients connect to the Voila server URL at the same time, and each one gets a dedicated kernel.
    The served notebook consists of a number of cells that just wait for some time and log their execution
    time (from the end of the previous cell). At the end of the notebook, the results are written to a unique
    file.
    This allows for testing the performance of serving all the cells concurrently when all the clients are
    requesting them at the same time. Ideally, the time needed to serve a cell should be close to the cell
    sleeping time. When all clients receive the entire notebook, we kill them as well as the Voila server
    (there is a timeout to check that the clients don't wait too long). Then we compute the cell execution
    mean time. It is an error if it is much greater than the ideal value (sleep_per_cell), and we allow for
    it to be <= max_meantime_per_cell.

    Keyword arguments:
    sleep_per_cell -- number of seconds a cell waits for (default 0.1)
    cell_nb -- number of waiting cells in the notebook (default 100)
    kernel_nb -- number of kernels to launch in parallel (default 10)
    max_meantime_per_cell -- maximum tolerated mean execution time per cell (default 0.5)
    ipynb_path -- path to the saved notebook (default 'tests/notebooks/sleep.ipynb')
    '''

    ipynb_dname, ipynb_fname = os.path.split(ipynb_path)
    os.chdir(ipynb_dname)
    result_dir = ipynb_fname[:-6]

    if os.path.exists(result_dir):
        shutil.rmtree(result_dir)
    os.makedirs(result_dir)

    # generate notebook
    ipynb = get_ipynb(cell_nb, sleep_per_cell, result_dir)
    with open(ipynb_fname, 'w') as f:
        nbformat.write(ipynb, f)

    # launch Voila
    voila = subprocess.Popen(('voila --no-browser ' + ipynb_fname).split(), stderr=subprocess.PIPE, universal_newlines=True)

    # wait until server is ready
    for line in get_lines(voila.stderr):
        print(line, end='')
        if line.startswith('http://'):
            break

    # launch clients
    clients = [subprocess.Popen('curl http://127.0.0.1:8866 --output /dev/null --silent'.split()) for i in range(kernel_nb)]

    # wait until all kernels have started
    kernel_i = 0
    for line in get_lines(voila.stderr):
        print(line, end='')
        if 'Kernel started' in line:
            kernel_i += 1
            if kernel_i == kernel_nb:
                # continue printing Voila's stderr in the background
                def target():
                    for line in get_lines(voila.stderr):
                        print(line, end='')
                threading.Thread(target=target).start()
                break

    # wait for all notebooks to execute
    t0 = time.time()
    done = False
    timeout = False
    timeout_time = 2 * max_meantime_per_cell * cell_nb
    while not done:
        time.sleep(1)
        done = True
        for client in clients:
            if client.poll() is None:
                done = False
        if not done:
            if time.time() - t0 > timeout_time:
                done = True
                timeout = True

    # stop Voila and all clients
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
    print('Mean time per cell', meantime_per_cell, end='')
    if meantime_per_cell > max_meantime_per_cell:
        print(' >', sleep_per_cell, '(maximum tolerated is', max_meantime_per_cell, ')')
        sys.exit(1)
    else:
        print(", should ideally be", sleep_per_cell, "but it's close enough!")


if __name__ == '__main__':
    test_performance()
