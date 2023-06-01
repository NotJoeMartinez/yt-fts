
# yt-fts 
`yt-fts` is a simple python script that uses yt-dlp to scrape all of a youtube channels subtitles
and load them into an sqlite database that is searchable from the command line. It allows you to
query a channel for specific key word or phrase and will generate time stamped youtube urls to
the video containing the keyword. 

- [Blog Post](https://notjoemartinez.com/blog/youtube_full_text_search/)

## Installation 

**pip**
```bash
pip install yt-fts
```

**from source**
```bash
git clone https://github.com/NotJoeMartinez/yt-fts
python3 -m venv .env
source .env/bin/activate
pip install -r requirements.txt
python3 -m yt-fts
```

## Dependencies 
This project requires [yt-dlp](https://github.com/yt-dlp/yt-dlp) installed globally. Platform specific installation instructions are available on the [yt-dlp wiki](https://github.com/yt-dlp/yt-dlp/wiki/Installation). 

**pip**
```bash
python3 -m pip install -U yt-dlp
```
**MacOS/Homebrew**
```bash
brew install yt-dlp
```
**Windows/winget**
```bash
winget install yt-dlp
```

## Usage 
```
Usage: yt-fts [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  delete    delete [channel id]
  download  download [channel url]
  export    export [search text] [channel id]
  list      Lists channels
  search    search [search text] [channel id]
```

## `download`
Will download all of a channels vtt files into your database 
```bash
yt-fts download "https://www.youtube.com/@TimDillonShow/videos"
```

`--channel-id [channel_id]`

If `download` fails you can manually input the channel id with the `--channel-id` flag.
The channel url should still be an argument 
```bash
yt-fts download --channel-id "UC4woSp8ITBoYDmjkukhEhxg" "https://www.youtube.com/@TimDillonShow/videos" 
```

`--language [en/fr/es/etc..]`

Specify subtitles language 
```bash
yt-fts download --language de "https://www.youtube.com/@TimDillonShow/videos" 
```

`--number-of-jobs [num_threads]`

Speed up downloads with multi threading 
```bash
yt-fts download --number-of-jobs 6 "https://www.youtube.com/@TimDillonShow/videos"
```

## `list`
List all of your downloaded channels 
```bash
yt-fts list
```

output:
```
Listing channels
  id  channel_name         channel_url
----  -------------------  ---------------------------------------------------------------
   1  The Tim Dillon Show  https://www.youtube.com/channel/UC4woSp8ITBoYDmjkukhEhxg/videos
   2  Lex Fridman          https://www.youtube.com/channel/UCSHZKyawb77ixDdsGog4iWA/videos
   3  Traversy Media       https://www.youtube.com/channel/UC29ju8bIPH5as8OGnQzwJyA/videos
```

## `search`
```
Usage: yt-fts search [OPTIONS] SEARCH_TEXT

  Search for a specified text within a channel, a specific video, or all
  channels. SEARCH_TEXT is the text to search for.

Options:
  --channel TEXT  The name or id of the channel to search in. This is required
                  unless the --all or --video options are used.
  --video TEXT    The id of the video to search in. This is used instead of
                  the channel option.
  --all           Search in all channels.
  --help          Show this message and exit.
```

- The search string does not have to be a word for word and match 
- Use Id if you have channels with the same name or channels that have special characters in their name 
- Search strings are limited to 40 characters. 

### Search by channel
**Ex:**
```bash
yt-fts search "life in the big city" --channel "The Tim Dillon Show"
# or 
yt-fts search "life in the big city" --channel 1  # assuming 1 is id of channel
```
output:
```
The Tim Dillon Show: "164 - Life In The Big City - YouTube"

    Quote: "van in the driveway life in the big city"
    Time Stamp: 00:30:44.580
    Video ID: dqGyCTbzYmc
    Link: https://youtu.be/dqGyCTbzYmc?t=1841
```

### Search all channels 
Use `--all` to search all channels in your database 

**Ex:**
```bash
yt-fts search "text to search" --all
```

### Search in video
Use `--video` to search in a specific video by it's ID

**Ex:**
```bash
yt-fts search "text to search" --video [VIDEO_ID]
```

### Advanced Search Syntax

The search string supports sqlite [Enhanced Query Syntax](https://www.sqlite.org/fts3.html#full_text_index_queries).
which includes things like [prefix queries](https://www.sqlite.org/fts3.html#termprefix) which you can use to match parts of a word.  

**Ex:**

```bash
yt-fts search "rea* kni* Mali*" --channel "The Tim Dillon Show" 
```
output:
```
The Tim Dillon Show: "#200 - Knife Fights In Malibu | The Tim Dillon Show - YouTube"

    Quote: "real knife fight down here in Malibu I"
    Time Stamp: 00:45:39.420
    Video ID: e79H5nxS65Q
    Link: https://youtu.be/e79H5nxS65Q?t=2736
```

## `Export`
Similar to `search` except it will export all of the search results to a csv 
with the format: `Channel Name,Video Title,Quote,Time Stamp,Link` as it's headers

```bash
yt-fts export "life in the big city" "The Tim Dillon Show"
```

You can export from all channels in your database as well
```bash
yt-fts export "life in the big city" --all
```

## `Delete` 
Will delete a channel from your database 
```bash
yt-fts delete [channel_id]
```
