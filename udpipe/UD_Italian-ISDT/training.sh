#!/bin/bash
cat it_isdt-ud-train.conllu | ../bin-linux64/udpipe  --train nob.udpipe
