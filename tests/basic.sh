
# downloads
download() {
    rm *.db
    rm *.csv
    rm *.txt
    stack_smashing="https://www.youtube.com/@stacksmashing/videos"
    pwn_function="https://www.youtube.com/@PwnFunction/videos"
    yt-fts download --language en --number-of-jobs 5 $stack_smashing
    yt-fts download --language en --number-of-jobs 5 $pwn_function
}


# search
test_search_by_channel(){

    stack_smashing_keywords=("firmware decrypt" "unknown bitcoin array" "input shift register" "extensible and linkable format")
    pwn_function_keywords=("templating engine" "parameter pollution" "session objects" "same origin policy")

    # loop through stack smashing keywords by name
    for keyword in "${stack_smashing_keywords[@]}" 
    do
        yt-fts search "${keyword}" --channel stacksmashing >> search_by_channel_name.txt
        yt-fts search "${keyword}" --channel 1 >> search_by_channel_id.txt
    done

    # loop through pwn function keywords
    # for keyword in "${pwn_function_keywords[@]}" 
    # do
    #     yt-fts search "${keyword}" --channel PwnFunction >> search_by_channel_name.txt
    #     yt-fts search "${keyword}" --channel 2
    # done

}

# export
test_export_by_channel() {

    stack_smashing_keywords=("firmware decrypt" "unknown bitcoin array" "input shift register" "extensible and linkable format")
    pwn_function_keywords=("templating engine" "parameter pollution" "session objects" "same origin policy")

    # loop through stack smashing keywords 
    for keyword in "${stack_smashing_keywords[@]}" 
    do
        yt-fts export "${keyword}" stacksmashing 
        yt-fts export "${keyword}" 1
    done

    # loop through pwn function keywords
    for keyword in "${pwn_function_keywords[@]}" 
    do
        yt-fts export "${keyword}" PwnFunction 
        yt-fts export "${keyword}" 2
    done
}

# search and export by all
test_search_export_all(){

    keywords=("firmware decrypt" "unknown bitcoin array" "input shift register" "extensible and linkable format" "templating engine" "parameter pollution" "session objects" "same origin policy")

    # loop through stack smashing keywords by name
    for keyword in "${keywords[@]}" 
    do
        yt-fts search "${keyword}" --all >> search_by_all.txt
        yt-fts export "${keyword}" --all
    done
}

# search video  
test_search_video(){

    keywords=("electrion" "same origin policy" "local storage")

    # loop through stack smashing keywords by name
    for keyword in "${keywords[@]}" 
    do
        yt-fts search "${keyword}" --video "jkJWA_CWrQs" >> search_video.txt
    done
}

test_errors(){
    ## search errors
    yt-fts search "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"  stacksmashing 
    yt-fts search "these words probably do not exist"  stacksmashing
    yt-fts search "linux" foobar

    ## export errors
    yt-fts export  "aaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaaa"  stacksmashing 
    yt-fts export "these words probably do not exist" stacksmashing
    yt-fts export "linux" foobar
}

all(){
    download
    test_search_by_channel
    test_export_by_channel
    test_search_export_all
    test_errors
}

if [[ -z "$@" ]]; then
    echo "Usage: "
    echo "  ./basic.sh all"
    echo "  ./basic.sh download"
    echo "  ./basic.sh search"
    echo "  ./basic.sh video"
    echo "  ./basic.sh export"
    echo "  ./basic.sh search-export-all"
    echo "  ./basic.sh errors"
elif [[ "$@" == "all" ]]; then
    all
elif [[ "$@" == "download" ]]; then
    download
elif [[ "$@" == "search" ]]; then
    test_search_by_channel
elif [[ "$@" == "video" ]]; then
    test_search_video
elif [[ "$@" == "export" ]]; then
    test_export_by_channel
elif [[ "$@" == "search-export-all" ]]; then
    test_search_export_all
elif [[ "$@" == "errors" ]]; then
    test_errors
else
    echo "Usage: "
    echo "  ./basic.sh all"
    echo "  ./basic.sh download"
    echo "  ./basic.sh search"
    echo "  ./basic.sh video"
    echo "  ./basic.sh export"
    echo "  ./basic.sh search-export-all"
    echo "  ./basic.sh errors"
fi