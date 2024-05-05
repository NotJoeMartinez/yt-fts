
# yt-fts - Youtube Full Text Search 
`yt-fts` is a command line program that uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) to scrape all of a youtube channels subtitles and load them into an sqlite database that is searchable from the command line. It allows you to query a channel for specific key word or phrase and will generate time stamped youtube urls to
the video containing the keyword. 

It also supports semantic search via the [OpenAI embeddings API](https://beta.openai.com/docs/api-reference/) using [chromadb](https://github.com/chroma-core/chroma).

- [Blog Post](https://notjoemartinez.com/blog/youtube_full_text_search/)
- [Semantic Search](#Semantic-Search-via-OpenAI-embeddings-API) 
- [CHANGELOG](CHANGELOG.md)

https://github.com/NotJoeMartinez/yt-fts/assets/39905973/6ffd8962-d060-490f-9e73-9ab179402f14

## Installation 

pip 

```bash
pip install yt-fts
```

Homebrew

```bash
brew tap notjoemartinez/yt-fts
brew install yt-fts
```


**yt-dlp dependency:**

This project requires [yt-dlp](https://github.com/yt-dlp/yt-dlp) installed globally. Platform specific installation instructions are available on the [yt-dlp wiki](https://github.com/yt-dlp/yt-dlp/wiki/Installation). 

```bash
# MacOS/Homebrew
brew install yt-dlp
# Windows/winget
winget install yt-dlp
# pip
python3 -m pip install -U yt-dlp
```

## `download`
Download subtitles for a channel. 

Takes a channel url or id as an argument. Specify the number of jobs to parallelize the download with the `--number-of-jobs` option. 

```bash
yt-fts download --number-of-jobs 5 "https://www.youtube.com/@3blue1brown"
```

## `list`
List saved channels.

The (ss) next to the channel name indicates that the channel has semantic search enabled. 

```bash
yt-fts list
```

```
┏━━━━┳━━━━━━━━━━━━━━━━━━━━━━━┳━━━━━━━┳━━━━━━━━━━━━━━━━━━━━━━━━━━┓
┃ ID ┃ Name                  ┃ Count ┃ Channel ID               ┃
┡━━━━╇━━━━━━━━━━━━━━━━━━━━━━━╇━━━━━━━╇━━━━━━━━━━━━━━━━━━━━━━━━━━┩
│ 1  │ ChessPage1 (ss)       │ 19    │ UCO2QPmnJFjdvJ6ch-pe27dQ │
│ 2  │ 3Blue1Brown           │ 127   │ UCYO_jab_esuFRV4b17AJtAw │
│ 3  │ george hotz archive   │ 410   │ UCwgKmJM4ZJQRJ-U5NjvR2dg │
│ 4  │ The Tim Dillon Show   │ 288   │ UC4woSp8ITBoYDmjkukhEhxg │
│ 5  │ Academy of Ideas (ss) │ 190   │ UCiRiQGCHGjDLT9FQXFW0I3A │
└────┴───────────────────────┴───────┴──────────────────────────┘

```

## `search` (Full Text Search)
Full text search for a string in saved channels.

- The search string does not have to be a word for word and match 
- Search strings are limited to 40 characters. 

```bash
# search in all channels
yt-fts search "[search query]" 

# search in channel 
yt-fts search "[search query]" --channel "[channel name or id]" 

# search in specific video
yt-fts search "[search query]" --video "[video id]"

# limit results 
yt-fts search "[search query]" --limit "[number of results]" --channel "[channel name or id]"

# export results to csv
yt-fts search "[search query]" --export --channel "[channel name or id]" 
```

Advanced Search Syntax:

The search string supports sqlite [Enhanced Query Syntax](https://www.sqlite.org/fts3.html#full_text_index_queries).
which includes things like [prefix queries](https://www.sqlite.org/fts3.html#termprefix) which you can use to match parts of a word.  

```bash
# AND search
yt-fts search "knife AND Malibu" --channel "The Tim Dillon Show" 

# OR SEARCH 
yt-fts search "knife OR Malibu" --channel "The Tim Dillon Show" 

# wild cards
yt-fts search "rea* kni* Mali*" --channel "The Tim Dillon Show" 
```


# Semantic Search 
You can enable semantic search for a channel by using the `get-embeddings` command.
This requires an OpenAI API key set in the environment variable `OPENAI_API_KEY`, or 
you can pass the key with the `--openai-api-key` flag. 


## `get-embedings`
Fetches OpenAI embeddings for specified channel
```bash

# make sure openAI key is set
# export OPENAI_API_KEY="[yourOpenAIKey]"

yt-fts get-embeddings --channel "3Blue1Brown"
```

After the embeddings are saved you will see a `(ss)` next to the channel name when you 
list channels and you will be able to use the `vsearch` command for that channel. 

## `vsearch` (Semantic Search)
`vsearch` is for "Vector search". This requires that you enable semantic 
search for a channel with `get-embeddings`. It has the same options as 
`search` but output will be sorted by similarity to the search string and 
the default return limit is 10. 

```bash
# search by channel name
yt-fts vsearch "[search query]" --channel "[channel name or id]"

# search in specific video
yt-fts vsearch "[search query]" --video "[video id]"

# limit results 
yt-fts vsearch "[search query]" --limit "[number of results]" --channel "[channel name or id]"

# export results to csv
yt-fts vsearch "[search query]" --export --channel "[channel name or id]" 

```



## How To

**Export search results:**
For both the `search` and `vsearch` commands you can export the results to a csv file with 
the `--export` flag. and it will save the results to a csv file in the current directory. 
```bash
yt-fts search "life in the big city" --export
yt-fts vsearch "existing in large metropolaten center" --export
```

**Delete a channel:**
You can delete a channel with the `delete` command. 

```bash
yt-fts delete --channel "3Blue1Brown"
```


**Update a channel:**
The update command currently only works for full text search and will not update the 
semantic search embeddings. 

```bash
yt-fts update --channel "3Blue1Brown"
```


**Export all of a channel's transcript:**
This command will create a directory in current working directory with the youtube 
channel id of the specified channel.
```bash
# Export to vtt
yt-fts export --channel "[id/name]" --format "[vtt/txt]"
```