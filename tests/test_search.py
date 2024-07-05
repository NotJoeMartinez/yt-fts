import pytest
import sqlite3
import os
import shutil
from click.testing import CliRunner
from yt_fts.yt_fts import download, cli

CONFIG_DIR = os.path.expanduser('~/.config/yt-fts')

@pytest.fixture(scope="session")
def runner():
    return CliRunner()

def reset_testing_env():
    if os.path.exists(CONFIG_DIR):
        if os.environ.get('YT_FTS_TEST_RESET', 'true').lower() == 'true':
            shutil.rmtree(CONFIG_DIR)
        else:
            print('running tests with existing db')

def get_test_db():
    conn = sqlite3.connect(f"{CONFIG_DIR}/subtitles.db")
    curr = conn.cursor()
    return curr

@pytest.fixture(scope="session", autouse=True)
@pytest.mark.order(1)
def setup_environment(runner):
    reset_testing_env()
    runner.invoke(cli, [
        'download',
        '-j',
        '5',
        'https://www.youtube.com/@JCS'
    ])
    runner.invoke(cli, [
        'download',
        '--playlist',
        '-j',
        '5',
        'https://www.youtube.com/playlist?list=PL5q_lef6zVkaTY_cT1k7qFNF2TidHCe-1'
    ])

@pytest.mark.order(2)
def test_global_search(runner, capsys):
    result = runner.invoke(cli, [
        'search',
        'guilt'
    ])

    print(result.output)
    captured = capsys.readouterr()
    output = captured.out

    assert "Y Combinator: The Vault" in output
    assert "JCS - Criminal Psychology" in output
    assert "Found 16 matches in 9 videos from 2 channels" in output


@pytest.mark.order(3)
def test_channel_search(runner, capsys):
    result = runner.invoke(cli, [
        'search',
        '-c',
        '1',
        'criminal'
    ])

    print(result.output)
    captured = capsys.readouterr()
    output = captured.out

    assert "Found 11 matches in 7 videos from 1 channel" in output
    assert "JCS - Criminal Psychology" in output
    assert "The Bizarre Case of Stephen McDaniel" in output


if __name__ == "__main__":
    pytest.main([__file__, "--order-scope=module"])