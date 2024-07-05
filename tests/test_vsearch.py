import pytest
import requests
import sqlite3
import os
import shutil
import zipfile
import sys
from io import BytesIO
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
            fetch_and_unzip_test_db()
        else:
            print('running tests with existing db')


def fetch_and_unzip_test_db():
    url = "https://yt-fts-testdb-server.notjoemartinez.workers.dev/yt-fts/test_dbs/2024-07-04.zip"
    response = requests.get(url)
    if response.status_code == 200:
        with zipfile.ZipFile(BytesIO(response.content)) as zip_ref:
            for file in zip_ref.namelist():
                if file.startswith('2024-07-04/'):
                    extracted_path = zip_ref.extract(file, CONFIG_DIR)
                    print("extracted path: ", extracted_path)

                    new_path = os.path.join(CONFIG_DIR, os.path.relpath(extracted_path, os.path.join(CONFIG_DIR, '2024-07-04')))
                    print(f"new_path: {new_path}")
                    os.makedirs(os.path.dirname(new_path), exist_ok=True)

                    if os.path.exists(new_path):
                        if os.path.isdir(new_path):
                            for item in os.listdir(extracted_path):
                                s = os.path.join(extracted_path, item)
                                d = os.path.join(new_path, item)
                                if os.path.isdir(s):
                                    shutil.copytree(s, d, dirs_exist_ok=True)
                                else:
                                    shutil.copy2(s, d)
                        else:
                            os.remove(new_path)
                            shutil.move(extracted_path, new_path)
                    else:
                        shutil.move(extracted_path, new_path)

            shutil.rmtree(os.path.join(CONFIG_DIR, '2024-07-04'), ignore_errors=True)

    else:
        raise Exception(f"Failed to download the zip file. Status code: {response.status_code}")

    print(f"Successfully extracted")


def get_test_db():
    conn = sqlite3.connect(f"{CONFIG_DIR}/subtitles.db")
    curr = conn.cursor()
    return curr


def test_vsearch(runner, capsys):
    reset_testing_env()

    result = runner.invoke(cli, [
        'vsearch',
        '-c',
        '3',
        'icbm gambit',
    ])

    print(result.output)
    captured = capsys.readouterr()
    output = captured.out

    assert "Title: Intercontinental Ballistic Missile Gambit (real opening)" in output
    assert "missile attack that will leave your opponent's position in unorganized chaos" in output


if __name__ == "__main__":
    pytest.main([__file__])