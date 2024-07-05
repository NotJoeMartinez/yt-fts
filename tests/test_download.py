import pytest
import sqlite3
import os
import shutil
from click.testing import CliRunner
from yt_fts.yt_fts import download, cli

CONFIG_DIR = os.path.expanduser('~/.config/yt-fts')


@pytest.fixture
def runner():
    return CliRunner()


def reset_testing_env():
    if os.path.exists(CONFIG_DIR):
        if os.environ.get('YT_FTS_TEST_RESET', 'true').lower() == 'true':
            shutil.rmtree(CONFIG_DIR)
        else:
            print('running tests with existing db')


def test_successful_download(runner):
    reset_testing_env()
    runner.invoke(cli, ['download', 'https://www.youtube.com/@JCS'])
    conn = sqlite3.connect(f"{CONFIG_DIR}/subtitles.db")
    curr = conn.cursor()

    query = '''
        select count(*) from
        Videos where channel_id = 'UCYwVxWpjeKFWwu8TML-Te9A';
    '''
    res = curr.execute(query)
    res = res.fetchone()

    print(res)
    assert res[0] > 0, f"Expected at least one video, but got {res[0]}"


if __name__ == "__main__":
    pytest.main([__file__])

