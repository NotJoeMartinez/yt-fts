
# yt-fts - Youtube Full Text Search 
`yt-fts` is a command line program that uses yt-dlp to scrape all of a youtube channels subtitles
and load them into an sqlite database that is searchable from the command line. It allows you to
query a channel for specific key word or phrase and will generate time stamped youtube urls to
the video containing the keyword. 

- [Blog Post](https://notjoemartinez.com/blog/youtube_full_text_search/)
- [Semantic Search](#Semantic-Search-via-OpenAI-embeddings-API) (Experimental)

https://github.com/NotJoeMartinez/yt-fts/assets/39905973/6ffd8962-d060-490f-9e73-9ab179402f14

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
  --version  Show the version and exit.
  --help     Show this message and exit.

Commands:
  delete          Delete a channel and all its data.
  download        Download subtitles from a specified YouTube channel.
  get-embeddings  Generate embeddings for a channel using OpenAI's...
  search          Search for a specified text within a channel, a...
  list View library, transcripts, channel video list and...
  update          Updates a specified YouTube channel.
```

## `download`
Download subtitles 
```
Usage: yt-fts download [OPTIONS] CHANNEL_URL

  Download subtitles from a specified YouTube channel.

  You must provide the URL of the channel as an argument. The script will
  automatically extract the channel id from the URL.

Options:
  -id, --channel-id TEXT        Optional channel id to override the one from
                                the url
  -l, --language TEXT           Language of the subtitles to download
  -j, --number-of-jobs INTEGER  Optional number of jobs to parallelize the run
```

### Examples:

**Basic download by url**

```bash
yt-fts download "https://www.youtube.com/@TimDillonShow/videos"
```

**Multithreaded download**

```bash
yt-fts download --number-of-jobs 6 "https://www.youtube.com/@TimDillonShow/videos"
```

**specify channel id**

If `download` fails you can manually input the channel id with the `--channel-id` flag.
The channel url should still be an argument 

```bash
yt-fts download --channel-id "UC4woSp8ITBoYDmjkukhEhxg" "https://www.youtube.com/@TimDillonShow/videos" 
```

**specify language**

Languages are represented using [ISO 639-1](https://en.wikipedia.org/wiki/List_of_ISO_639-1_codes) language codes 

```bash
yt-fts download --language de "https://www.youtube.com/@TimDillonShow/videos" 
```

## `list`
```
Usage: yt-fts list [OPTIONS]

  View library, transcripts, channel video list and config settings.

Options:
  -t, --transcript TEXT  Show transcript for a video
  -c, --channel TEXT     Show list of videos for a channel
  -l, --library          Show list of channels in library
  --config               Show path to config directory
```

```
yt-fts show -l
```
output:
```
  id    count  channel_name         channel_url
----  -------  -------------------  ----------------------------------------------------
   1      265  The Tim Dillon Show  https://youtube.com/channel/UC4woSp8ITBoYDmjkukhEhxg
   2      688  Lex Fridman (ss)     https://youtube.com/channel/UCSHZKyawb77ixDdsGog4iWA
   3      434  Traversy Media       https://youtube.com/channel/UC29ju8bIPH5as8OGnQzwJyA
```

## `search`
Search saved subtitles 
```
Usage: yt-fts search [OPTIONS] TEXT

  Search for a specified text within a channel, a specific video, or across
  all channels.

Options:
  -c, --channel TEXT   The name or id of the channel to search in. This is
                       required unless the --all or --video options are used.
  -v, --video TEXT     The id of the video to search in. This is used instead
                       of the channel option.
  -a, --all            Search in all channels.
  -s, --semantic       Use Semantic Search
  -l, --limit INTEGER  Max number of results to return
  -e, --export         Export search results to a CSV file.
```

- The search string does not have to be a word for word and match 
- Use Id if you have channels with the same name or channels that have special characters in their name 
- Search strings are limited to 40 characters. 

### Examples:

**Search by channel**

```bash
yt-fts search "life in the big city" --channel "The Tim Dillon Show"
# or 
yt-fts search "life in the big city" --channel 1  # assuming 1 is id of channel
```
output:
```
"Dennis would go hey life in the big city"

    Channel: The Tim Dillon Show
    Title: 154 - The 3 AM Episode - YouTube
    Time Stamp: 00:58:53.789
    Video ID: MhaG3Yfv1cU
    Link: https://youtu.be/MhaG3Yfv1cU?t=3530
```

**Search all channels**

```bash
yt-fts search "text to search" --all
```

**Search in video**

```bash
yt-fts search "text to search" --video [VIDEO_ID]
```

**Advanced Search Syntax**

The search string supports sqlite [Enhanced Query Syntax](https://www.sqlite.org/fts3.html#full_text_index_queries).
which includes things like [prefix queries](https://www.sqlite.org/fts3.html#termprefix) which you can use to match parts of a word.  

```bash
yt-fts search "rea* kni* Mali*" --channel "The Tim Dillon Show" 
```
output:
```
"real knife fight down here in Malibu I"

    Channel: The Tim Dillon Show
    Title: #200 - Knife Fights In Malibu | The Tim Dillon Show - YouTube
    Time Stamp: 00:45:39.420
    Video ID: e79H5nxS65Q
    Link: https://youtu.be/e79H5nxS65Q?t=2736
```

## `update`
Will update a channel with new subtitles if any are found. 
```
Usage: yt-fts update [OPTIONS]

  Updates a specified YouTube channel.

  You must provide the ID of the channel as an argument. Keep in mind some
  might not have subtitles enabled. This command will still attempt to
  download subtitles as subtitles are sometimes added later.

Options:
  -c, --channel TEXT            The name or id of the channel to update.
                                [required]
  -l, --language TEXT           Language of the subtitles to download
  -j, --number-of-jobs INTEGER  Optional number of jobs to parallelize the run
```

## `delete` 
Will delete a channel from your database 
```
Usage: yt-fts delete [OPTIONS]

  Delete a channel and all its data.

  You must provide the name or the id of the channel you want to delete as an
  argument.

  The command will ask for confirmation before performing the deletion.

Options:
  -c, --channel TEXT  The name or id of the channel to delete  [required]
```

**Examples:**

```bash
yt-fts delete "The Tim Dillon Show"
# or
yt-fts delete 1 
```


--- 
# Semantic Search via OpenAI embeddings API 
The following commands are a work in progress but should enable semantic search. 
This requires that you have an openAI API key which you can learn more about that [here](https://platform.openai.com/docs/api-reference/introduction). 

**Limitations**

Keep in mind that generating embeddings will substantially grow the size of your subtitles database and will run slower due to the limitations of working with vectors in sqlite. When running semantic
searches for the first time, API access is still required to generate embeddings for the search string.
These search string embeddings are saved to a history table and won't require additional api requests
after. 

### `get-embedings`
```
Usage: yt-fts get-embeddings [OPTIONS]

  Generate embeddings for a channel using OpenAI's embeddings API.

  Requires an OpenAI API key to be set as an environment variable
  OPENAI_API_KEY.

Options:
  -c, --channel TEXT   The name or id of the channel to generate embeddings
                       for
  --open-api-key TEXT  OpenAI API key. If not provided, the script will
                       attempt to read it from the OPENAI_API_KEY environment
                       variable.
```
