import pytest
import csv
import os
import shutil
import subprocess
from click.testing import CliRunner
from yt_fts.yt_fts import cli
from testing_utils import fetch_and_unzip_test_db

CONFIG_DIR = os.path.expanduser('~/.config/yt-fts')

@pytest.fixture
def runner():
    return CliRunner()


def reset_testing_env():
    if os.path.exists(CONFIG_DIR):
        if os.environ.get('YT_FTS_TEST_RESET', 'true').lower() == 'true':
            shutil.rmtree(CONFIG_DIR)
            fetch_and_unzip_test_db()
            subprocess.run('rm *.csv', shell=True)

        else:
            print('running tests with existing db')


def test_export_search(runner, capsys):
    reset_testing_env()

    result = runner.invoke(cli, [
        'search',
        '-c',
        '1',
        'criminal',
        '-e'
    ])

    assert result.exit_code == 0
    
    # list of files in the current directory
    output_files = os.listdir()

    # if the file starts with channel_UCYwVxWpjeKFWwu8TML-Te9A 
    # then it's the exported file
    exported_file = None
    for file in output_files:
        if file.startswith('channel_UCYwVxWpjeKFWwu8TML-Te9A'):
            exported_file = file

    assert exported_file is not None, 'Exported file not found'

    with open(exported_file, 'r') as f:
        reader = csv.reader(f)
        lines = list(reader)
        assert len(lines) >= 12, 'Exported file has less than 12 lines'

    # clean up
    subprocess.run('rm *.csv', shell=True)



def test_export_vsearch(runner, capsys):
    reset_testing_env()

    result = runner.invoke(cli, [
        'vsearch',
        '-c',
        '3',
        'icmb gambit',
        '-e'
    ])

    assert result.exit_code == 0

    output_files = os.listdir()

    exported_file = None
    for file in output_files:
        if file.startswith('channel_UCO2QPmnJFjdvJ6ch-pe27dQ'):
            exported_file = file
    assert exported_file is not None, 'vsearch exported file not found'

    with open(exported_file, 'r') as f:
        reader = csv.reader(f)
        lines = list(reader)
        assert len(lines) >= 11, 'vsearch exported file has less than 11 lines' 
    
    subprocess.run('rm *.csv', shell=True)


def test_export_search_all(runner, capsys):
    reset_testing_env()

    result = runner.invoke(cli, [
        'search',
        'guilt',
        '-e',
    ])

    assert result.exit_code == 0

    output_files = os.listdir()

    exported_file = None
    for file in output_files:
        if file.startswith('all_'):
            exported_file = file
    assert exported_file is not None, 'Exported file not found'

    with open(exported_file, 'r') as f:
        reader = csv.reader(f)
        lines = list(reader)
        assert len(lines) >= 17, 'Exported file has less than 17 lines'

    subprocess.run('rm *.csv', shell=True)


if __name__ == "__main__":
    pytest.main([__file__])