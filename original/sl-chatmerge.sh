#!/bin/bash

time for d in {1..1}; do

echo Trying Cygwin Local - Full Sync
#sl-chatmerge-one.sh /cygdrive/c/Users/$USER/AppData/Roaming/Firestorm_x64/ /cygdrive/c/Users/$USER/Resilio/SL-Logs-and-Settings/SL-Chat/ "$@"
#sl-chatmerge-one.sh /cygdrive/c/Users/$USER/AppData/Roaming/SecondLife/ /cygdrive/c/Users/$USER/Resilio/SL-Logs-and-Settings/SL-Chat/ "$@"
#sl-chatmerge-one.sh /cygdrive/c/Users/$USER/Resilio/SL-Logs-and-Settings/SL-Chat/ /cygdrive/c/Users/$USER/AppData/Roaming/SecondLife/ "$@"
#sl-chatmerge-one.sh /cygdrive/c/Users/$USER/Resilio/SL-Logs-and-Settings/SL-Chat/ /cygdrive/c/Users/$USER/AppData/Roaming/Firestorm_x64/ "$@"
sl-chatmerge-one.sh /cygdrive/c/Users/$USER/AppData/Roaming/Firestorm_x64/ /cygdrive/c/Users/$USER/Mega/Apps/SL-Logs-and-Settings/SL-Chat/ "$@"
sl-chatmerge-one.sh /cygdrive/c/Users/$USER/AppData/Roaming/SecondLife/ /cygdrive/c/Users/$USER/Mega/Apps/SL-Logs-and-Settings/SL-Chat/ "$@"
sl-chatmerge-one.sh /cygdrive/c/Users/$USER/Mega/Apps/SL-Logs-and-Settings/SL-Chat/ /cygdrive/c/Users/$USER/AppData/Roaming/SecondLife/ "$@"
sl-chatmerge-one.sh /cygdrive/c/Users/$USER/Mega/Apps/SL-Logs-and-Settings/SL-Chat/ /cygdrive/c/Users/$USER/AppData/Roaming/Firestorm_x64/ "$@"
echo

echo Trying Cygwin Mapped Home - Full Sync
#sl-chatmerge-one.sh /cygdrive/c/Users/$USER/AppData/Roaming/Firestorm_x64/ /cygdrive/h/Resilio/SL-Logs-and-Settings/SL-Chat/ "$@"
#sl-chatmerge-one.sh /cygdrive/c/Users/$USER/AppData/Roaming/SecondLife/ /cygdrive/h/Resilio/SL-Logs-and-Settings/SL-Chat/ "$@"
#sl-chatmerge-one.sh /cygdrive/h/Resilio/SL-Logs-and-Settings/SL-Chat/ /cygdrive/c/Users/$USER/AppData/Roaming/SecondLife/ "$@"
#sl-chatmerge-one.sh /cygdrive/h/Resilio/SL-Logs-and-Settings/SL-Chat/ /cygdrive/c/Users/$USER/AppData/Roaming/Firestorm_x64/ "$@"
sl-chatmerge-one.sh /cygdrive/c/Users/$USER/AppData/Roaming/Firestorm_x64/ /cygdrive/h/Mega/Apps/SL-Logs-and-Settings/SL-Chat/ "$@"
sl-chatmerge-one.sh /cygdrive/c/Users/$USER/AppData/Roaming/SecondLife/ /cygdrive/h/Mega/Apps/SL-Logs-and-Settings/SL-Chat/ "$@"
sl-chatmerge-one.sh /cygdrive/h/Mega/Apps/SL-Logs-and-Settings/SL-Chat/ /cygdrive/c/Users/$USER/AppData/Roaming/SecondLife/ "$@"
sl-chatmerge-one.sh /cygdrive/h/Mega/Apps/SL-Logs-and-Settings/SL-Chat/ /cygdrive/c/Users/$USER/AppData/Roaming/Firestorm_x64/ "$@"
echo

echo Trying macOS - Full Sync
#sl-chatmerge-one.sh ~/Library/Application\ Support/Firestorm/ ~/Dropbox/Apps/SL-Logs-and-Settings/SL-Chat/ "$@"
#sl-chatmerge-one.sh ~/Library/Application\ Support/SecondLife/ ~/Dropbox/Apps/SL-Logs-and-Settings/SL-Chat/ "$@"
#sl-chatmerge-one.sh ~/Dropbox/Apps/SL-Logs-and-Settings/SL-Chat/ ~/Library/Application\ Support/SecondLife/ "$@"
#sl-chatmerge-one.sh ~/Dropbox/Apps/SL-Logs-and-Settings/SL-Chat/ ~/Library/Application\ Support/Firestorm/ "$@"
#sl-chatmerge-one.sh ~/Library/Application\ Support/Firestorm/ ~/Resilio/SL-Logs-and-Settings/SL-Chat/ "$@"
#sl-chatmerge-one.sh ~/Library/Application\ Support/SecondLife/ ~/Resilio/SL-Logs-and-Settings/SL-Chat/ "$@"
#sl-chatmerge-one.sh ~/Resilio/SL-Logs-and-Settings/SL-Chat/ ~/Library/Application\ Support/SecondLife/ "$@"
#sl-chatmerge-one.sh ~/Resilio/SL-Logs-and-Settings/SL-Chat/ ~/Library/Application\ Support/Firestorm/ "$@"
sl-chatmerge-one.sh ~/Library/Application\ Support/Firestorm/ ~/Mega/Apps/SL-Logs-and-Settings/SL-Chat/ "$@"
sl-chatmerge-one.sh ~/Library/Application\ Support/Kokua/ ~/Mega/Apps/SL-Logs-and-Settings/SL-Chat/ "$@"
sl-chatmerge-one.sh ~/Library/Application\ Support/SecondLife/ ~/Mega/Apps/SL-Logs-and-Settings/SL-Chat/ "$@"
sl-chatmerge-one.sh ~/Mega/Apps/SL-Logs-and-Settings/SL-Chat/ ~/Library/Application\ Support/SecondLife/ "$@"
sl-chatmerge-one.sh ~/Mega/Apps/SL-Logs-and-Settings/SL-Chat/ ~/Library/Application\ Support/Kokua/ "$@"
sl-chatmerge-one.sh ~/Mega/Apps/SL-Logs-and-Settings/SL-Chat/ ~/Library/Application\ Support/Firestorm/ "$@"
echo

done

echo All done.
