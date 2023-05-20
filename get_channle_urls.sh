yt-dlp --print "%(id)s;%(title)s" "URL" >> ids_titles.csv
youtube-dl --write-auto-sub --skip-download
