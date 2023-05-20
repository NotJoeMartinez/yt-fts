
# yt-fts
Search all of a YouTube channel from the command line
- [Blog Post](https://notjoemartinez.com/blog/youtube_full_text_search/)

### Usage 
```
Usage: yt_fts.py [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  delete    delete [channel id]
  download  download [channel url]
  list      Lists channels
  search    search [channel id] [search text]
```

### `download`
Will download all of a channels vtt files into your database 

### `list`
Will list all of your downloaded channels 

### `search`
Will search a channel for text based off the channel id you give it and 
will print a url to that point in the video
```bash
python yt_fts.py search [channel_id] "text you want to find"
```

### `Delete` 
Will delete a channel from your database 
```bash
python yt_fts.py delete [channel_id]
```