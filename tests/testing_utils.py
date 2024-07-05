import os
import sqlite3
import tempfile
import shutil
import requests
from zipfile import ZipFile

CONFIG_DIR = os.path.expanduser('~/.config/yt-fts')

def fetch_and_unzip_test_db():
    url = "https://yt-fts-testdb-server.notjoemartinez.workers.dev/yt-fts/test_dbs/2024-07-04.zip"

    # Create a temporary directory
    with tempfile.TemporaryDirectory() as temp_dir:
        # Download the zip file
        response = requests.get(url)
        zip_path = os.path.join(temp_dir, "downloaded.zip")

        with open(zip_path, "wb") as zip_file:
            zip_file.write(response.content)

        # Unzip the file
        extract_dir = os.path.join(temp_dir, "extracted")
        with ZipFile(zip_path, "r") as zip_ref:
            zip_ref.extractall(extract_dir)

        # Move the yt-fts directory to ~/.config/
        source_dir = os.path.join(extract_dir, "yt-fts")
        dest_dir = os.path.expanduser("~/.config/yt-fts")

        if os.path.exists(dest_dir):
            shutil.rmtree(dest_dir)

        shutil.copytree(source_dir, dest_dir, symlinks=True, ignore=None)

    # print(f"The 'yt-fts' directory has been copied to {dest_dir}")
    # print("Contents of the copied directory:")
    # for root, dirs, files in os.walk(dest_dir):
    #     level = root.replace(dest_dir, '').count(os.sep)
    #     indent = ' ' * 4 * level
    #     print(f"{indent}{os.path.basename(root)}/")
    #     sub_indent = ' ' * 4 * (level + 1)
    #     for f in files:
    #         print(f"{sub_indent}{f}")



def get_test_db():
    conn = sqlite3.connect(f"{CONFIG_DIR}/subtitles.db")
    curr = conn.cursor()
    return curr
