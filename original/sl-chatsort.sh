#!/bin/bash

#cat "$1" | 
sed 's///' |
awk '{ printf("%s%s",$0~/^\[[0-9]{4}\/[0-9]{2}\/[0-9]{2} /?(FNR!=1?ORS:""):OFS,$0) } END{ print "" }' |
sort -k1.1,1.21 | uniq

