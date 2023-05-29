
# yt-fts 
`yt-fts` is a simple python script that uses yt-dlp to scrape all of a youtube channels subtitles
and load them into an sqlite database that is searchable from the command line. It allows you to
query a channel for specific key word or phrase and will generate time stamped youtube urls to
the video containing the keyword. 

- [Blog Post](https://notjoemartinez.com/blog/youtube_full_text_search/)

### Installation 

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

### Dependencies 
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
channel_id                channel_name         channel_url
------------------------  -------------------  ---------------------------------------------------------------
UC4woSp8ITBoYDmjkukhEhxg  The Tim Dillon Show  https://www.youtube.com/channel/UC4woSp8ITBoYDmjkukhEhxg/videos
```

## `search`
Search a channel for text based off the channel id you give it and 
print a url to that point in the video. The search string does not 
have to be a word for word and match is limited to 40 characters. 

```bash
yt-fts search "text you want to find" [channel_id]
```
**Ex:**
```bash
yt-fts search "life in the big city" UC4woSp8ITBoYDmjkukhEhxg 
```
output:
```
The Tim Dillon Show: "164 - Life In The Big City - YouTube"

    Quote: "van in the driveway life in the big city"
    Time Stamp: 00:30:44.580
    Link: https://youtu.be/dqGyCTbzYmc?t=1841
```

### Search all channels 
Use `--all` to search all channels in your database 

**Ex:**
```bash
yt-fts search "text to search" --all
```

### Advanced Search Syntax

The search string supports sqlite [Enhanced Query Syntax](https://www.sqlite.org/fts3.html#full_text_index_queries).
which includes things like [prefix queries](https://www.sqlite.org/fts3.html#termprefix) which you can use to match parts of a word.  

**Ex:**

```bash
yt-fts search "rea* kni* Mali*" UC4woSp8ITBoYDmjkukhEhxg 
```
output:
```
The Tim Dillon Show: "#200 - Knife Fights In Malibu | The Tim Dillon Show - YouTube"

    Quote: "real knife fight down here in Malibu I"
    Time Stamp: 00:45:39.420
    Link: https://youtu.be/e79H5nxS65Q?t=2736
```

## `Export`
Similar to `search` except it will export all of the search results to a csv 
with the format: `Channel Name,Video Title,Quote,Time Stamp,Link` as it's headers

```bash
yt-fts export "life in the big city" UC4woSp8ITBoYDmjkukhEhxg 
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
