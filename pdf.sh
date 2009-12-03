#!/bin/sh
python /home/alan/coding/_checkouts/mercussion/parser.py --midi $1.music > ly/$1.ly
cd pdf
lilypond -f pdf ../ly/$1.ly
rm *.ps
cd ..
