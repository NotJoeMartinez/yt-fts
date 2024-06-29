## Testing channels
- JCS - Criminal Psychology
  - https://www.youtube.com/@JCS 
  - https://www.youtube.com/channel/UCYwVxWpjeKFWwu8TML-Te9A

## Testing Playlists
- How to start a startup 
  - https://www.youtube.com/playlist?list=PL5q_lef6zVkaTY_cT1k7qFNF2TidHCe-1

## Test Download Commands
### Channel Download 
Commands:
```sh
# custom channel name
yt-fts download "https://www.youtube.com/@JCS" 
# legacy channel name
yt-fts download "https://www.youtube.com/channel/UCYwVxWpjeKFWwu8TML-Te9A"
# mutli threading 
yt-fts download -j 5 "https://www.youtube.com/@JCS" 
```
Expected sql output:
```sql
select * from channels;
-- UCYwVxWpjeKFWwu8TML-Te9A|JCS - Criminal Psychology|https://www.youtube.com/channel/UCYwVxWpjeKFWwu8TML-Te9A/videos

select count(*) from Videos where channel_id = 'UCYwVxWpjeKFWwu8TML-Te9A';
-- 17

select count(*) from Subtitles ;
-- 21153
```

### Playlist Download

```shell
# default
yt-fts download --playlist "https://www.youtube.com/playlist?list=PL5q_lef6zVkaTY_cT1k7qFNF2TidHCe-1"
# multi threaded
yt-fts downlaod --playlist -j 5 "https://www.youtube.com/playlist?list=PL5q_lef6zVkaTY_cT1k7qFNF2TidHCe-1"
```

Expected sql output:
```sql
select * from Channels where channel_id = 'UCxIJaCMEptJjxmmQgGFsnCg';
-- UCxIJaCMEptJjxmmQgGFsnCg|Y Combinator: The Vault|https://www.youtube.com/channel/UCxIJaCMEptJjxmmQgGFsnCg/videos
select count(*) from videos where channel_id = 'UCxIJaCMEptJjxmmQgGFsnCg';
-- 16

SELECT COUNT(*) as subtitle_count
FROM Subtitles s
JOIN Videos v ON s.video_id = v.video_id
JOIN Channels c ON v.channel_id = c.channel_id
WHERE c.channel_id = 'UCxIJaCMEptJjxmmQgGFsnCg';
-- 20970
```


## Test `search` commands
Assuming you have both the playlists saved to local db
### Global Search
Command:
```sh
yt-fts search "growth hacking"
```

Expected output:
```text
Found 3 matches in 2 videos from 1 channel
Query 'growth hacking' 
Scope: all
```

Command:
```sh
yt-fts search "knife attack" 
```

Expected output:
```text
Found 1 matches in 1 videos from 1 channel
Query 'knife attack' 
Scope: all
```


### Search JCS by name
Command:
```sh
yt-fts search --channel "JCS - Criminal Psychology" "criminal 
```
Expected output:
```txt
Found 11 matches in 7 videos from 1 channel
Query 'criminal' 
Scope: channel
```

### Search JCS by channel id
Command:
```sh
yt-fts search -c 4 "criminal" 
```

Expected output:
```txt
Found 11 matches in 7 videos from 1 channel
Query 'criminal' 
Scope: channel
```