import sqlite3

from sqlite_utils import Database
from tabulate import tabulate

from yt_fts.utils import show_message

db_name = 'subtitles.db'

def make_db():
    db = Database(db_name)

    db["Channels"].create({
            "channel_id": str,
            "channel_name": str,
            "channel_url": str,
        }, 
        pk="channel_id", 
        not_null={"channel_name", "channel_url"}, 
        if_not_exists=True
    )

    db["Videos"].create({
            "video_id": str,
            "video_title": str,
            "video_url": str,
            "channel_id": str
        }, 
        pk="video_id", 
        not_null={"video_title", "video_url"}, 
        if_not_exists=True, 
        foreign_keys=[
            ("channel_id", "Channels")
        ]
    )

    db["Subtitles"].create(
        {
            "subtitle_id": int,
            "video_id": str,
            "timestamp": str,
            "text": str
        }, 
        pk="subtitle_id", 
        not_null={"timestamp", "text"}, 
        if_not_exists=True, 
        foreign_keys=[
            ("video_id", "Videos")
        ]
    ).enable_fts(
        ["text"], 
        create_triggers=True, 
        replace=True
    )


def add_channel_info(channel_id, channel_name, channel_url):
    db = Database(db_name)

    db["Channels"].insert({
        "channel_id": channel_id,
        "channel_name": channel_name,
        "channel_url": channel_url
    })


def add_video(channel_id, video_id,  video_title, video_url):
    db = Database(db_name)

    db["Videos"].insert({
        "video_id": video_id,
        "video_title": video_title,
        "video_url": video_url,
        "channel_id": channel_id
    })


def add_subtitle(video_id, start_time, text):
    db = Database(db_name)

    db["Subtitles"].insert({
        "video_id": video_id,
        "timestamp": start_time,
        "text": text
    })


def get_channels():
    db = Database(db_name)

    # return db.execute("SELECT * FROM Channels").fetchall()
    return db.execute("SELECT ROWID, channel_name, channel_url FROM Channels").fetchall()


def search_channel(channel_id, text):
    db = Database(db_name)

    # cur = db.execute(f"SELECT video_id FROM Videos WHERE channel_id = ?", [channel_id]) 

    return list(db["Subtitles"].search(text, where=f"video_id IN (SELECT video_id FROM Videos WHERE channel_id = '{channel_id}')"))


def get_title_from_db(video_id):
    db = Database(db_name)

    return db.execute(f"SELECT video_title FROM Videos WHERE video_id = ?", [video_id]).fetchone()[0]


def search_all(text):
    db = Database(db_name)

    return list(db["Subtitles"].search(text))


def get_channel_name_from_id(channel_id):
    db = Database(db_name)

    return db.execute(f"SELECT channel_name FROM Channels WHERE channel_id = ?", [channel_id]).fetchone()[0]

def get_channel_name_from_video_id(video_id):
    db = Database(db_name)

    return db.execute(f"SELECT channel_name FROM Channels WHERE channel_id = (SELECT channel_id FROM Videos WHERE video_id = ?)", [video_id]).fetchone()[0]

def delete_channel(channel_id):
    conn = sqlite3.connect(db_name)
    cur = conn.cursor()

    cur.execute("DELETE FROM Channels WHERE channel_id = ?", (channel_id,))
    cur.execute("DELETE FROM Subtitles WHERE video_id IN (SELECT video_id FROM Videos WHERE channel_id = ?)", (channel_id,))
    cur.execute("DELETE FROM Videos WHERE channel_id = ?", (channel_id,))

    conn.commit()
    conn.close()


def get_channel_id_from_rowid(rowid):
    db = Database(db_name)

    res = db.execute(f"SELECT channel_id FROM Channels WHERE ROWID = ?", [rowid]).fetchone()

    if res is None:
        return None
    else:
        return res[0]


def get_channel_id_from_name(channel_name):
    db = Database(db_name)

    res = db.execute(f"SELECT channel_id FROM Channels WHERE channel_name = ?", [channel_name]).fetchall()

    if len(res) > 1:
        channels = db.execute(f"SELECT ROWID, channel_name, channel_url FROM Channels WHERE channel_name = ?", [channel_name]).fetchall()
        print(tabulate(channels, headers=["id", "channel_name", "channel_url"]))
        print("")
        show_message("multiple_channels_found")
        exit()
    if len(res) == 0:
        return None
    else:
        return res[0][0]