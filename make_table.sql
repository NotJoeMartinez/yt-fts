
CREATE TABLE Channels (
    channel_id TEXT PRIMARY KEY,
    channel_name TEXT NOT NULL,
    channel_url TEXT NOT NULL
);

CREATE TABLE Videos (
    video_id TEXT PRIMARY KEY,
    video_title TEXT NOT NULL,
    video_url TEXT NOT NULL,
    channel_id TEXT,
    FOREIGN KEY(channel_id) REFERENCES Channels(channel_id)
);

CREATE TABLE Subtitles (
    subtitle_id INTEGER PRIMARY KEY AUTOINCREMENT,
    video_id TEXT,
    timestamp TEXT NOT NULL,
    text TEXT NOT NULL,
    FOREIGN KEY(video_id) REFERENCES Videos(video_id)
);
