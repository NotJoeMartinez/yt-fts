
# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/).

## [0.1.49] - 2024-06-25
### Fixed
- Outdated chromadb dependency crashing cli 
  - https://github.com/NotJoeMartinez/yt-fts/issues/145

### Added
- Date in fts searches and exports 
  - https://github.com/NotJoeMartinez/yt-fts/issues/142


## [0.1.48] - 2024-04-05
### Fixed
- [yt-fts-138](https://github.com/NotJoeMartinez/yt-fts/pull/141)
  - Fixed unicode decode error #138
  - Introduced when we added current metadata with `--write-info-json`
    - Caused by writing json to windows filesystem, which encodes in `Windows-1252` instead of `utf-8`
    - Another reason to not use subprocess.  
### Added 
- [yt-fts-139](https://github.com/NotJoeMartinez/yt-fts/pull/139)
  - Playlists downloading now supported by passing the `--playlist/-p` to `download` command 


## [0.1.43] - 2024-04-05
### Changed 
  - [yt-fts-136](https://github.com/NotJoeMartinez/yt-fts/pull/136)
    - Overhauled full text search results UI
    - Results are displayed more logically, with less unnecessary information sorted by frequency.
  
  - [yt-fts-131](https://github.com/NotJoeMartinez/yt-fts/pull/131)
    - Moved build system to `pyproject.toml` from `setup.py`

### Fixed
  - [yt-fts-134](https://github.com/NotJoeMartinez/yt-fts/pull/134)
    - Disabled chromadb opentelemetry

### Added 
  - [yt-fts-132](https://github.com/NotJoeMartinez/yt-fts/pull/132)
    - Github actions integration

  

### [0.1.42] - 2024-01-22
Special thanks to [@danlamanna](https://github.com/danlamanna) for these fixes

### Fixed 
  - [yt-fts-126](https://github.com/NotJoeMartinez/yt-fts/pull/126) 
    - Major: Fixed bug that prevented chroma database entries from being deleted if the user did not have an openAI key set 

### Changed 
  - [yt-fts-127](https://github.com/NotJoeMartinez/yt-fts/pull/127)
    - Major: Improved adding to database time on download by over 50% by using metadata downloaded from yt-dlp

### Added 
  - [yt-fts-124](https://github.com/NotJoeMartinez/yt-fts/pull/124)
    - Minor added -h flag to cli 


## [0.1.41] - 2024-01-08
### Fixed
  - [yt-fts-121](https://github.com/NotJoeMartinez/yt-fts/pull/121)
    - Major: Fixed bug where delete command fails due to database locking

## [0.1.40] - 2024-01-08
### Fixed 
  - [yt-fts-119](https://github.com/NotJoeMartinez/yt-fts/pull/119)
    - Medium: Fixed bug where end times were incorrect due to vtt parsing error 

## [0.1.39] - 2023-12-31
### Fixed
  - [yt-fts-118](https://github.com/NotJoeMartinez/yt-fts/pull/118)
    - Major: Fixed bug where download will fail if channel does not have live stream page

## [0.1.38] - 2023-12-29
### Added 
  - [yt-fts-116](https://github.com/NotJoeMartinez/yt-fts/pull/116)
    - Minor: Search word bold highlighting on `vsearch` and `search`
  - [yt-fts-117](https://github.com/NotJoeMartinez/yt-fts/pull/117)
    - Minor: Added hints on advanced query syntax when query doesn't get anything 


## [0.1.37] - 2023-12-27
### Added 
  - [yt-fts-114](https://github.com/NotJoeMartinez/yt-fts/pull/114)
    - Medium: Added vtt export to export command
    - Minor: removed print statement from `get_channel_id_from_input`


## [0.1.36] - 2023-12-25
### Fixed 
- [yt-fts-112](https://github.com/NotJoeMartinez/yt-fts/pull/112)
  - Medium: Fixed issue with download command not downloading live streamed videos

### Added
- [yt-fts-111](https://github.com/NotJoeMartinez/yt-fts/pull/111)
  - Minor: Added `export` command which exports channel subtitles to a directory of text files

## [0.1.35] - 2023-12-19

### Added
- [yt-fts-109](https://github.com/NotJoeMartinez/yt-fts/pull/109)
  - Minor: added summary string to vector search
- [yt-fts-108](https://github.com/NotJoeMartinez/yt-fts/pull/108)
  - Minor: added limit option to fts search 
### Fixed
- [yt-fts-110](https://github.com/NotJoeMartinez/yt-fts/pull/110)
  - Medium: Fixed issue with `delete` command not deleting channels from chroma database
 

## [0.1.34] - 2023-12-19

### Added
- Minor: Basic unit testing with the built in `unittest` module.

### Changed 
- [yt-fts-96](https://github.com/NotJoeMartinez/yt-fts/pull/96)
  - Major: Embeddings are now stored using chromadb instead of sqlite. This allows for more efficient storage and retrieval of embeddings. 
  - Major: Semantic search and full text search are now separate commands. `vsearch` for semantic search and `search` for full text search however both commands have similar flags
  - Medium: The text converted to embeddings is now split up by 10 second intervals to increase context for the embeddings.
  - Minor: both `vsearch` and `search` now search all channels by default. Use `--channel` to specify a channel to search. 
  - Minor: There's currently no way to update the embeddings
  - Minor: the `search` command has no `--limit` flag


## [0.1.33] - 2023-12-14

### Fixed

- [yt-fts-91](https://github.com/NotJoeMartinez/yt-fts/pull/91)
  - Major: Fixed bootstrapping issue where `subtitles.db` was allways created in the current working directory

## [0.1.32] - 2023-12-14

### Changed 

- [yt-fts-87](https://github.com/NotJoeMartinez/yt-fts/issues/87)

  Minor: Moved `--list config` to its own command `list config` to make it more discoverable.

## [0.1.31] - 2023-08-02

### Changed

- [yt-fts-85](https://github.com/NotJoeMartinez/yt-fts/pull/85)

  Minor: Moved all ASCII message printing to the [rich](https://github.com/Textualize/rich) python library 
  to consolidate all warning, status, progress and error message formating to one library. This removes
  `tabulate` and `progress` dependencies. 

## [0.1.30] - 2023-07-31

### Added

- Changelog

  Minor: Added a changelog to the project.

### Changed

- [yt-fts-67](https://github.com/NotJoeMartinez/yt-fts/issues/67)

  Minor: YouTube URL validation now allows for /@channelName and /channle/channelID
  instead of forcing /@channel/videos. 
