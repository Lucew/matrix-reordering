# we use this nice article by
# https://alexandra-zaharia.github.io/posts/kill-subprocess-and-its-children-on-timeout-python/
# WARNING: This only works on LINUX platforms.

import os
import subprocess
import multiprocessing as mp
import argparse
import functools
import math

from tqdm import tqdm
import psutil
from glob import glob


def compute_process_timeout(method_timeout_s: int, method_number: int, repetition_number: int):
    return math.ceil((method_timeout_s*method_number*repetition_number)*1.1)


def run_calculator(file_path: str, method_timeout_s: int, method_number: int, repetition_number: int):

    # check whether we are on a posix system
    if os.name != 'posix':
        raise EnvironmentError('This program can only be run on linux machines!')

    # get the folder and the filename
    folder = os.path.dirname(file_path)
    filename = os.path.basename(file_path)

    # create the command we want to run
    cmd = ['Rscript', 'Evaluate_Reorderings.R', folder, str(method_timeout_s), str(repetition_number),
           str(method_number), filename]

    # create the file we want to write the output in
    process_timeout = compute_process_timeout(method_timeout_s, method_number, repetition_number)
    with open(os.path.join(folder, f'{filename}.output_file'), 'w') as filet:

        # start running the process (multiprocessing can't time out, therefore going this way)
        proc = subprocess.Popen(cmd, start_new_session=True, stderr=filet, stdout=filet)

        # put a timeout on the process
        try:
            proc.wait(timeout=process_timeout)
        # check whether we reached a timeout and kill the process with all its children
        except subprocess.TimeoutExpired:
            print(f'\n\n\nTimeout for {cmd} ({process_timeout}s) expired', file=filet)
            print('Terminating the whole process group...', file=filet)

            # https://gist.github.com/jizhilong/6687481?permalink_comment_id=3057122#gistcomment-3057122
            for child in psutil.Process(proc.pid).children(recursive=True):
                child.kill()
            proc.kill()


def seconds2str(n: int):

    # get the days first
    days, n = divmod(n, 24 * 3600)

    # then compute the hours
    hours, n = divmod(n, 3600)

    # get the minutes and seconds
    minutes, seconds = divmod(n, 60)

    return f"{days} days, {hours:02d}:{minutes:02d}:{seconds:02d}"


def main(path: str, method_timeout_s: int, method_number: int, repetition_number: int, workers: int = None):

    # find all folders that start with csv_transformed
    target_path = os.path.join(path, 'csv_transformed_*')
    folders = glob(target_path)
    files = [ele for folder in folders for ele in glob(os.path.join(folder, '*.csv'))]

    # check whether the folders exist
    if len(files) == 0 or len(files) == 0:
        raise ValueError(f'No folders found in: {target_path}')
    else:
        print(f'Found {len(files)} files in the following folders: {folders}')

    # set the number of workers
    if workers is None:
        workers = mp.cpu_count()//2
    if workers > mp.cpu_count():
        raise ValueError(f'We can not use more workers than cores. You defined [{workers}], we have {mp.cpu_count()}.')

    # calculate the approximate duration of the computation with timeouts for perfect parallelization
    process_time = compute_process_timeout(method_timeout_s, method_number, repetition_number)
    estimated_duration = seconds2str(int(process_time * len(files) / workers))
    print(f'With perfect parallelization the estimated duration for is: {estimated_duration}. '
          f'Each individual process has: {seconds2str(process_time)}.')

    # now make the multiprocessing over all the metrics
    spi_computing = functools.partial(run_calculator, method_timeout_s=method_timeout_s, method_number=method_number,
                                      repetition_number=repetition_number)
    with mp.Pool(workers) as pool:

        # capture the keyboard interrupt to kill all child processes
        try:
            # do this to have a progress bar
            result_iterator = tqdm(pool.imap_unordered(spi_computing, files),
                                   desc=f'Computing Reorderings ({seconds2str(process_time)})', total=len(files))
            for _ in result_iterator:
                pass
        except KeyboardInterrupt as er:

            # get the currently running process and kill all its children
            proc = psutil.Process(os.getpid())
            for child in proc.children(recursive=True):
                child.kill()

            # reraise the keyboard interrupt
            raise er


def check_bool(inputed: str):
    if inputed.lower() not in ['true', 'false']:
        raise ValueError(f'We only accept true/false you specified: [{inputed}].')
    return inputed.lower() == 'true'


if __name__ == '__main__':
    _parser = argparse.ArgumentParser()
    _parser.add_argument('-p', '--path', type=str, default=os.path.join(os.getcwd(), 'data'))
    _parser.add_argument('-mt', '--method_timeout_s', type=int, default=300)
    _parser.add_argument('-mn', '--method_number', type=int, default=42)
    _parser.add_argument('-rs', '--repetitions', type=int, default=100)
    _parser.add_argument('-w', '--workers', type=int, default=None)
    _args = _parser.parse_args()
    main(_args.path, _args.method_timeout_s, _args.method_number, _args.repetitions, _args.workers)
