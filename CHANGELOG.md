
# Change Log
All notable changes to this project will be documented in this file.
 
The format is based on [Keep a Changelog](http://keepachangelog.com/).

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
