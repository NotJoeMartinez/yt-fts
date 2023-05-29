CREATE TABLE [Channels] (
   [channel_id] TEXT PRIMARY KEY,
   [channel_name] TEXT NOT NULL,
   [channel_url] TEXT NOT NULL
);
CREATE TABLE [Videos] (
   [video_id] TEXT PRIMARY KEY,
   [video_title] TEXT NOT NULL,
   [video_url] TEXT NOT NULL,
   [channel_id] TEXT REFERENCES [Channels]([channel_id])
);
CREATE TABLE [Subtitles] (
   [subtitle_id] INTEGER PRIMARY KEY,
   [video_id] TEXT REFERENCES [Videos]([video_id]),
   [timestamp] TEXT NOT NULL,
   [text] TEXT NOT NULL
);
CREATE VIRTUAL TABLE [Subtitles_fts] USING FTS5 (
    [text],
    content=[Subtitles]
)
/* Subtitles_fts(text) */;
CREATE TABLE IF NOT EXISTS 'Subtitles_fts_data'(id INTEGER PRIMARY KEY, block BLOB);
CREATE TABLE IF NOT EXISTS 'Subtitles_fts_idx'(segid, term, pgno, PRIMARY KEY(segid, term)) WITHOUT ROWID;
CREATE TABLE IF NOT EXISTS 'Subtitles_fts_docsize'(id INTEGER PRIMARY KEY, sz BLOB);
CREATE TABLE IF NOT EXISTS 'Subtitles_fts_config'(k PRIMARY KEY, v) WITHOUT ROWID;
CREATE TRIGGER [Subtitles_ai] AFTER INSERT ON [Subtitles] BEGIN
  INSERT INTO [Subtitles_fts] (rowid, [text]) VALUES (new.rowid, new.[text]);
END;
CREATE TRIGGER [Subtitles_ad] AFTER DELETE ON [Subtitles] BEGIN
  INSERT INTO [Subtitles_fts] ([Subtitles_fts], rowid, [text]) VALUES('delete', old.rowid, old.[text]);
END;
CREATE TRIGGER [Subtitles_au] AFTER UPDATE ON [Subtitles] BEGIN
  INSERT INTO [Subtitles_fts] ([Subtitles_fts], rowid, [text]) VALUES('delete', old.rowid, old.[text]);
  INSERT INTO [Subtitles_fts] (rowid, [text]) VALUES (new.rowid, new.[text]);
END;
