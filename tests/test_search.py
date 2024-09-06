import pytest
import sqlite3
import os
import shutil
from click.testing import CliRunner
from yt_fts.yt_fts import download, cli
from testing_utils import fetch_and_unzip_test_db, get_test_db

CONFIG_DIR = os.path.expanduser('~/.config/yt-fts')


@pytest.fixture(scope="session")
def runner():
    return CliRunner()


def reset_testing_env():
    if os.path.exists(CONFIG_DIR):
        if os.environ.get('YT_FTS_TEST_RESET', 'true').lower() == 'true':
            shutil.rmtree(CONFIG_DIR)
            fetch_and_unzip_test_db()
        else:
            print('running tests with existing db')


def test_global_search(runner, capsys):
    result = runner.invoke(cli, [
        'search',
        'guilt'
    ])

    assert result.exit_code == 0

    print(result.output)
    captured = capsys.readouterr()
    output = captured.out

    assert "Y Combinator: The Vault" in output
    assert "JCS - Criminal Psychology" in output
    # assert "Found 16 matches in 9 videos from 2 channels" in output


def test_channel_search(runner, capsys):
    result = runner.invoke(cli, [
        'search',
        '-c',
        '1',
        'criminal'
    ])

    assert result.exit_code == 0

    print(result.output)
    captured = capsys.readouterr()
    output = captured.out

    # assert "Found 11 matches in 7 videos from 1 channel" in output
    assert "JCS - Criminal Psychology" in output
    assert "The Bizarre Case of Stephen McDaniel" in output


if __name__ == "__main__":
    pytest.main([__file__])
