import pytest
import sqlite3
import os
import shutil
from click.testing import CliRunner
from yt_fts.yt_fts import download, cli

CONFIG_DIR = os.path.expanduser('~/.config/yt-fts')


@pytest.fixture(scope="session", autouse=True)
def cleanup_after_tests():
    yield
    if os.path.exists(CONFIG_DIR):
        shutil.rmtree(CONFIG_DIR)
    if os.path.exists(f"{CONFIG_DIR}_backup"):
        shutil.move(f"{CONFIG_DIR}_backup", CONFIG_DIR)


@pytest.fixture
def runner():
    return CliRunner()


def reset_testing_env():
    if os.path.exists(CONFIG_DIR):
        if os.environ.get('YT_FTS_TEST_RESET', 'true').lower() == 'true':

            if os.path.exists(CONFIG_DIR):
                if not os.path.exists(f"{CONFIG_DIR}_backup"):
                    shutil.copytree(CONFIG_DIR, f"{CONFIG_DIR}_backup")

            shutil.rmtree(CONFIG_DIR)

        else:
            print('running tests with existing db')

def get_test_db():
    conn = sqlite3.connect(f"{CONFIG_DIR}/subtitles.db")
    curr = conn.cursor()
    return curr


def test_channel_download(runner, capsys):  # Add capsys as a parameter
    reset_testing_env()
    results = runner.invoke(cli, [
        'download',
        '-j',
        '5',
        'https://www.youtube.com/@JCS'
    ])

    assert results.exit_code == 0

    curr = get_test_db()

    # jcs channel id
    channel_id = 'UCYwVxWpjeKFWwu8TML-Te9A'

    res = curr.execute(f"""
            select count(*) from
            Videos where channel_id = '{channel_id}'
    """)
    video_count = res.fetchone()[0]

    res = curr.execute(f"""
        SELECT COUNT(*) as subtitle_count
        FROM Subtitles s
        JOIN Videos v ON s.video_id = v.video_id
        JOIN Channels c ON v.channel_id = c.channel_id
        WHERE c.channel_id = '{channel_id}'
    """)
    subtitle_count = res.fetchone()[0]

    assert video_count == 17, f"Expected 17 videos, but got {video_count}"
    assert subtitle_count >= 21153, f"Expected 21153 subtitles, but got {subtitle_count}"


def test_playlist_download(runner, capsys):
    reset_testing_env()

    print("downloading playlist")
    results = runner.invoke(cli, [
        'download',
        '--playlist',
        '-j',
        '5',
        'https://www.youtube.com/playlist?list=PL5q_lef6zVkaTY_cT1k7qFNF2TidHCe-1'
    ])

    assert results.exit_code == 0

    curr = get_test_db()
    # ycombinator
    channel_id = 'UCxIJaCMEptJjxmmQgGFsnCg'

    res = curr.execute(f"""
            select count(*) 
            from Videos 
            where channel_id = '{channel_id}'
    """)

    video_count = res.fetchone()[0]

    res = curr.execute(f"""
        SELECT COUNT(*) as subtitle_count
        FROM Subtitles s
        JOIN Videos v ON s.video_id = v.video_id
        JOIN Channels c ON v.channel_id = c.channel_id
        WHERE c.channel_id = '{channel_id}'
    """)

    subtitle_count = res.fetchone()[0]

    assert video_count == 21, f"Expected 21 videos, but got {video_count}"
    assert subtitle_count >= 20970, f"Expected 20970 subtitles, but got {subtitle_count}"




if __name__ == "__main__":
    pytest.main([__file__])
