#!/bin/bash

export LC_ALL='C'

FILELIST=/tmp/sl-filelist.txt
DIRLIST=/tmp/sl-dirlist.txt
TMP=/tmp/sl-temp.txt

[ -f "$TMP" ] && rm "$TMP"

if [[ ! -d "$1/logs" ]] ; then
    echo "Directory $1/logs doesn't exist. Looks risky. Aborting."
    exit
fi

if [[ ! -d "$2/logs" ]] ; then
    echo "Directory $2/logs doesn't exist. Looks risky. Aborting."
    exit
fi

echo "From $1 to $2..."

(
  find -L "$1" -type f -iname "*.txt" |cut -b $(echo -n "$1"|wc -c)- 
  find -L "$2" -type f -iname "*.txt" |cut -b $(echo -n "$2"|wc -c)-
) | sort | uniq |
grep -v "conflicted copy" |
grep -vE "/(cef_log|plugin_cookies|search_history|teleport_history|typed_locations)\.txt$" >"$FILELIST"

cat "$FILELIST" |sed 's/^\(.*\)\/.*$/\1/' |uniq >"$DIRLIST"



cat "$DIRLIST" |while read -r d; do mkdir -p "$2/$d"; done

input_stream() {
  if [ "$#" -gt 2 ]; then
    # If filters were provided, build a grep command with multiple -e patterns.
    grep_args=()
    # Start from the 3rd argument for filters.
    for ((i=3;i<=$#;i++)); do
      grep_args+=("-e" "${!i}")
    done
    grep -i "${grep_args[@]}" "$FILELIST"
  else
    # Otherwise, just output the whole file list.
    cat "$FILELIST"
  fi
}

input_stream "$@" | while read -r f; do
#echo "Processing $f..."


if [ -f "$1/$f" ]; then
  if [ -f "$2/$f" ]; then
    diff -q "$1/$f" "$2/$f" >/dev/null || (
      (
        cat "$1/$f" 2>/dev/null
        cat "$2/$f" 2>/dev/null
      ) | sl-chatsort.sh >"$TMP"
      diff -q "$TMP" "$2/$f" >/dev/null || ( echo "Updating $f..."; cp "$TMP" "$2/$f" )
    )
  else
    echo "Adding $f..."
    cp "$1/$f" "$2/$f"
  fi
fi

done

[ -f "$FILELIST" ] && rm "$FILELIST"
[ -f "$DIRLIST" ] && rm "$DIRLIST"
[ -f "$TMP" ] && rm "$TMP"

