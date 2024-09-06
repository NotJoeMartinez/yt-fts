# yt-fts - YouTube Full Text Search 
`yt-fts` is a command line program that uses [yt-dlp](https://github.com/yt-dlp/yt-dlp) to scrape all of a YouTube 
channels subtitles and load them into a sqlite database that is searchable from the command line. It allows you to
query a channel for specific key word or phrase and will generate time stamped YouTube urls to
the video containing the keyword. 

It also supports semantic search via the [OpenAI embeddings API](https://beta.openai.com/docs/api-reference/) using [chromadb](https://github.com/chroma-core/chroma).

- [Blog Post](https://notjoemartinez.com/blog/youtube_full_text_search/)
- [LLM/RAG Chat Bot](#llm-chat-bot)
- [Video Summaries](#summarize)
- [Semantic Search](#vsearch-semantic-search)
- [CHANGELOG](CHANGELOG.md)

https://github.com/NotJoeMartinez/yt-fts/assets/39905973/6ffd8962-d060-490f-9e73-9ab179402f14

## Installation 

pip 

```bash
pip install yt-fts
```

## `download`
Download subtitles for a channel. 

Takes a channel url as an argument. Specify the number of jobs to parallelize the download with the `--jobs` flag. 
Use the `--cookies-from-browser` to use cookies from your browser in the requests, will help if you're getting errors 
that request you to sign in. You can also run the `update` command several times to gradually get more videos into the database. 

```bash
yt-fts download --jobs 5 "https://www.youtube.com/@3blue1brown"
yt-fts download --cookies-from-browser firefox "https://www.youtube.com/@3blue1brown"
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
yt-fts search "[search query]" --video-id "[video id]"

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


# Semantic Search and RAG
You can enable semantic search for a channel by using the `mbeddings` command.
This requires an OpenAI API key set in the environment variable `OPENAI_API_KEY`, or 
you can pass the key with the `--openai-api-key` flag. 


## `embeddings`
Fetches OpenAI embeddings for specified channel
```bash

# make sure openAI key is set
# export OPENAI_API_KEY="[yourOpenAIKey]"

yt-fts embeddings --channel "3Blue1Brown"

# specify time interval in seconds to split text by default is 30 
# the larger the interval the more accurate the llm response  
# but semantic search will have more text for you to read. 
yt-fts embeddings --interval 60 --channel "3Blue1Brown" 
```
After the embeddings are saved you will see a `(ss)` next to the channel name when you 
list channels, and you will be able to use the `vsearch` command for that channel. 

## `llm` (Chat Bot)
Starts interactive chat session with `gpt-4o` OpenAI model using 
the semantic search results of your initial prompt as the context
to answer questions. If it can't answer your question, it has a 
mechanism to update the context by running targeted query based 
off the conversation. The channel must have semantic search enabled.

```bash
yt-fts llm --channel "3Blue1Brown" "How does back propagation work?"
```

## `summarize`
Summarizes a YouTube video transcript, providing time stamped URLS. 
Requires a valid YouTube video URL or video ID as argument. If the 
trancript is not in the database it will try to scrape it.

```bash
yt-fts summarize "https://www.youtube.com/watch?v=9-Jl0dxWQs8"
# or
yt-fts summarize "9-Jl0dxWQs8"
```
output:
```
In this video, 3Blue1Brown explores how large language models (LLMs) like GPT-3 
might store facts within their vast...                                                         

 1 Introduction to Fact Storage in LLMs:                                                                                     
    • The video starts by questioning how LLMs store specific facts and                                                      
      introduces the idea that these facts might be stored in a particular part of the                                       
      network known as multi-layer perceptrons (MLPs).                                                                       
    • 0:00                                                                                                                   
 2 Overview of Transformers and MLPs:                                                                                        
    • Provides a refresher on transformers and explains that the video will focus                                            
```

## `vsearch` (Semantic Search)
`vsearch` is for "Vector search". This requires that you enable semantic 
search for a channel with `embeddings`. It has the same options as 
`search` but output will be sorted by similarity to the search string and 
the default return limit is 10. 

```bash
# search by channel name
yt-fts vsearch "[search query]" --channel "[channel name or id]"

# search in specific video
yt-fts vsearch "[search query]" --video-id "[video id]"

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

This command will create a directory in current working directory with the YouTube 
channel id of the specified channel.
```bash
# Export to vtt
yt-fts export --channel "[id/name]" --format "[vtt/txt]"
```