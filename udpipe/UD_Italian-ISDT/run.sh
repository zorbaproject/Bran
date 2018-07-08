#!/bin/bash
if [[ -f $1 ]]; then
echo "Apro il file"
cat $1 | ../bin-linux64/udpipe --tokenize --tag --parse nob.udpipe
else
echo $1 | ../bin-linux64/udpipe --tokenize --tag --parse nob.udpipe
fi
