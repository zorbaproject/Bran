#!/bin/bash

cd /home/luca/Progetti/vdb-hacking/
nnumber=$(ls -1 ./corpus-ricerche/ | wc -l)
onumber=$(cat fcount.tmp)
if [[ $nnumber == $onumber ]]; then
kill -9 $(ps aux | grep 'url2corpus' | grep 'python' | sed "s/[a-z]*[ ]*\([0-9]*\)[ ]*.*/\1/g")
./url2corpus.py "RICERCAREPUBBLICA:" ./corpus-ricerche/ $(less corpus-ricerche/fromdate.tmp | tail -n 1)
fi
echo $nnumber > fcount.tmp
