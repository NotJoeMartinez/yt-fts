import sqlite3

def make_db():
    con = sqlite3.connect('subtitles.db')  
    cur = con.cursor()  

    cur.execute('''
        CREATE TABLE IF NOT EXISTS Channels (
            channel_id TEXT PRIMARY KEY,
            channel_name TEXT NOT NULL,
            channel_url TEXT NOT NULL
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS Videos (
            video_id TEXT PRIMARY KEY,
            video_title TEXT NOT NULL,
            video_url TEXT NOT NULL,
            channel_id TEXT,
            FOREIGN KEY(channel_id) REFERENCES Channels(channel_id)
        );
    ''')

    cur.execute('''
        CREATE TABLE IF NOT EXISTS Subtitles (
            subtitle_id INTEGER PRIMARY KEY AUTOINCREMENT,
            video_id TEXT,
            timestamp TEXT NOT NULL,
            text TEXT NOT NULL,
            FOREIGN KEY(video_id) REFERENCES Videos(video_id)
        );
    ''')

    con.commit()
    con.close()


def add_channel_info(channel_id, channel_name, channel_url):
    con = sqlite3.connect('subtitles.db')  
    cur = con.cursor()  

    cur.execute(f"INSERT INTO Channels VALUES (?, ?, ?)", (channel_id, channel_name, channel_url))
    con.commit()
    con.close()


def add_video(channel_id, vid_id,  vid_title, vid_url):
    con = sqlite3.connect('subtitles.db')  
    cur = con.cursor()  

    cur.execute(f"INSERT INTO Videos VALUES (?, ?, ?, ?)", (vid_id, vid_title, vid_url, channel_id))
    con.commit()
    con.close()


def add_subtitle(vid_id, start_time, text):
    con = sqlite3.connect('subtitles.db')  
    cur = con.cursor()  

    cur.execute(f"INSERT INTO Subtitles (video_id, timestamp, text) VALUES (?, ?, ?)", (vid_id, start_time, text))
    con.commit()
    con.close()



def get_channels():
    con = sqlite3.connect('subtitles.db')  
    cur = con.cursor()  

    cur.execute(f"SELECT * FROM Channels")
    res = cur.fetchall()
    con.close()
    return res


def search_channel(channel_id, text):
    con = sqlite3.connect('subtitles.db')  
    cur = con.cursor()  

    cur.execute(f"SELECT * FROM Subtitles WHERE video_id IN (SELECT video_id FROM Videos WHERE channel_id = ?) AND text LIKE ?", (channel_id, '%'+text+'%'))
    res = cur.fetchall()
    con.close()
    return res


def get_title_from_db(sub_id):
    con = sqlite3.connect('subtitles.db')
    cur = con.cursor()
    cur.execute(f"SELECT video_title FROM Videos WHERE video_id IN (SELECT video_id FROM Subtitles WHERE subtitle_id = ?)", (sub_id,))
    res = cur.fetchone()
    con.close()
    return res
