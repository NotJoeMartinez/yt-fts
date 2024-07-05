import pytest
import sqlite3
import os
import shutil
import subprocess
from click.testing import CliRunner
from yt_fts.yt_fts import download, cli
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
        else:
            print('running tests with existing db')


def test_vsearch(runner, capsys):
    reset_testing_env()

    result = runner.invoke(cli, [
        'vsearch',
        '-c',
        '3',
        'icbm gambit',
    ])

    assert result.exit_code == 0

    print(result.output)
    captured = capsys.readouterr()
    output = captured.out

    assert "Title: Intercontinental Ballistic Missile Gambit (real opening)" in output
    assert "missile attack that will leave your opponent's position in unorganized chaos" in output


if __name__ == "__main__":
    pytest.main([__file__])