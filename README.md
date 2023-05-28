
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

### Usage 
```
Usage: yt-fts [OPTIONS] COMMAND [ARGS]...

Options:
  --help  Show this message and exit.

Commands:
  delete    delete [channel id]
  download  download [channel url]
  export    export [channel id] [search text]
  list      Lists channels
  search    search [channel id] [search text]
```

### `download`
Will download all of a channels vtt files into your database 
```bash
yt-fts download "https://www.youtube.com/@TimDillonShow/videos"
```

**`--channel-id [youtube channel id]`**

If `download` fails you can manually input the channel id with the `--channel-id` flag.
The channel url should still be an argument 
```bash
yt-fts download --channel-id "UC4woSp8ITBoYDmjkukhEhxg" "https://www.youtube.com/@TimDillonShow/videos" 
```

**`--language [en/fr/es/etc..]`**

Specify subtitles language 
```bash
yt-fts download --language de "https://www.youtube.com/@TimDillonShow/videos" 
```

**`--number-of-jobs [number]`**

Speed up downloads with multi threading 
```bash
yt-fts download --number-of-jobs 6 "https://www.youtube.com/@TimDillonShow/videos"
```

### `list`
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

### `search`
Search a channel for text based off the channel id you give it and 
print a url to that point in the video
```bash
yt-fts search [channel_id] "text you want to find"
```
**EX:**

```bash
yt-fts search UC4woSp8ITBoYDmjkukhEhxg "life in the big city"
```
output:
```
Video title"("#208 - Let's Have A Party | The Tim Dillon Show - YouTube",)"

    Quote: "life in the big city Dan is wearing the"
    Time Stamp: 01:50:07.790
    Link: https://youtu.be/CJ_KAsz8rjQ?t=6604

Video title"('#176 - The Florida Project | The Tim Dillon Show - YouTube',)"

    Quote: "the show life in the big city love these"
    Time Stamp: 00:31:05.669
    Link: https://youtu.be/nKcqbHQndFQ?t=1862

Video title"('164 - Life In The Big City - YouTube',)"

    Quote: "life in the big city it was one of my"
    Time Stamp: 00:27:17.549
    Link: https://youtu.be/dqGyCTbzYmc?t=1634
```

### `Export`
Similar to `search` except it will export all of the search results to a csv 
with the format: `Video Title,Quote,Time Stamp,Link` as it's headers
```bash
yt-fts export UC4woSp8ITBoYDmjkukhEhxg "life in the big city" 
```

### `Delete` 
Will delete a channel from your database 
```bash
yt-fts delete [channel_id]
```
