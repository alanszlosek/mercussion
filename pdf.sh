#!/bin/sh
python /home/alan/coding/_checkouts/mercussion/parser.py --lilypond < $1 > /home/alan/coding/_checkouts/mercussion/testing/ly/$1.ly
lilypond -f pdf -o /home/alan/coding/_checkouts/mercussion/testing/pdf/$1 /home/alan/coding/_checkouts/mercussion/testing/ly/$1.ly
